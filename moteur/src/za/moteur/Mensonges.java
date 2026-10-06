package za.moteur;

import org.bukkit.Bukkit;
import org.bukkit.entity.Player;
import za.moteur.coeur.Bases;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Graphe;
import za.moteur.coeur.Information;
import za.moteur.coeur.Memoire;
import za.moteur.coeur.Norda;
import za.moteur.coeur.Region;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.UUID;

/**
 * Le mensonge lisible (bible IA-9, points 75, 76, 98). Un PNJ ne ment jamais au hasard : il ment s'il a un intérêt
 * (un secret à protéger, de l'avidité, une loyauté ailleurs) ET si son honnêteté est basse. Quatre réponses : vraie,
 * fausse par erreur, mensonge pour protéger un secret, mensonge pour envoyer dans un piège. Toujours un indice :
 * phrase nerveuse, contradiction avec ce que le joueur sait, un autre survivant qui souffle « demande à… ».
 * Démasquer un menteur coûte sa confiance au camp ; accuser à tort coûte la réputation de l'accusateur.
 */
public final class Mensonges {
    private final ZAMoteur z;
    private final Random rng = new Random();
    private static final String[] NERVEUX = {"Pourquoi tu me demandes ça ?", "Hein ? Euh... non.", "C'est quoi, un interrogatoire ?",
            "J'ai rien à voir avec ça, moi.", "Tu poses beaucoup de questions, toi."};

    Mensonges(ZAMoteur z) {
        this.z = z;
    }

    /** zam demander <uuid> <id> : le joueur demande « Qu'est-ce que tu sais ? » */
    void demander(String u, int id) {
        Bases.Survivant s = z.vivantes.cerveau.survivant(id);
        z.vivantes.cerveau.personnalite(s);
        String rep;
        boolean nerveux = false;
        String type = "vraie";
        Information.Connue c = null;
        synchronized (z.monde) {
            Region r = regionBase(s);
            List<Information.Connue> l = new ArrayList<>(z.monde.info.savoir("pnj:" + id));
            if (r != null) l.addAll(z.monde.info.savoir("region:" + r.id));
            for (Information.Connue k : l) if (c == null || k.info.importance > c.info.importance) c = k;
            Memoire.Relation rel = z.monde.memoire.relations.get("pnj:" + id + "|joueur:" + u);
            double confiance = rel == null ? 20 : rel.confiance + rel.gratitude / 2 - rel.ressentiment;
            boolean menteur = s.honnetete < 40;
            if (!s.secret.isEmpty() && menteur && (s.secret.equals("informateur") || rng.nextDouble() < 0.5)) {
                type = "secret";
                nerveux = true;
                if (s.secret.equals("informateur")) rep = rng.nextDouble() < 0.5 ? "NORDA ? Jamais vu un drone par ici. Et toi, tu sors souvent la nuit ? Tu vas où, d'habitude ?"
                        : "Rien de spécial. Dis donc, ta base, elle a du courant ? Juste pour savoir.";
                else if (s.secret.equals("voleur")) rep = "Les vivres qui manquent ? Ça doit être un des nouveaux. Moi, je dors, la nuit.";
                else rep = "Avant ? J'étais... caissier. Voilà. Caissier.";
            } else if (menteur && s.avidite > 65 && confiance < 0 && r != null) {
                type = "piege";
                nerveux = rng.nextDouble() < 0.5;
                Region rouge = plusDangereuse(r);
                rep = "Une cache intacte, du côté de " + (rouge == null ? "la vieille route" : rouge.nom) + ". Personne n'y est allé. Vas-y vite, avant les autres.";
            } else if (c != null) {
                int f = Information.fiabiliteActuelle(c, System.currentTimeMillis());
                if (f < 40) type = "erreur";
                rep = (f < 40 ? "J'en suis sûr : " : "Il paraît que ") + Character.toLowerCase(c.texte.charAt(0)) + c.texte.substring(1)
                        + " (" + Information.age(System.currentTimeMillis() - c.info.cree) + ")";
                // le joueur l'apprend, avec la fiabilité du PNJ
                Information.Connue k = z.monde.info.apprendre("joueur:" + u, c.info, c.texte, Math.min(c.fiabilite, (int) s.honnetete), "pnj:" + s.nom, c.sauts + 1);
                k.morceaux = 3;
            } else rep = "Rien de neuf. Les morts, comme d'habitude. Et la faim.";
        }
        if (nerveux) rep = NERVEUX[rng.nextInt(NERVEUX.length)] + " ... " + rep;
        z.pont.zaevt("pnj_dit " + u + " " + id + " " + rep);
        if (!type.equals("vraie") && !type.equals("erreur")) {
            // l'indice : un autre survivant de la base, empathique, souffle quelque chose (IA-9)
            Bases.Survivant temoin = null;
            for (Bases.Survivant o : z.vivantes.cerveau.survivants.values())
                if (o != s && s.base.equals(o.base) && o.empathie > 55 && o.honnetete > 55 && !o.etat.equals("mort")) temoin = o;
            if (temoin != null && rng.nextDouble() < 0.6) {
                String t = temoin.nom + " te glisse, plus tard : « " + s.nom + " ne dit pas tout. Regarde où il va, la nuit. »";
                Bukkit.getScheduler().runTaskLater(z, () -> z.pont.zaevt("base_avis " + u + " " + t), 20L * 90);
            }
            Evenement e = new Evenement("mensonge").grav(1).acteur("pnj:" + id).dit(s.nom + " a menti (" + type + ")");
            e.visibilite = "secret";
            e.savent.add("pnj:" + id);
            z.publier(e);
        }
    }

    /** zam accuser <uuid> <id> : « Je te soupçonne. » Vrai : il est démasqué. Faux : l'accusateur paie. */
    void accuser(String u, int id) {
        Bases.Survivant s = z.vivantes.cerveau.survivant(id);
        z.vivantes.cerveau.personnalite(s);
        Player p = joueur(u);
        double x = p == null ? 0 : p.getLocation().getX(), zz = p == null ? 0 : p.getLocation().getZ();
        List<String> temoins = new ArrayList<>();
        for (Bases.Survivant o : z.vivantes.cerveau.survivants.values()) if (o != s && s.base.equals(o.base)) temoins.add("pnj:" + o.id);
        if (!s.secret.isEmpty() && !s.secret.equals("agent_double")) {
            Evenement e = new Evenement("mensonge_demasque").a(x, zz).grav(2).acteur("pnj:" + id).dit(s.nom + " : " + secretTexte(s.secret));
            for (String t : temoins) e.temoin(t);
            z.publier(e);
            z.pont.zaevt("pnj_demasque " + u + " " + id + " " + s.secret);
            s.moral = Math.max(0, s.moral - 20);
            if (!s.secret.equals("informateur")) s.secret = "";
        } else {
            Evenement e = new Evenement("fausse_accusation").a(x, zz).grav(2).acteur(u).acteur("pnj:" + id).dit("accusé à tort : " + s.nom);
            for (String t : temoins) e.temoin(t);
            z.publier(e);
            z.pont.zaevt("pnj_dit " + u + " " + id + " Moi ? Après tout ce que j'ai fait ici ? ... Je m'en souviendrai.");
        }
    }

    /** zam retourner <uuid> <id> : l'informateur démasqué livre une fausse piste à NORDA (chaîne 4) */
    void retourner(String u, int id) {
        Bases.Survivant s = z.vivantes.cerveau.survivant(id);
        if (!s.secret.equals("informateur")) {
            z.pont.zaevt("pnj_dit " + u + " " + id + " Je ne sais pas de quoi tu parles.");
            return;
        }
        s.secret = "agent_double";
        synchronized (z.monde) {
            Norda.Dossier d = z.norda.dossier(u);
            double ang = rng.nextDouble() * Math.PI * 2;
            d.posX = d.posX + Math.cos(ang) * (1200 + rng.nextInt(800));
            d.posZ = d.posZ + Math.sin(ang) * (1200 + rng.nextInt(800));
            d.rayon = 150;
            d.posJour = z.jour();
            d.croyances.add("J" + z.jour() + " : selon notre informateur, le sujet s'est installé ailleurs (" + (int) d.posX + ", " + (int) d.posZ + ")");
        }
        z.pont.zaevt("pnj_dit " + u + " " + id + " D'accord. Je leur dirai que tu es parti vers l'autre bout de la région. Ils me croient, eux.");
    }

    /** chaque jour : les informateurs rapportent (98, chaîne 4) */
    void jour() {
        for (Bases.Survivant s : z.vivantes.cerveau.survivants.values()) {
            if (!s.secret.equals("informateur") || s.base.isEmpty() || s.etat.equals("mort")) continue;
            Bases.Base b = z.vivantes.cerveau.bases.get(s.base);
            if (b == null) continue;
            synchronized (z.monde) {
                z.norda.preuve(s.base, "informateur", 6, b.x, b.z, z.jour(), 0);
            }
        }
    }

    private static String secretTexte(String s) {
        switch (s) {
            case "informateur":
                return "il renseignait NORDA";
            case "voleur":
                return "c'est lui qui volait les vivres";
            default:
                return "il était avec les pillards, avant";
        }
    }

    private Region regionBase(Bases.Survivant s) {
        Bases.Base b = z.vivantes.cerveau.bases.get(s.base);
        if (b == null) return null;
        return z.monde.graphe.region(b.x, b.z);
    }

    private Region plusDangereuse(Region r) {
        Region best = null;
        for (Region v : z.monde.graphe.voisins(r.id)) if (best == null || v.danger() > best.danger()) best = v;
        return best;
    }

    private static Player joueur(String u) {
        try {
            return Bukkit.getPlayer(UUID.fromString(u));
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    @SuppressWarnings("unused")
    private static String lieu(Graphe g, double x, double z) {
        Graphe.Lieu l = g.lieuProche(x, z, 400);
        return l == null ? "" : l.nom;
    }
}
