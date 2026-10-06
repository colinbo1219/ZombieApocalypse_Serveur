package za.moteur.coeur;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Le moteur d'information (bible F9). Une information = contenu + source + lieu + moment + fiabilité + fraîcheur.
 * La Chronique garde la vérité ; ici vivent les VERSIONS qui circulent : elles voyagent de région en région par des
 * canaux réels (témoins, camps, relais radio, marchands), vieillissent, se déforment, arrivent parfois en morceaux.
 * Chaque détenteur (« joueur:uuid », « region:id », « camp:id », « faction:nom », « norda », « pnj:id ») a son savoir.
 */
public final class Information {
    public static final class Info {
        public long id;
        public long evt;              // l'événement de la Chronique (0 = aucun : rumeur inventée, propagande)
        public String sujet = "";     // horde, route, prix, norda, lieu, personne...
        public String texte = "";     // la version d'origine
        public String region;
        public double x, z;
        /** vraie | fausse | erreur | incomplete | propagande | tromperie */
        public String nature = "vraie";
        public String source = "temoin";
        public int fiabilite = 70;
        public long cree = System.currentTimeMillis();
        public int jour;
        public int importance;
    }

    /** ce qu'un détenteur sait d'une information : SA version */
    public static final class Connue {
        public Info info;
        public String texte;
        public int fiabilite;
        public long recue;
        public String canal;
        public int morceaux = 3;      // sur 3 : moins = fragments (« … bunker … nord … »)
        public int sauts;             // nombre de bouches par lesquelles elle est passée
    }

    public final Map<Long, Info> infos = new LinkedHashMap<>();
    public final Map<String, Map<Long, Connue>> savoirs = new HashMap<>();
    private long suivant = 1;
    private final Random rng;
    public int maxInfos = 2500, maxParDetenteur = 80;
    public java.util.function.LongSupplier horloge = System::currentTimeMillis;

    public Information(Random rng) {
        this.rng = rng;
    }

    // ---------------------------------------------------------------- naissance

    /** chaque événement assez important devient une information là où il s'est passé (témoins, région, camps) */
    public Info depuisEvenement(Evenement e, Graphe g) {
        if (e.importance < 8 || e.region == null) return null;
        if (e.visibilite.equals("secret")) return null;
        String t = phrase(e, g);
        if (t == null) return null;
        Info i = nouvelle(e.type, t, e.region, e.x, e.z, e.jour);
        i.evt = e.id;
        i.importance = e.importance;
        i.nature = e.verite.equals("faux") ? "fausse" : "vraie";
        i.source = sourceDe(e);
        i.fiabilite = Math.min(e.fiabilite, i.nature.equals("vraie") ? 75 : 45);
        apprendre("region:" + e.region, i, t, i.fiabilite, "temoin", 0);
        for (String a : e.acteurs) apprendre(cle(a), i, t, 95, "vecu", 0);
        for (String a : e.temoins) apprendre(cle(a), i, t, 85, "temoin", 0);
        return i;
    }

    private static String cle(String acteur) {
        return acteur.length() == 36 ? "joueur:" + acteur : acteur;
    }

    private static String sourceDe(Evenement e) {
        switch (e.source) {
            case "joueur":
                return "joueur";
            case "drone":
                return "drone";
            case "norda":
                return "fuite";
            case "radio":
                return "radio";
            default:
                return "temoin";
        }
    }

    public Info nouvelle(String sujet, String texte, String region, double x, double z, int jour) {
        Info i = new Info();
        i.id = suivant++;
        i.sujet = sujet;
        i.texte = texte;
        i.region = region;
        i.x = x;
        i.z = z;
        i.jour = jour;
        i.cree = horloge.getAsLong();
        infos.put(i.id, i);
        while (infos.size() > maxInfos) {
            Long k = infos.keySet().iterator().next();
            infos.remove(k);
            for (Map<Long, Connue> m : savoirs.values()) m.remove(k);
        }
        return i;
    }

    /** un détenteur apprend (ou réapprend par un autre canal : les morceaux se recollent) */
    public Connue apprendre(String qui, Info i, String texte, int fiab, String canal, int sauts) {
        Map<Long, Connue> m = savoirs.computeIfAbsent(qui, k -> new LinkedHashMap<>());
        Connue c = m.get(i.id);
        if (c != null) {
            if (!canal.equals(c.canal)) c.morceaux = Math.min(3, c.morceaux + 1);
            // une source plus fiable ou plus fraîche remplace la version connue
            if (fiab > c.fiabilite) {
                c.fiabilite = fiab;
                c.texte = texte;
                c.canal = canal;
                c.sauts = Math.min(c.sauts, sauts);
            }
            return c;
        }
        c = new Connue();
        c.info = i;
        c.texte = texte;
        c.fiabilite = Math.max(5, Math.min(99, fiab));
        c.recue = horloge.getAsLong();
        c.canal = canal;
        c.sauts = sauts;
        // par la radio brouillée ou de loin, ça arrive parfois en morceaux
        if (sauts >= 2 && rng.nextDouble() < 0.25) c.morceaux = 1 + rng.nextInt(2);
        m.put(i.id, c);
        while (m.size() > maxParDetenteur) m.remove(m.keySet().iterator().next());
        return c;
    }

    public boolean sait(String qui, long info) {
        Map<Long, Connue> m = savoirs.get(qui);
        return m != null && m.containsKey(info);
    }

    public List<Connue> savoir(String qui) {
        Map<Long, Connue> m = savoirs.get(qui);
        List<Connue> l = m == null ? new ArrayList<>() : new ArrayList<>(m.values());
        l.sort((a, b) -> Long.compare(b.info.cree, a.info.cree));
        return l;
    }

    // ---------------------------------------------------------------- voyage (toutes les 5 minutes)

    /**
     * Les informations des régions passent aux régions voisines. Les relais radio réparés (106) et les tours accélèrent ;
     * chaque passage peut perdre de la précision. Les vieilles infos sans importance cessent de voyager.
     */
    public void voyager(Graphe g, long maintenant) {
        List<String[]> envois = new ArrayList<>();
        for (Map.Entry<String, Map<Long, Connue>> d : savoirs.entrySet()) {
            if (!d.getKey().startsWith("region:")) continue;
            String rid = d.getKey().substring(7);
            Region r = g.regions.get(rid);
            if (r == null) continue;
            double p = 0.18 + 0.12 * Math.min(3, r.repeteurs) + 0.05 * Math.min(3, r.tours) + (r.population > 30 ? 0.08 : 0);
            for (Connue c : d.getValue().values()) {
                double ageH = (maintenant - c.info.cree) / 3_600_000.0;
                if (ageH > 6 + c.info.importance / 5.0) continue;
                if (c.sauts >= 1 + c.info.importance / 20) continue;
                if (rng.nextDouble() > p) continue;
                for (Region v : g.voisins(rid)) {
                    if (sait("region:" + v.id, c.info.id)) continue;
                    String canal = r.repeteurs > 0 ? "radio" : "rumeur";
                    envois.add(new String[]{v.id, String.valueOf(c.info.id), canal, String.valueOf(c.sauts + 1), String.valueOf(c.fiabilite), c.texte});
                }
            }
        }
        for (String[] e : envois) {
            Info i = infos.get(Long.parseLong(e[1]));
            if (i == null) continue;
            int sauts = Integer.parseInt(e[3]);
            int fiab = Integer.parseInt(e[4]) - (e[2].equals("radio") ? 4 : 9);
            String t = e[2].equals("radio") && rng.nextDouble() < 0.6 ? e[5] : degrader(e[5]);
            apprendre("region:" + e[0], i, t, fiab, e[2], sauts);
        }
    }

    /** « 46 morts sur la 40, près du barrage » → « une grosse horde quelque part par là » */
    public String degrader(String t) {
        String r = t;
        if (rng.nextDouble() < 0.5) r = r.replaceAll("\\b\\d{3,}\\b", "des centaines de").replaceAll("\\b\\d{2}\\b", "des dizaines de");
        if (rng.nextDouble() < 0.3) r = r.replace("une horde", "une énorme horde").replace("quelques", "beaucoup de");
        if (rng.nextDouble() < 0.25) r = r.replaceAll("(près|autour) (de|du|des) [^,.]+", "quelque part dans le coin");
        return r;
    }

    /** le texte tel que le détenteur le perçoit : en morceaux s'il n'a pas tout recoupé */
    public String vu(Connue c) {
        if (c.morceaux >= 3) return c.texte;
        String[] mots = c.texte.split(" ");
        StringBuilder b = new StringBuilder("… ");
        int garde = c.morceaux == 2 ? 3 : 4;
        for (int k = 0; k < mots.length; k++) {
            if ((k + c.info.id) % garde == 0 || mots[k].length() < 4) continue;
            if ((k + c.info.id) % 2 == 0) b.append(mots[k]).append(" … ");
        }
        return b.toString().trim();
    }

    public static String age(long ms) {
        long m = ms / 60_000;
        if (m < 1) return "à l'instant";
        if (m < 60) return "il y a " + m + " min";
        long h = m / 60;
        if (h < 24) return "il y a " + h + " h";
        return "il y a " + (h / 24) + " j";
    }

    /** la fiabilité baisse avec l'âge, selon le sujet : une route sûre ne vaut plus rien six heures plus tard */
    public static int fiabiliteActuelle(Connue c, long maintenant) {
        double h = (maintenant - c.info.cree) / 3_600_000.0;
        double vitesse = c.info.sujet.contains("horde") || c.info.sujet.contains("route") || c.info.sujet.contains("tir") ? 12 : 3;
        return (int) Math.max(3, c.fiabilite - h * vitesse);
    }

    // ---------------------------------------------------------------- phrases

    private static String phrase(Evenement e, Graphe g) {
        Graphe.Lieu l = g.lieuProche(e.x, e.z, 400);
        Region r = g.regions.get(e.region);
        String ou = l != null ? "près de " + l.nom : r != null ? "du côté de " + r.nom : "quelque part";
        String quoi = e.texte == null ? "" : e.texte;
        switch (e.type) {
            case "horde_attaque_lieu":
                return "Une horde a attaqué " + ou + ".";
            case "horde_passe":
            case "megahorde":
                return "Une grosse horde se déplace " + ou + ".";
            case "nid_ne":
                return "Un nid s'est formé " + ou + ".";
            case "nid_detruit":
                return "Le nid " + ou + " a été détruit.";
            case "labo_detruit":
                return "Un labo a sauté " + ou + ". L'eau en aval n'est plus sûre.";
            case "region_perdue":
                return "On a perdu " + (r != null ? r.nom : "le secteur") + ".";
            case "region_reprise":
                return (r != null ? r.nom : "Le secteur") + " a été repris.";
            case "quarantaine":
                return "L'armée a bouclé le secteur " + ou + ".";
            case "frappe_incendiaire":
                return "Une frappe incendiaire " + ou + ".";
            case "nemesis_nee":
                return "Un mort armé, avec un casque, rôde " + ou + (quoi.isEmpty() ? "." : ". On l'appelle " + quoi + ".");
            case "nemesis_vaincue":
                return quoi + " a été abattu " + ou + ".";
            case "boss_tue":
                return (quoi.isEmpty() ? "Le monstre" : quoi) + " est tombé " + ou + ".";
            case "colonne_refugies":
                return "Une colonne de réfugiés est sur la route " + ou + ".";
            case "crash":
                return "Un hélicoptère s'est écrasé " + ou + ".";
            case "drone_abattu":
                return "Quelqu'un a abattu un drone NORDA " + ou + ".";
            case "norda_barrage":
                return "NORDA contrôle la route " + ou + ".";
            case "courant_retabli":
                return "Le courant est revenu " + ou + ".";
            case "courant_coupe":
                return "Blackout " + ou + ".";
            case "explosion":
                return "Une explosion " + ou + ".";
            case "mort_joueur":
                return "Quelqu'un est mort " + ou + ".";
            case "signalement":
                return quoi;
            case "vol":
            case "promesse_tenue":
            case "conflit_camp":
            case "depart_survivant":
                return quoi.isEmpty() ? null : quoi + " (" + ou + ").";
            case "faction_blocus":
            case "traite_signe":
            case "faction_raid":
            case "convoi_detruit":
            case "convoi_parti":
                return quoi;
            default:
                if (e.type.startsWith("monde_") && !quoi.isEmpty()) return quoi;
                if (e.gravite >= 3 && !quoi.isEmpty()) return quoi + " (" + ou + ")";
                return null;
        }
    }

    // ---------------------------------------------------------------- sauvegarde (lignes texte)

    public List<String> exporter() {
        List<String> l = new ArrayList<>();
        l.add("suivant\t" + suivant);
        for (Info i : infos.values())
            l.add("I\t" + i.id + "\t" + i.evt + "\t" + i.sujet + "\t" + i.texte.replace('\t', ' ') + "\t" + (i.region == null ? "" : i.region)
                    + "\t" + (int) i.x + "\t" + (int) i.z + "\t" + i.nature + "\t" + i.source + "\t" + i.fiabilite + "\t" + i.cree + "\t" + i.jour + "\t" + i.importance);
        for (Map.Entry<String, Map<Long, Connue>> d : savoirs.entrySet()) {
            for (Connue c : d.getValue().values())
                l.add("C\t" + d.getKey() + "\t" + c.info.id + "\t" + c.texte.replace('\t', ' ') + "\t" + c.fiabilite + "\t" + c.recue + "\t" + c.canal + "\t" + c.morceaux + "\t" + c.sauts);
        }
        return l;
    }

    public void importer(List<String> l) {
        for (String s : l) {
            String[] c = s.split("\t", -1);
            try {
                if (c[0].equals("suivant")) suivant = Long.parseLong(c[1]);
                else if (c[0].equals("I") && c.length >= 14) {
                    Info i = new Info();
                    i.id = Long.parseLong(c[1]);
                    i.evt = Long.parseLong(c[2]);
                    i.sujet = c[3];
                    i.texte = c[4];
                    i.region = c[5].isEmpty() ? null : c[5];
                    i.x = Double.parseDouble(c[6]);
                    i.z = Double.parseDouble(c[7]);
                    i.nature = c[8];
                    i.source = c[9];
                    i.fiabilite = Integer.parseInt(c[10]);
                    i.cree = Long.parseLong(c[11]);
                    i.jour = Integer.parseInt(c[12]);
                    i.importance = Integer.parseInt(c[13]);
                    infos.put(i.id, i);
                    suivant = Math.max(suivant, i.id + 1);
                } else if (c[0].equals("C") && c.length >= 9) {
                    Info i = infos.get(Long.parseLong(c[2]));
                    if (i == null) continue;
                    Connue k = apprendre(c[1], i, c[3], Integer.parseInt(c[4]), c[6], Integer.parseInt(c[8]));
                    k.recue = Long.parseLong(c[5]);
                    k.morceaux = Integer.parseInt(c[7]);
                }
            } catch (RuntimeException ignored) {
                // ligne abîmée
            }
        }
    }

    /** nettoyage : les infos très vieilles et sans importance sont oubliées partout */
    public void oublier(long maintenant) {
        Iterator<Map.Entry<Long, Info>> it = infos.entrySet().iterator();
        while (it.hasNext()) {
            Info i = it.next().getValue();
            double jours = (maintenant - i.cree) / 86_400_000.0;
            if (jours > 2 + i.importance / 4.0) {
                it.remove();
                for (Map<Long, Connue> m : savoirs.values()) m.remove(i.id);
            }
        }
    }
}
