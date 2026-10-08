package za.moteur;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Statistic;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Monster;
import org.bukkit.entity.Player;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Horde;
import za.moteur.coeur.Region;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.UUID;

/**
 * Le Directeur (bible IA-1) : le metteur en scène invisible. Il regarde chaque joueur et dose la peur.
 * Intensité 0-100 ; cycle Calme -> Montée -> Pic -> Relâche. Il joue avec ce qu'il a (hordes virtuelles, événements,
 * Némésis, radio, sons), il ne crée rien de magique, et il ne triche jamais devant le joueur (règle 6).
 */
public final class Directeur {
    public static final class Etat {
        public double intensite;
        public String phase = "calme";
        public long phaseDebut = System.currentTimeMillis();
        public long derniereAction;
        public long relacheJusqua;
        public long capJusqua;
        public final List<Long> morts = new ArrayList<>();
        public final List<String> carnet = new ArrayList<>();
        public long sessionDebut = System.currentTimeMillis();
        public boolean momentFait;
        public String dernierPic = "";
        public int kills, construits, regions, social;
        public double degatsRecus;
        public long dernierDegat;
    }

    private final ZAMoteur z;
    private final Map<UUID, Etat> etats = new HashMap<>();
    private final Random rng = new Random();
    private long derniereGrandeNuit;

    Directeur(ZAMoteur z) {
        this.z = z;
    }

    public Etat etat(UUID u) {
        return etats.computeIfAbsent(u, k -> new Etat());
    }

    public boolean relacheActive(UUID u) {
        Etat e = etats.get(u);
        return e != null && e.relacheJusqua > System.currentTimeMillis();
    }

    void noter(Etat e, String t) {
        e.carnet.add(new java.text.SimpleDateFormat("HH:mm").format(new java.util.Date()) + " " + t);
        while (e.carnet.size() > 50) e.carnet.remove(0);
    }

    // ---------------------------------------------------------------- ce que le Directeur perçoit

    public void degats(Player p, double n) {
        Etat e = etat(p.getUniqueId());
        e.intensite = Math.min(100, e.intensite + n * 3);
        e.degatsRecus += n;
        e.dernierDegat = System.currentTimeMillis();
    }

    public void mort(Player p) {
        Etat e = etat(p.getUniqueId());
        long now = System.currentTimeMillis();
        e.morts.add(now);
        e.morts.removeIf(t -> now - t > 30 * 60_000L);
        if (e.morts.size() >= 3) {
            // anti-frustration : intensité plafonnée, et un coup de chance plausible
            e.capJusqua = now + 20 * 60_000L;
            e.relacheJusqua = now + 10 * 60_000L;
            noter(e, "3 morts en 30 min : plafond et coup de chance");
            z.pont.zaevt("chance " + p.getUniqueId());
            e.morts.clear();
        }
    }

    public void kill(Player p) {
        etat(p.getUniqueId()).kills++;
    }

    public void construit(Player p) {
        etat(p.getUniqueId()).construits++;
    }

    public void join(Player p) {
        Etat e = etat(p.getUniqueId());
        e.sessionDebut = System.currentTimeMillis();
        e.momentFait = false;
    }

    // ---------------------------------------------------------------- chaque seconde

    void tick1s() {
        long now = System.currentTimeMillis();
        List<Player> ps = new ArrayList<>(z.mondePrincipal().getPlayers());
        for (Player p : ps) {
            Etat e = etat(p.getUniqueId());
            Location l = p.getLocation();
            // ce qui fait monter
            int proches = 0;
            for (Entity en : p.getNearbyEntities(16, 8, 16)) if (en instanceof Monster) proches++;
            double monte = proches * 0.8;
            if (p.getHealth() < 8) monte += 1.5;
            if (l.getBlock().getLightLevel() < 5) monte += 0.4;
            boolean seul = true;
            for (Player o : ps) if (o != p && o.getLocation().distanceSquared(l) < 50 * 50) seul = false;
            if (seul) monte += 0.2;
            else e.social++;
            // ce qui fait redescendre : la sécurité (base, groupe), le temps
            double descend = 1.0;
            if (z.mat.presBase(l, 40)) descend += 2;
            if (!seul) descend += 0.5;
            if (proches == 0 && now - e.dernierDegat > 20_000) descend += 1;
            e.intensite = Math.max(0, Math.min(100, e.intensite + monte - descend));
            // plafonds : nouveaux joueurs (premières heures, p81) et anti-frustration
            boolean nouveau = p.getStatistic(Statistic.PLAY_ONE_MINUTE) < 3 * 60 * 60 * 20;
            if (nouveau) e.intensite = Math.min(e.intensite, 50);
            if (e.capJusqua > now) e.intensite = Math.min(e.intensite, 40);
            cycle(p, e, now, nouveau);
        }
        // nuits de serveur : un rythme commun pour les grandes nuits partagées
        if (z.estNuit() && ps.size() >= 3 && now - derniereGrandeNuit > 3 * 60 * 60_000L) {
            boolean prets = true;
            for (Player p : ps) if (relacheActive(p.getUniqueId()) || etat(p.getUniqueId()).intensite > 60) prets = false;
            if (prets && rng.nextDouble() < 0.002) {
                derniereGrandeNuit = now;
                z.pont.zaevt("grande_nuit");
                z.publier(new Evenement("grande_nuit").a(0, 0).grav(4));
            }
        }
    }

    private void cycle(Player p, Etat e, long now, boolean nouveau) {
        long dans = now - e.phaseDebut;
        String avant = e.phase;
        switch (e.phase) {
            case "calme":
                if (e.intensite > 25 || dans > 6 * 60_000L) changer(e, "montee", now);
                break;
            case "montee":
                if (e.intensite > 70) changer(e, "pic", now);
                else if (dans > 8 * 60_000L) changer(e, "pic", now);
                break;
            case "pic":
                if (dans > 3 * 60_000L || e.intensite < 30) {
                    changer(e, "relache", now);
                    e.relacheJusqua = now + (90 + rng.nextInt(90)) * 1000L;
                    z.pont.set("relache::" + p.getUniqueId(), String.valueOf(e.relacheJusqua));
                }
                break;
            default:
                if (now > e.relacheJusqua) changer(e, "calme", now);
                break;
        }
        if (!avant.equals(e.phase)) noter(e, "phase " + e.phase + " (intensité " + (int) e.intensite + ")");
        // une action à la fois, espacées
        long ecart = e.phase.equals("pic") ? 40_000 : 75_000 + rng.nextInt(60_000);
        if (now - e.derniereAction < ecart) return;
        e.derniereAction = now;
        agir(p, e, nouveau, now);
    }

    private void changer(Etat e, String ph, long now) {
        e.phase = ph;
        e.phaseDebut = now;
    }

    private void agir(Player p, Etat e, boolean nouveau, long now) {
        String u = p.getUniqueId().toString();
        Location l = p.getLocation();
        switch (e.phase) {
            case "calme": {
                // il prépare : un son lointain plausible, un signe, une porte entrouverte
                int c = rng.nextInt(3);
                if (c == 0) {
                    z.ecosysteme.echoLointain(p);
                    noter(e, "son lointain");
                } else if (c == 1) {
                    z.ecosysteme.signesPres(p);
                    noter(e, "signe avant-coureur");
                } else {
                    z.pont.zaevt("ambiance " + u + " porte");
                    noter(e, "porte qui grince");
                }
                break;
            }
            case "montee": {
                int c = rng.nextInt(3);
                if (c == 0) {
                    embuscade(p, 2 + rng.nextInt(2));
                    noter(e, "embuscade");
                } else if (c == 1) {
                    z.pont.zaevt("imitateur " + u);
                    noter(e, "imitateur");
                } else {
                    Horde h;
                    synchronized (z.monde) {
                        h = z.monde.attirerHorde(l.getX(), l.getZ(), 700);
                    }
                    noter(e, h == null ? "aucune horde à dévier" : "horde #" + h.id + " déviée vers lui");
                }
                break;
            }
            case "pic": {
                if (nouveau) {
                    embuscade(p, 3);
                    noter(e, "pic doux (nouveau joueur)");
                    break;
                }
                List<String> choix = new ArrayList<>();
                choix.add("horde");
                choix.add("evenement");
                if (z.nemesis.aUneNemesis(p.getUniqueId())) choix.add("nemesis");
                // profil : chacun ses moments forts
                if (e.kills > e.construits && e.kills > 50) choix.add("nemesis");
                if (e.construits > e.kills) choix.add("siege");
                if (e.regions > 5) choix.add("decouverte");
                choix.remove(e.dernierPic);            // anti-routine
                String k = choix.get(rng.nextInt(choix.size()));
                e.dernierPic = k;
                e.momentFait = true;
                switch (k) {
                    case "nemesis":
                        if (z.nemesis.revanche(p)) noter(e, "revanche de la Némésis");
                        else embuscade(p, 4);
                        break;
                    case "horde": {
                        Horde h;
                        synchronized (z.monde) {
                            h = z.monde.attirerHorde(l.getX(), l.getZ(), 1200);
                            if (h != null) {
                                h.objectif = "traquer";
                                h.traquee = u;
                                h.cx = l.getX();
                                h.cz = l.getZ();
                            }
                        }
                        noter(e, h == null ? "pas de horde : embuscade" : "horde #" + h.id + " lancée sur lui");
                        if (h == null) embuscade(p, 4);
                        break;
                    }
                    case "siege":
                        z.pont.zaevt("evenement siege " + u);
                        noter(e, "siège (bâtisseur)");
                        break;
                    case "decouverte":
                        z.pont.zaevt("evenement decouverte " + u);
                        noter(e, "découverte (explorateur)");
                        break;
                    default:
                        String[] ev = {"crash", "largage", "convoi_attaque", "survivant_poursuivi", "alarme", "chien_guide", "patrouille_norda", "fausse_alerte", "signal_inconnu"};
                        String t = ev[rng.nextInt(ev.length)];
                        z.pont.zaevt("evenement " + t + " " + u);
                        noter(e, "événement sans annonce : " + t);
                }
                break;
            }
            default: {
                // relâche : c'est le moment des SMS, de la radio, des PNJ, des découvertes
                z.pont.zaevt("relache " + u);
                noter(e, "relâche");
            }
        }
        // quota : au moins un moment fort par session
        if (!e.momentFait && now - e.sessionDebut > 40 * 60_000L && !e.phase.equals("relache")) {
            e.momentFait = true;
            z.pont.zaevt("evenement moment_fort " + u);
            noter(e, "moment fort forcé (quota de session)");
        }
    }

    /** quelques morts tirés du génome de la région, à 20-35 blocs, hors de vue (règle 6) */
    public void embuscade(Player p, int n) {
        Region r;
        synchronized (z.monde) {
            r = z.monde.graphe.region(p.getLocation().getX(), p.getLocation().getZ());
        }
        for (int i = 0; i < n; i++) {
            Location l = z.mat.pointHorsVue(p, 20, 35);
            if (l == null) continue;
            String t = r != null ? r.tirerType(z.monde.rng) : "ZA_Shambler";
            Bukkit.dispatchCommand(Bukkit.getConsoleSender(), "mm mobs spawn " + t + " 1 " + l.getWorld().getName() + "," + l.getBlockX() + "," + l.getBlockY() + "," + l.getBlockZ());
        }
    }

    void jour() {
        for (Etat e : etats.values()) {
            e.kills = (int) (e.kills * 0.8);
            e.construits = (int) (e.construits * 0.8);
        }
    }

    public List<String> rapport(UUID u) {
        Etat e = etat(u);
        List<String> r = new ArrayList<>();
        r.add("Intensité " + (int) e.intensite + " — phase " + e.phase + (relacheActive(u) ? " (relâche active)" : "")
                + " — profil : " + e.kills + " éliminations, " + e.construits + " constructions, " + e.social + " s en groupe");
        r.addAll(e.carnet.subList(Math.max(0, e.carnet.size() - 15), e.carnet.size()));
        return r;
    }

    void sauver(ConfigurationSection s) {
        for (Map.Entry<UUID, Etat> en : etats.entrySet()) {
            String p = en.getKey().toString() + ".";
            s.set(p + "kills", en.getValue().kills);
            s.set(p + "construits", en.getValue().construits);
            s.set(p + "dernier_pic", en.getValue().dernierPic);
        }
    }

    void charger(ConfigurationSection s) {
        if (s == null) return;
        for (String k : s.getKeys(false)) {
            try {
                Etat e = etat(UUID.fromString(k));
                e.kills = s.getInt(k + ".kills");
                e.construits = s.getInt(k + ".construits");
                e.dernierPic = s.getString(k + ".dernier_pic", "");
            } catch (IllegalArgumentException ignored) {
                // clé abîmée
            }
        }
    }

    public Player joueur(String u) {
        try {
            return Bukkit.getPlayer(UUID.fromString(u));
        } catch (IllegalArgumentException e) {
            return null;
        }
    }
}
