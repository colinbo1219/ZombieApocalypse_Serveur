package za.moteur;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitRunnable;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Graphe;
import za.moteur.coeur.Horde;
import za.moteur.coeur.Monde;
import za.moteur.coeur.Norda;
import za.moteur.coeur.Region;
import za.moteur.coeur.Simulateur;

import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Logger;

/**
 * ZAMoteur — le moteur du monde (bible ZA, F1 « ZAMonde 2.0 »).
 * La simulation (graphe, régions, hordes, contamination, NORDA, Chronique, réactions) tourne HORS du fil principal ;
 * le fil principal ne fait que les actions visibles (apparitions, blocs, effets), avec un budget par tick.
 * Skript garde le contenu (dialogues, menus, commandes joueurs) : il appelle le moteur par « zam ... » et le moteur
 * lui répond par « zaevt ... » (za_p103_moteur.sk).
 */
public final class ZAMoteur extends JavaPlugin {
    private static ZAMoteur inst;

    public Monde monde;
    public Norda norda;
    public final Pont pont = new Pont();
    public Persistance persistance;
    public Materialisation mat;
    public Directeur directeur;
    public Cerveaux cerveaux;
    public Nemesis nemesis;
    public NordaReel nordaReel;
    public Lea lea;
    public Telemetrie telemetrie;
    public Ecosysteme ecosysteme;
    public Omega omega;
    public InfoJoueurs infoJoueurs;
    public BasesVivantes vivantes;
    public Societe societe;
    public Mensonges mensonges;

    /** bases enregistrées (/base, p8) : jamais envahies automatiquement (règle 2) */
    public final Map<UUID, Location> bases = new ConcurrentHashMap<>();
    public final Map<UUID, String> factions = new ConcurrentHashMap<>();
    public final Map<String, Boolean> systemes = new LinkedHashMap<>();
    public volatile int jourSkript = -1;
    private int jourTraite = -1;

    // budget du fil principal (F1) — valeurs de départ
    public int budgetSpawnsTick = 6, budgetBlocsTick = 200, budgetCommandesTick = 20;
    public int plafondReelsServeur = 350, plafondReelsJoueur = 40;

    public static Logger log() {
        return inst != null ? inst.getLogger() : Logger.getLogger("ZAMoteur");
    }

    public static ZAMoteur get() {
        return inst;
    }

    public boolean actif(String systeme) {
        return systemes.getOrDefault(systeme, true);
    }

    @Override
    public void onEnable() {
        inst = this;
        getDataFolder().mkdirs();
        copierDefaut("reactions.yml");
        copierDefaut("config.yml");
        reloadConfig();
        for (String s : new String[]{"hordes", "directeur", "cerveaux", "nemesis", "norda", "lea", "ecosysteme", "telemetrie", "materialisation", "bases", "factions", "omega"})
            systemes.put(s, getConfig().getBoolean("systemes." + s, !s.equals("omega")));
        budgetSpawnsTick = getConfig().getInt("budget.apparitions_par_tick", 6);
        budgetBlocsTick = getConfig().getInt("budget.blocs_par_tick", 200);
        plafondReelsServeur = getConfig().getInt("plafonds.zombies_reels_serveur", 350);
        plafondReelsJoueur = getConfig().getInt("plafonds.zombies_reels_joueur", 40);

        Graphe g;
        try {
            g = Graphe.charger(new File(getDataFolder(), "graphe.yml").toPath());
        } catch (Exception e) {
            log().warning("graphe.yml illisible (" + e.getMessage() + ") : grille de secours.");
            g = new Graphe();
            g.grilleVide();
        }
        monde = new Monde(g, 1250 + System.currentTimeMillis() % 1000);
        norda = new Norda(monde.rng);
        try {
            monde.reactions.charger(new File(getDataFolder(), "reactions.yml").toPath());
        } catch (Exception e) {
            log().warning("reactions.yml : " + e.getMessage());
        }
        persistance = new Persistance(this);
        persistance.charger();
        telemetrie = new Telemetrie(this);
        mat = new Materialisation(this);
        directeur = new Directeur(this);
        cerveaux = new Cerveaux(this);
        nemesis = new Nemesis(this);
        nordaReel = new NordaReel(this);
        lea = new Lea(this);
        ecosysteme = new Ecosysteme(this);
        omega = new Omega(this);
        infoJoueurs = new InfoJoueurs(this);
        vivantes = new BasesVivantes(this);
        societe = new Societe(this);
        mensonges = new Mensonges(this);
        monde.memoire.annonce = t -> pont.zaevt("legende " + t);
        persistance.chargerModules();

        monde.pont = this::actionServeur;
        monde.chronique.ecouter(e -> {
            telemetrie.evenement(e);
            lea.evenement(e);
            if (e.gravite >= 3) pont.zaevt("chron " + e.gravite + " " + e.ligne());
        });
        Bukkit.getPluginManager().registerEvents(new Ecouteurs(this), this);

        // fil principal : chaque tick, le budget d'actions visibles
        new BukkitRunnable() {
            @Override
            public void run() {
                pont.vider(budgetCommandesTick);
                mat.tickPrincipal();
            }
        }.runTaskTimer(this, 1L, 1L);
        // fil principal : chaque seconde, perception et Directeur (les entités ne se lisent que là)
        new BukkitRunnable() {
            @Override
            public void run() {
                if (actif("directeur")) directeur.tick1s();
                if (actif("cerveaux")) cerveaux.tick1s();
                if (actif("norda")) nordaReel.tick1s();
                if (actif("nemesis")) nemesis.tick1s();
                if (actif("bases")) vivantes.tick1s();
            }
        }.runTaskTimer(this, 40L, 20L);
        // HORS du fil principal : la simulation, toutes les 30 secondes
        new BukkitRunnable() {
            @Override
            public void run() {
                List<Materialisation.Pos> joueurs = new ArrayList<>(mat.positionsJoueurs());
                synchronized (monde) {
                    monde.nuit = estNuit();
                    if (actif("hordes")) monde.tick30s();
                    jourSiBesoin();
                }
                mat.planifier(joueurs);
            }
        }.runTaskTimerAsynchronously(this, 200L, 600L);
        // fil principal : toutes les 30 s, publier l'état des joueurs vers Skript (/zone, /signal, /ville)
        new BukkitRunnable() {
            @Override
            public void run() {
                // signe de vie pour Skript (za_mot_actif)
                pont.set("pret", String.valueOf(System.currentTimeMillis() / 1000));
                publierEtatsJoueurs();
                if (actif("ecosysteme")) ecosysteme.tick30s();
                if (actif("lea")) lea.tick30s();
                infoJoueurs.tick30s();
                if (actif("factions")) societe.tick30s();
            }
        }.runTaskTimer(this, 300L, 600L);
        // sauvegarde toutes les 5 minutes
        new BukkitRunnable() {
            @Override
            public void run() {
                persistance.sauver();
            }
        }.runTaskTimer(this, 6000L, 6000L);
        log().info("ZAMoteur prêt : " + monde.graphe.regions.size() + " régions, " + monde.graphe.lieux.size() + " lieux, "
                + monde.reactions.regles.size() + " règles de réaction, " + monde.hordes.size() + " hordes.");
    }

    @Override
    public void onDisable() {
        if (mat != null) mat.toutDematerialiser();
        if (persistance != null) persistance.sauver();
    }

    private void copierDefaut(String nom) {
        File f = new File(getDataFolder(), nom);
        if (f.exists()) return;
        try (InputStream in = getResource(nom)) {
            if (in != null) Files.copy(in, f.toPath(), StandardCopyOption.REPLACE_EXISTING);
        } catch (Exception e) {
            log().warning("Copie de " + nom + " impossible : " + e.getMessage());
        }
    }

    public World mondePrincipal() {
        World w = Bukkit.getWorld("world");
        return w != null ? w : Bukkit.getWorlds().get(0);
    }

    public boolean estNuit() {
        World w = mondePrincipal();
        long t = w.getTime();
        return t > 13000 && t < 23000;
    }

    public int jour() {
        return monde.jour;
    }

    /** le jour serveur vient de Skript ({za::serveur::jours}) ; à défaut, du temps du monde */
    private void jourSiBesoin() {
        int j = jourSkript >= 0 ? jourSkript : (int) (mondePrincipal().getFullTime() / 24000L);
        if (jourTraite < 0) {
            jourTraite = j;
            monde.jour = j;
            return;
        }
        if (j > jourTraite) {
            jourTraite = j;
            monde.tickJour();
            monde.jour = j;
            List<Norda.Ordre> ordres = actif("norda") ? norda.planDuJour(j) : new ArrayList<>();
            Bukkit.getScheduler().runTask(this, () -> {
                nordaReel.executer(ordres);
                telemetrie.jour();
                lea.jour();
                nemesis.jour();
                directeur.jour();
                omega.jour();
                if (actif("bases")) vivantes.jour();
                if (actif("factions")) societe.jour();
                if (actif("bases")) mensonges.jour();
                pont.set("monde::jour_moteur", String.valueOf(j));
            });
        }
    }

    // ================================================================ actions des réactions confiées au serveur

    private void actionServeur(String action, Evenement src) {
        String[] t = action.trim().split("\\s+", 3);
        String lieu = nomLieu(src);
        switch (t[0]) {
            case "radio":
                if (t.length >= 3) pont.radio(t[1], remplacer(t[2], src, lieu));
                return;
            case "skript":
                if (t.length >= 2) pont.console(remplacer(action.substring(7), src, lieu));
                return;
            case "sms":
                for (String a : src.acteurs) if (a.length() == 36) pont.sms(a, "Inconnu", remplacer(action.substring(4), src, lieu));
                return;
            case "norda":
                if (t.length >= 3 && t[1].equals("soupcon")) {
                    double n = Double.parseDouble(t[2].replace("+", ""));
                    synchronized (monde) {
                        for (String a : src.acteurs) if (a.length() == 36) norda.preuve(a, "agent", n, src.x, src.z, monde.jour, 0);
                    }
                }
                return;
            case "pluie_toxique":
                pont.zaevt("pluie_toxique " + (int) src.x + " " + (int) src.z);
                return;
            case "signes":
                ecosysteme.signes(src.x, src.z, 600);
                return;
            case "graffiti":
                pont.zaevt("graffiti " + (int) src.x + " " + (int) src.z + " " + remplacer(action.substring(9), src, lieu));
                return;
            case "son":
                if (t.length >= 2) pont.zaevt("son_loin " + (int) src.x + " " + (int) src.z + " " + t[1]);
                return;
            default:
                log().fine("Action inconnue : " + action);
        }
    }

    public String nomLieu(Evenement e) {
        if (e.texte != null && !e.texte.isEmpty() && e.texte.length() < 50 && !e.texte.contains(" ")) return e.texte;
        Graphe.Lieu l = monde.graphe.lieuProche(e.x, e.z, 300);
        if (l != null) return l.nom;
        Region r = monde.graphe.regions.get(e.region);
        return r == null ? "la région" : r.nom;
    }

    private String remplacer(String s, Evenement e, String lieu) {
        return s.replace("{lieu}", lieu).replace("{texte}", e.texte).replace("{region}", e.region == null ? "?" : e.region)
                .replace("{acteurs}", String.join(",", e.acteurs).isEmpty() ? "-" : String.join(",", e.acteurs));
    }

    /** publication depuis le fil principal ou Skript */
    public Evenement publier(Evenement e) {
        synchronized (monde) {
            return monde.publier(e);
        }
    }

    // ================================================================ états des joueurs vers Skript

    private void publierEtatsJoueurs() {
        for (Player p : Bukkit.getOnlinePlayers()) {
            if (p.getWorld().getName().equals("za_prologue")) continue;
            Location l = p.getLocation();
            Region r;
            Norda.Dossier d;
            synchronized (monde) {
                r = monde.graphe.region(l.getX(), l.getZ());
                d = norda.dossiers.get(p.getUniqueId().toString());
                if (r != null) norda.route(p.getUniqueId().toString(), r.id);
            }
            if (r == null) continue;
            String u = p.getUniqueId().toString();
            pont.set("reg::" + u, r.id + "|" + r.nom.replace('|', '/') + "|" + r.etat + "|" + (int) r.contamination + "|" + (int) r.eau
                    + "|" + (int) r.danger() + "|" + r.nids + "|" + (int) r.population + "|" + (r.courant ? 1 : 0) + "|" + (int) r.attentionZ
                    + "|" + (int) r.vegetation + "|" + r.tours + "|" + (r.quarantaineJusqua >= monde.jour ? 1 : 0));
            pont.set("palier::" + u, d == null ? "0" : String.valueOf(d.palier));
            // réputation de proie (71) : ce que les morts retiennent de toi (éliminations récentes)
            pont.set("proie::" + u, String.valueOf(directeur.etat(p.getUniqueId()).kills));
            // ce que la région a appris (IA-6), pour le bestiaire : le trait le plus fort, en mots
            String adapt = "";
            double best = 0.25;
            synchronized (monde) {
                for (Map.Entry<String, Double> t : r.traits.entrySet())
                    if (t.getValue() > best) {
                        best = t.getValue();
                        adapt = t.getKey();
                    }
            }
            pont.set("adapt::" + u, adapt.isEmpty() ? "-" : adapt);
        }
    }

    // ================================================================ commandes

    @Override
    public boolean onCommand(CommandSender s, Command c, String label, String[] a) {
        String n = c.getName().toLowerCase(Locale.ROOT);
        try {
            if (n.equals("zam")) return Commandes.zam(this, s, a);
            if (n.equals("zaadmin")) return Commandes.zaadmin(this, s, a);
            if (n.equals("infos")) return infoJoueurs.infos(this, s, a);
            if (n.equals("signaler")) return infoJoueurs.signaler(this, s, a);
        } catch (RuntimeException e) {
            s.sendMessage("§c[ZAMoteur] erreur : " + e.getMessage());
            log().warning("Commande " + n + " " + Arrays.toString(a) + " : " + e);
        }
        return true;
    }

    // ================================================================ simulateur depuis le jeu (F6)

    public void simuler(CommandSender s, int jours, int fantomes) {
        Bukkit.getScheduler().runTaskAsynchronously(this, () -> {
            try {
                Graphe g = Graphe.charger(new File(getDataFolder(), "graphe.yml").toPath());
                Monde m = new Monde(g, 1250);
                m.reactions.charger(new File(getDataFolder(), "reactions.yml").toPath());
                // copie de l'état actuel des régions
                synchronized (monde) {
                    for (Region r : monde.graphe.regions.values()) {
                        Region c = m.graphe.regions.get(r.id);
                        if (c == null) continue;
                        c.contamination = r.contamination;
                        c.nids = r.nids;
                        c.nidStade = r.nidStade;
                        c.cadavres = r.cadavres;
                        c.courant = r.courant;
                    }
                    for (Horde h : monde.hordes) {
                        Horde k = m.creerHorde(m.graphe.regions.get(h.region), h.taille);
                        if (k != null) {
                            k.x = h.x;
                            k.z = h.z;
                        }
                    }
                }
                List<String> rapport = Simulateur.simuler(m, jours, fantomes);
                Bukkit.getScheduler().runTask(this, () -> {
                    s.sendMessage("§6[Simulateur] §7" + jours + " jours, " + fantomes + " joueurs fantômes :");
                    for (String l : rapport) s.sendMessage("§7" + l);
                });
            } catch (Exception e) {
                Bukkit.getScheduler().runTask(this, () -> s.sendMessage("§cSimulateur : " + e.getMessage()));
            }
        });
    }

    /** au retour d'un joueur : ce qui s'est passé à sa base pendant son absence (règle 2) */
    public void rapportAbsence(Player p) {
        Bukkit.getScheduler().runTaskLater(this, () -> {
            if (!p.isOnline()) return;
            List<String> l = vivantes.absence(p.getUniqueId().toString());
            if (l.isEmpty()) return;
            p.sendMessage("§6§l━━ PENDANT TON ABSENCE ━━");
            for (int i = Math.max(0, l.size() - 10); i < l.size(); i++) p.sendMessage("§7• " + l.get(i));
        }, 120L);
    }

    public Map<String, Object> resumeSystemes() {
        Map<String, Object> m = new HashMap<>();
        synchronized (monde) {
            m.put("regions", monde.graphe.regions.size());
            m.put("hordes", monde.hordes.size());
            m.put("chronique", monde.chronique.total);
            m.put("reactions_attente", monde.reactions.enAttente());
            m.put("reactions_declenchees", monde.reactions.declenchees);
            m.put("dossiers_norda", norda.dossiers.size());
        }
        m.put("zombies_reels", mat.totalReels());
        m.put("commandes_skript", pont.envoyees);
        return m;
    }
}
