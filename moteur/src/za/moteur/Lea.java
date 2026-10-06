package za.moteur;

import org.bukkit.configuration.ConfigurationSection;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Graphe;
import za.moteur.coeur.Region;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Léa et les radios journalistes (bible IA-12, points 17/74, 51/75, 93).
 * Chaque événement de la Chronique reçoit un score (gravité × nouveauté × proximité × implication des joueurs) ; les
 * meilleurs passent à l'antenne le soir même, avec une source et un degré de certitude. Léa se trompe parfois et se
 * corrige plus tard. Quatre stations, quatre tons. Si elle dit trop de vérités sur NORDA, NORDA la fait taire.
 */
public final class Lea {
    private final ZAMoteur z;
    private final List<Evenement> aDire = new ArrayList<>();
    private final List<Evenement> erreurs = new ArrayList<>();
    private final Random rng = new Random();
    public int veritesNorda;          // ce qu'elle a révélé sur NORDA
    public boolean silence;           // station réduite au silence (l'émetteur, 106)
    public int silenceDepuis = -1;
    private long derniere;
    private final Map<String, Integer> dejaDit = new HashMap<>();

    Lea(ZAMoteur z) {
        this.z = z;
    }

    void evenement(Evenement e) {
        if (e.gravite < 2) return;
        synchronized (aDire) {
            aDire.add(e);
            while (aDire.size() > 200) aDire.remove(0);
        }
    }

    private double score(Evenement e) {
        double nouveaute = 1.0 / (1 + dejaDit.getOrDefault(e.type, 0));
        double joueurs = 1;
        for (String a : e.acteurs) if (a.length() == 36) joueurs += 1;
        double age = Math.max(0.2, 1 - (System.currentTimeMillis() - e.quand) / (40 * 60_000.0));
        return e.gravite * nouveaute * joueurs * age;
    }

    /** toutes les 30 s : une nouvelle au plus toutes les 4 minutes */
    void tick30s() {
        if (!z.actif("lea") || silence) return;
        if (System.currentTimeMillis() - derniere < 4 * 60_000L) return;
        Evenement best = null;
        double bs = 2.5;
        synchronized (aDire) {
            for (Evenement e : aDire) {
                if (e.diffuse) continue;
                double s = score(e);
                if (s > bs) {
                    bs = s;
                    best = e;
                }
            }
            if (best == null) return;
            best.diffuse = true;
        }
        derniere = System.currentTimeMillis();
        dejaDit.merge(best.type, 1, Integer::sum);
        diffuser(best);
    }

    private void diffuser(Evenement e) {
        String lieu = z.nomLieu(e);
        // la source et sa fiabilité
        String source;
        double fiab = 0.8;
        if (e.verite.equals("faux")) {
            source = "une rumeur";
            fiab = 0.3;
        } else if (e.source.equals("joueur")) {
            source = "un auditeur";
            fiab = 0.6;
        } else if (e.type.startsWith("norda")) {
            source = "une fuite";
            fiab = 0.5;
        } else source = rng.nextDouble() < 0.5 ? "des témoins" : "un survivant sur place";
        String certitude = fiab >= 0.75 ? "confirmé" : fiab >= 0.5 ? "non confirmé" : "rumeur";
        String t = texte(e, lieu);
        if (t == null) return;
        // parfois, elle se trompe (lieu voisin) : elle se corrigera plus tard
        if (rng.nextDouble() < 0.08 && !e.type.startsWith("norda")) {
            Graphe.Lieu faux = null;
            synchronized (z.monde) {
                List<Graphe.Lieu> l = new ArrayList<>(z.monde.graphe.lieux.values());
                if (!l.isEmpty()) faux = l.get(rng.nextInt(l.size()));
            }
            if (faux != null) {
                t = t.replace(lieu, faux.nom);
                erreurs.add(e);
            }
        }
        z.pont.radio("lea", t + " (" + certitude + " — " + source + ")");
        // les autres stations racontent leur version (propagande contradictoire, 75)
        if (e.gravite >= 4) {
            if (rng.nextDouble() < 0.5) z.pont.radio("pirate", pirate(e, lieu));
            if (e.type.contains("labo") || e.type.contains("frappe") || e.type.contains("quarantaine") || e.type.contains("norda"))
                z.pont.radio("norda", "Information officielle : la situation à " + lieu + " est sous contrôle. Les rumeurs contraires sont dangereuses.");
            if (e.type.contains("horde") || e.type.contains("frappe") || e.type.contains("quarantaine"))
                z.pont.radio("bravo", "Bravo à tous les postes. Secteur " + lieu + ". Code ambre. Fin.");
        }
        if (e.type.startsWith("norda") || e.type.contains("labo")) veritesNorda++;
        // trop de vérités : NORDA menace, puis la fait taire
        if (veritesNorda == 6) z.pont.radio("lea", "... On m'a laissé un message, ce matin. Sous ma porte. Je continue quand même. Vous avez le droit de savoir.");
        if (veritesNorda >= 10 && !silence) {
            silence = true;
            silenceDepuis = z.jour();
            z.pont.zaevt("lea_silence");
            z.publier(new Evenement("lea_silence").a(0, 0).grav(5).dit("CKZA 98,5"));
        }
    }

    private String texte(Evenement e, String lieu) {
        switch (e.type) {
            case "horde_attaque_lieu":
                return "Une horde a frappé " + lieu + ". On ne sait pas encore combien sont restés.";
            case "horde_passe":
                return "Une grosse horde traverse le secteur de " + lieu + ". Restez à l'intérieur, éteignez les lumières.";
            case "megahorde":
                return "Tous les postes : " + e.texte + " est en mouvement. Une Mégahorde. Barricadez tout.";
            case "region_perdue":
                return "On a perdu le contact avec " + lieu + ". Plus de lumière, plus de radio. Rien.";
            case "region_reprise":
                return lieu + " est repris. Il y a de la lumière, là-bas. Je ne pensais plus dire ça.";
            case "nid_ne":
                return "Des survivants parlent d'un nid près de " + lieu + ". Évitez le coin la nuit.";
            case "matrice":
                return "Quelque chose grandit dans " + lieu + ". Les scientifiques appellent ça une matrice.";
            case "frappe_incendiaire":
                return "Ils ont brûlé " + lieu + ". Une frappe incendiaire. Avec qui dedans ?";
            case "quarantaine":
                return "Le secteur de " + lieu + " est en quarantaine. Barbelés, soldats. N'essayez pas de passer.";
            case "colonne_refugies":
                return "Une colonne de réfugiés est sur la route : " + e.texte + ". Si vous les croisez, aidez-les.";
            case "pillards_sur_colonne":
                return "Des pillards ont attaqué des réfugiés près de " + lieu + ". Des enfants, dans le lot.";
            case "labo_detruit":
                return "Une explosion à " + lieu + ". Un labo, paraît-il. Ne buvez pas l'eau en aval.";
            case "nemesis_nee":
                return "Un mort « armé » dans le secteur de " + lieu + ". Il porte un casque. Celui de quelqu'un qu'on connaissait.";
            case "nemesis_vaincue":
                return "Quelqu'un a abattu " + e.texte + ". Il y a encore des gens qui se battent, dehors.";
            case "legende_locale":
                return "On l'appelle " + e.texte + ". Il rôde depuis des jours. Ne l'approchez pas seuls.";
            case "mutation":
                return "Des morts différents, vers " + lieu + ". Ils " + mutation(e.texte) + ". Faites attention.";
            case "drone_abattu":
                return "Un drone est tombé près de " + lieu + ". Un drone. Qui a encore des drones ?";
            case "boss_tue":
                return "Le monstre de " + lieu + " est tombé. Le coin respire un peu mieux.";
            case "ville_tombee":
                return lieu + " est tombée. On s'en souviendra.";
            case "lieu_attaque":
            case "camp_attaque":
                return "Le camp de " + lieu + " est attaqué en ce moment. S'il y a quelqu'un dans le coin...";
            case "grande_nuit":
                return "Cette nuit, tout bouge en même temps. Je n'ai jamais vu ça. Restez ensemble.";
            case "signalement":
                return "Un auditeur nous écrit : « " + e.texte + " ». Je n'ai pas pu vérifier.";
            case "crash":
                return "Des gens ont vu de la fumée près de " + lieu + ". Un appareil, peut-être. Si vous y allez, vous ne serez pas seuls.";
            case "explosion":
                return "Une explosion entendue près de " + lieu + ". Quelqu'un, ou quelque chose ?";
            default:
                if (e.gravite >= 4 && !e.texte.isEmpty()) return "Des nouvelles de " + lieu + " : " + e.texte + ".";
                return null;
        }
    }

    private static String mutation(String trait) {
        switch (trait) {
            case "grimpeur":
                return "grimpent";
            case "carbonise":
                return "ne brûlent plus comme avant";
            case "blinde":
                return "encaissent les coups";
            case "sourd_aux_leurres":
                return "ignorent les leurres";
            case "evite_pieges":
                return "évitent les pièges";
            default:
                return "changent";
        }
    }

    private String pirate(Evenement e, String lieu) {
        String[] t = {"Encore " + lieu + " ! Et l'armée qui regarde ailleurs. Comme toujours.",
                "On vous dit que c'est sous contrôle, à " + lieu + " ? Rions ensemble. Puis courez.",
                "Radio Libre Saint-Aurèle : " + lieu + ", c'est ce qu'ils ne veulent pas que vous sachiez."};
        return t[rng.nextInt(t.length)];
    }

    /** une fois par jour : les corrections, l'anniversaire des chutes et des reprises (8) */
    void jour() {
        if (!erreurs.isEmpty() && !silence) {
            Evenement e = erreurs.remove(0);
            z.pont.radio("lea", "Une correction : hier, j'ai parlé du mauvais endroit. C'était " + z.nomLieu(e) + ". Je m'excuse. On fait de notre mieux.");
        }
        // anniversaires : trente jours plus tard
        synchronized (z.monde) {
            for (Region r : z.monde.graphe.regions.values()) {
                for (String p : r.plaques) {
                    if (!p.contains("Jour " + (z.jour() - 30))) continue;
                    if (!silence) z.pont.radio("lea", "Il y a trente jours : " + p + ". On n'oublie pas.");
                }
            }
        }
        // l'émetteur réparé rend sa voix à Léa (Skript : zam lea retour)
        if (silence && z.jour() - silenceDepuis > 7 && rng.nextDouble() < 0.1) {
            silence = false;
            veritesNorda = 4;
            z.pont.radio("lea", "... C'est moi. Je suis encore là. Ils ont cassé l'émetteur, pas ma voix.");
        }
    }

    public void retour() {
        silence = false;
        veritesNorda = 3;
        z.pont.radio("lea", "Merci. À ceux qui ont réparé l'émetteur : merci. On recommence.");
    }

    void sauver(ConfigurationSection s) {
        s.set("verites_norda", veritesNorda);
        s.set("silence", silence);
        s.set("silence_depuis", silenceDepuis);
    }

    void charger(ConfigurationSection s) {
        if (s == null) return;
        veritesNorda = s.getInt("verites_norda");
        silence = s.getBoolean("silence");
        silenceDepuis = s.getInt("silence_depuis", -1);
    }
}
