package za.moteur;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Information;
import za.moteur.coeur.Memoire;
import za.moteur.coeur.Region;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Ce que chaque joueur SAIT (bible F9, S-5, S-9) : les nouvelles de la région où il se trouve lui parviennent par
 * les gens, les camps et les relais radio, avec leur source, leur âge et leur fiabilité. Le joueur est aussi une
 * source : /signaler. Il peut transmettre ce qu'il sait : /infos dire. Le brouillard d'information du point 7.
 */
public final class InfoJoueurs {
    private final ZAMoteur z;
    private final Map<UUID, Long> derniereNotif = new HashMap<>();

    InfoJoueurs(ZAMoteur z) {
        this.z = z;
    }

    private static String cle(Player p) {
        return "joueur:" + p.getUniqueId();
    }

    /** toutes les 30 s : ce qui se dit dans la région arrive aux joueurs qui y sont */
    void tick30s() {
        long now = System.currentTimeMillis();
        for (Player p : z.mondePrincipal().getPlayers()) {
            Location l = p.getLocation();
            Information.Connue montrer = null;
            synchronized (z.monde) {
                Region r = z.monde.graphe.region(l.getX(), l.getZ());
                if (r == null) continue;
                Information inf = z.monde.info;
                int appris = 0;
                for (Information.Connue c : inf.savoir("region:" + r.id)) {
                    if (appris >= 3) break;
                    if (inf.sait(cle(p), c.info.id)) continue;
                    Information.Connue k = inf.apprendre(cle(p), c.info, c.texte, c.fiabilite - 5, c.canal.equals("radio") ? "radio" : "rumeur", c.sauts + 1);
                    k.morceaux = c.morceaux;
                    appris++;
                    if (c.info.importance >= 25 && (montrer == null || c.info.importance > montrer.info.importance)) montrer = k;
                }
                if (montrer != null) {
                    Long d = derniereNotif.get(p.getUniqueId());
                    if (d != null && now - d < 180_000) montrer = null;
                }
                if (montrer != null) {
                    derniereNotif.put(p.getUniqueId(), now);
                    p.sendMessage("§8[" + (montrer.canal.equals("radio") ? "Sur les ondes" : "On dit") + "] §7" + inf.vu(montrer)
                            + " §8(" + source(montrer) + ", " + Information.age(now - montrer.info.cree) + ", " + Information.fiabiliteActuelle(montrer, now) + " %)");
                }
            }
        }
    }

    private static String source(Information.Connue c) {
        switch (c.info.source) {
            case "joueur":
                return "un survivant comme toi";
            case "drone":
                return "un drone";
            case "fuite":
                return "une fuite";
            case "radio":
                return "la radio";
            default:
                return c.sauts <= 1 ? "un témoin" : "de bouche à oreille";
        }
    }

    // ---------------------------------------------------------------- commandes joueurs

    boolean infos(ZAMoteur z, CommandSender s, String[] a) {
        if (!(s instanceof Player)) return true;
        Player p = (Player) s;
        long now = System.currentTimeMillis();
        if (a.length >= 3 && a[0].equals("dire")) {
            Player cible = Bukkit.getPlayerExact(a[1]);
            if (cible == null || cible.getWorld() != p.getWorld() || cible.getLocation().distance(p.getLocation()) > 12) {
                p.sendMessage("§7Il faut être à côté de la personne pour lui dire ça (ou passer par la radio).");
                return true;
            }
            synchronized (z.monde) {
                List<Information.Connue> l = z.monde.info.savoir(cle(p));
                int n;
                try {
                    n = Integer.parseInt(a[2]) - 1;
                } catch (NumberFormatException e) {
                    n = -1;
                }
                if (n < 0 || n >= l.size()) {
                    p.sendMessage("§7Numéro inconnu (/infos pour la liste).");
                    return true;
                }
                Information.Connue c = l.get(n);
                // un joueur est une source comme une autre : ce qu'il transmet perd un peu en route
                z.monde.info.apprendre(cle(cible), c.info, c.texte, Math.min(c.fiabilite, 70), "joueur:" + p.getName(), c.sauts + 1);
                cible.sendMessage("§8[" + p.getName() + "] §7" + z.monde.info.vu(c) + " §8(" + Information.age(now - c.info.cree) + ")");
            }
            p.sendMessage("§7Tu lui as dit ce que tu savais.");
            return true;
        }
        int page = 0;
        if (a.length >= 1) {
            try {
                page = Math.max(0, Integer.parseInt(a[0]) - 1);
            } catch (NumberFormatException ignored) {
                // page 1
            }
        }
        synchronized (z.monde) {
            List<Information.Connue> l = z.monde.info.savoir(cle(p));
            p.sendMessage("§3§l━━ CE QUE TU SAIS ━━ §8(" + l.size() + " nouvelles ; rien n'est garanti)");
            if (l.isEmpty()) p.sendMessage("§7Rien. Parle aux gens, écoute la radio, va voir.");
            for (int k = page * 8; k < Math.min(l.size(), page * 8 + 8); k++) {
                Information.Connue c = l.get(k);
                int f = Information.fiabiliteActuelle(c, now);
                String coul = f >= 70 ? "§a" : f >= 40 ? "§e" : "§c";
                p.sendMessage("§8" + (k + 1) + ". §7" + z.monde.info.vu(c) + " §8— " + source(c) + ", " + Information.age(now - c.info.cree)
                        + ", " + coul + f + " %" + (c.morceaux < 3 ? " §8(en morceaux)" : ""));
            }
            if (l.size() > page * 8 + 8) p.sendMessage("§8/infos " + (page + 2) + " pour la suite · /infos dire <joueur> <n°> · /signaler <ce que tu as vu>");
        }
        return true;
    }

    /** le joueur rapporte ce qu'il a vu : ça entre dans le réseau avec sa propre fiabilité (F9) */
    boolean signaler(ZAMoteur z, CommandSender s, String[] a) {
        if (!(s instanceof Player) || a.length == 0) {
            s.sendMessage("§7/signaler <ce que tu as vu> — ex. : /signaler une horde sur la 117 vers le barrage");
            return true;
        }
        Player p = (Player) s;
        String t = String.join(" ", a);
        if (t.length() > 120) t = t.substring(0, 120);
        Location l = p.getLocation();
        Evenement e = new Evenement("signalement").a(l.getX(), l.getZ()).grav(2).acteur(p.getUniqueId().toString()).dit(t).imp(20);
        e.source = "joueur";
        e.fiabilite = 55;
        for (Player o : p.getWorld().getPlayers()) if (o != p && o.getLocation().distance(l) < 32) e.temoin(o.getUniqueId().toString());
        z.publier(e);
        p.sendMessage("§7Tu fais passer le mot. §8(Ça voyagera de camp en camp, et ça se déformera peut-être.)");
        return true;
    }

    // ---------------------------------------------------------------- admin

    void admin(CommandSender s, String[] a) {
        if (a.length < 2) {
            s.sendMessage("§7/zaadmin memoire <clé> · /zaadmin relation <de> <envers> · /zaadmin savoir <clé> · /zaadmin legendes");
            return;
        }
        synchronized (z.monde) {
            switch (a[0]) {
                case "memoire":
                    for (Memoire.Souvenir v : z.monde.memoire.souvenirs(resoudre(a[1])))
                        s.sendMessage("§7J" + v.jour + " §f" + v.texte + " §8(certitude " + v.certitude + ", importance " + v.importance
                                + (v.interpretation.isEmpty() ? "" : ", « " + v.interpretation + " »") + ")");
                    break;
                case "relation": {
                    if (a.length < 3) return;
                    Memoire.Relation r = z.monde.memoire.relations.get(resoudre(a[1]) + "|" + resoudre(a[2]));
                    if (r == null) {
                        s.sendMessage("§7Aucune relation enregistrée.");
                        return;
                    }
                    s.sendMessage("§6" + a[1] + " → " + a[2] + " : §f" + r.niveau() + " §8(confiance " + (int) r.confiance + ", gratitude " + (int) r.gratitude
                            + ", peur " + (int) r.peur + ", ressentiment " + (int) r.ressentiment + ")");
                    for (String x : r.raisons) s.sendMessage("§8  " + x);
                    break;
                }
                case "savoir":
                    for (Information.Connue c : z.monde.info.savoir(resoudre(a[1])))
                        s.sendMessage("§7" + c.texte + " §8(" + c.info.nature + ", " + c.canal + ", " + c.fiabilite + " %, sauts " + c.sauts + ")");
                    break;
                default:
                    break;
            }
        }
    }

    /** un pseudo devient sa clé « joueur:uuid » ; le reste passe tel quel (region:r_3_4, faction:milice, pnj:12) */
    static String resoudre(String n) {
        Player p = Bukkit.getPlayerExact(n);
        if (p != null) return "joueur:" + p.getUniqueId();
        if (n.length() == 36) return "joueur:" + n;
        return n;
    }
}
