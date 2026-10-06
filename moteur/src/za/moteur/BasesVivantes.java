package za.moteur;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import za.moteur.coeur.Bases;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Region;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Le pont entre le cerveau des bases (coeur.Bases, IA-15 / IA-8) et le serveur : Skript décrit les bases et les
 * survivants (zam basestock, zam surv, zam survres), le cerveau décide toutes les 5 minutes, et les ordres repartent
 * vers Skript (zaevt base_sortie, base_prudent, base_journal, base_avis, base_conflit, base_depart).
 */
public final class BasesVivantes {
    private final ZAMoteur z;
    public final Bases cerveau;
    private long dernier;

    BasesVivantes(ZAMoteur z) {
        this.z = z;
        this.cerveau = new Bases(new java.util.Random());
    }

    private static boolean enLigne(String uuid) {
        try {
            return Bukkit.getPlayer(UUID.fromString(uuid)) != null;
        } catch (IllegalArgumentException e) {
            return false;
        }
    }

    /** chaque seconde (fil principal) : la décision ne tourne que toutes les 5 minutes (cadence F1) */
    void tick1s() {
        long now = System.currentTimeMillis();
        if (now - dernier < 300_000) return;
        dernier = now;
        long t = z.mondePrincipal().getTime();
        boolean nuit = z.estNuit();
        boolean matin = t >= 0 && t < 4000;
        List<Bases.Ordre> ordres = cerveau.decider(z.jour(), nuit, matin, BasesVivantes::enLigne, b -> {
            synchronized (z.monde) {
                Region r = z.monde.graphe.region(b.x, b.z);
                return r == null ? 0 : r.contamination;
            }
        }, now);
        executer(ordres);
    }

    /** /zaadmin chaine 10 : décider tout de suite */
    void forcer() {
        dernier = 0;
        tick1s();
    }

    void jour() {
        executer(cerveau.jour(z.jour(), BasesVivantes::enLigne));
        for (Bases.Base b : cerveau.bases.values()) {
            z.pont.set("bv::" + b.proprio + "::etat", b.etat);
            if (!b.bilan.isEmpty()) z.pont.set("bv::" + b.proprio + "::bilan", b.bilan.get(0));
        }
    }

    private void executer(List<Bases.Ordre> ordres) {
        for (Bases.Ordre o : ordres) {
            Bases.Survivant s = cerveau.survivants.get(o.survivant);
            switch (o.type) {
                case "sortie":
                    z.pont.zaevt("base_sortie " + o.base + " " + o.survivant + " " + o.tache);
                    z.pont.zaevt("base_journal " + o.base + " " + o.texte);
                    break;
                case "prudent":
                    z.pont.zaevt("base_prudent " + o.base + " " + o.survivant + " " + o.tache + " " + o.quantite);
                    z.pont.zaevt("base_journal " + o.base + " " + o.texte);
                    if (s != null) publier("mission_survivant", o.base, 1, "pnj:" + s.id, o.texte);
                    break;
                case "journal":
                    z.pont.zaevt("base_journal " + o.base + " " + o.texte);
                    break;
                case "avis":
                    z.pont.zaevt("base_avis " + o.base + " " + o.texte);
                    break;
                case "conflit":
                    z.pont.zaevt("base_avis " + o.base + " " + o.texte);
                    publier("conflit_camp", o.base, 2, "pnj:" + o.survivant + ",pnj:" + o.tache, o.texte);
                    break;
                case "depart":
                    z.pont.zaevt("base_depart " + o.base + " " + o.survivant);
                    z.pont.zaevt("base_avis " + o.base + " " + o.texte);
                    publier("depart_survivant", o.base, 3, "pnj:" + o.survivant, o.texte);
                    break;
                default:
                    break;
            }
        }
    }

    private void publier(String type, String proprio, int g, String acteurs, String texte) {
        Location l = null;
        try {
            l = z.bases.get(UUID.fromString(proprio));
        } catch (IllegalArgumentException ignored) {
            // pas un uuid
        }
        Evenement e = new Evenement(type).grav(g).dit(texte);
        if (l != null) e.a(l.getX(), l.getZ());
        for (String a : acteurs.split(",")) e.acteur(a);
        e.visibilite = "prive";
        z.publier(e);
    }

    // ================================================================ ce que Skript décrit

    /** zam basestock <uuid> nourriture:12 bois:40 ... */
    void stocks(String[] a) {
        Bases.Base b = cerveau.base(a[1]);
        for (int k = 2; k < a.length; k++) {
            int i = a[k].indexOf(':');
            if (i > 0) b.stocks.put(a[k].substring(0, i), Integer.parseInt(a[k].substring(i + 1)));
        }
        try {
            Location l = z.bases.get(UUID.fromString(a[1]));
            if (l != null) {
                b.x = l.getX();
                b.z = l.getZ();
            }
        } catch (IllegalArgumentException ignored) {
            // pas un uuid
        }
    }

    /** zam surv <id> <base|-> <métier> <état> <mission 0|1> <blessé 0|1> <fatigue> <santé> <moral> <trait|-> <aversion|-> <récolte> <combat> <médical> <méca> <nom...> */
    void survivant(String[] a) {
        Bases.Survivant s = cerveau.survivant(Integer.parseInt(a[1]));
        s.base = a[2].equals("-") ? "" : a[2];
        s.metier = a[3];
        s.etat = a[4];
        s.enMission = a[5].equals("1");
        s.blesse = a[6].equals("1");
        s.fatigue = Double.parseDouble(a[7]);
        s.sante = Double.parseDouble(a[8]);
        s.moral = Double.parseDouble(a[9]);
        s.trait = a[10].equals("-") ? "" : a[10];
        s.aversion = a[11].equals("-") ? "" : a[11];
        String[] cles = {"recolte", "combat", "medical", "meca"};
        for (int k = 0; k < 4; k++) {
            double v = Double.parseDouble(a[12 + k]) * 10;
            s.competences.put(cles[k], Math.max(s.competences.getOrDefault(cles[k], 0.0), v));
        }
        StringBuilder n = new StringBuilder();
        for (int k = 16; k < a.length; k++) n.append(k > 16 ? " " : "").append(a[k]);
        s.nom = n.toString();
        s.vu = System.currentTimeMillis();
        cerveau.personnalite(s);
    }

    /** zam survres <id> <tâche> <issue> <n> : le résultat d'une vraie sortie de za_p92 */
    void resultat(String[] a) {
        Bases.Survivant s = cerveau.survivant(Integer.parseInt(a[1]));
        String l = cerveau.resultat(s, a[2], a[3], Integer.parseInt(a[4]), z.jour());
        publier("mission_survivant", s.base, a[3].equals("blesse") ? 2 : 1, "pnj:" + s.id, s.nom + " — " + l);
    }

    // ================================================================ /zaadmin base <joueur>

    void admin(CommandSender s, String[] a) {
        if (a.length < 2) {
            s.sendMessage("§7/zaadmin base <joueur> · /zaadmin survivant <id>");
            return;
        }
        if (a[0].equals("survivant")) {
            Bases.Survivant v = cerveau.survivants.get(Integer.parseInt(a[1]));
            if (v == null) {
                s.sendMessage("§7Inconnu du moteur.");
                return;
            }
            s.sendMessage("§6" + v.nom + " §7(" + v.metier + ", " + v.etat + (v.blesse ? ", blessé" : "") + ") fatigue " + (int) v.fatigue + ", moral " + (int) v.moral);
            s.sendMessage("§7courage " + (int) v.courage + ", honnêteté " + (int) v.honnetete + ", loyauté " + (int) v.loyaute + ", avidité " + (int) v.avidite
                    + ", empathie " + (int) v.empathie + ", paranoïa " + (int) v.paranoia + ", sociabilité " + (int) v.sociabilite);
            s.sendMessage("§7compétences " + v.competences + (v.intention.isEmpty() ? "" : " — intention : " + v.intention) + (v.secret.isEmpty() ? "" : " — §csecret : " + v.secret));
            for (String j : v.journal) s.sendMessage("§8  " + j);
            return;
        }
        Player p = Bukkit.getPlayerExact(a[1]);
        String u = p != null ? p.getUniqueId().toString() : a[1];
        Bases.Base b = cerveau.bases.get(u);
        if (b == null) {
            s.sendMessage("§7Aucune base vivante pour " + a[1] + ".");
            return;
        }
        s.sendMessage("§6[Base] §f" + a[1] + " — " + b.etat + ", moral " + (int) b.moral + (b.sortiesInterdites ? ", sorties interdites" : ""));
        List<String> st = new ArrayList<>();
        for (String r : Bases.RESSOURCES) st.add(r + " " + b.stock(r) + "/" + b.min(r));
        s.sendMessage("§7stocks : " + String.join(", ", st));
        if (!b.bilan.isEmpty()) s.sendMessage("§7bilan : " + b.bilan.get(0));
        for (String h : b.historique.subList(Math.max(0, b.historique.size() - 8), b.historique.size())) s.sendMessage("§8  " + h);
    }

    void interdire(String u, boolean oui) {
        cerveau.base(u).sortiesInterdites = oui;
    }

    void minimum(String u, String res, int n) {
        cerveau.base(u).minimums.put(res, Math.max(0, n));
    }

    /** au retour du joueur : le rapport d'absence (règle 2) */
    List<String> absence(String u) {
        Bases.Base b = cerveau.bases.get(u);
        if (b == null) return new ArrayList<>();
        List<String> l = new ArrayList<>(b.absence);
        b.absence.clear();
        return l;
    }
}
