package za.moteur.coeur;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * La mémoire (bible F10, S-6). La Chronique garde la vérité ; ici, ce que chacun EN RETIENT.
 * - mémoire personnelle (PNJ, factions, camps, NORDA, joueurs) : souvenirs avec certitude, importance, interprétation ;
 * - mémoire des relations (PNJ ↔ joueur, faction ↔ joueur...) : confiance, gratitude, peur, ressentiment ET les raisons ;
 * - légendes et histoires détectées : plusieurs versions d'un même fait.
 * Règle 12 : entre deux joueurs, on garde des faits, jamais des sentiments (pas de relation joueur → joueur).
 */
public final class Memoire {
    public static final class Souvenir {
        public long evt;
        public String texte;
        public int certitude;
        public int importance;
        public int jour;
        public String interpretation = "";
        public int repetitions;
    }

    public static final class Relation {
        public double confiance, gratitude, peur, ressentiment;
        public final List<String> raisons = new ArrayList<>();

        public String niveau() {
            double c = confiance + gratitude / 2 - ressentiment / 2;
            if (c < 0) return "hostile";
            if (c <= 20) return "méfiance";
            if (c <= 40) return "connaissance";
            if (c <= 60) return "confiance faible";
            if (c <= 80) return "confiance";
            if (c <= 95) return "proche";
            return "loyal";
        }
    }

    public static final class Legende {
        public String nom;
        public long evt;
        public int jour;
        public final Map<String, String> versions = new LinkedHashMap<>();
        public int popularite = 1;
    }

    public final Map<String, List<Souvenir>> personnelle = new HashMap<>();
    public final Map<String, Relation> relations = new HashMap<>();
    public final List<Legende> legendes = new ArrayList<>();
    private final Map<String, List<long[]>> suites = new HashMap<>();   // acteur -> {evt, importance, jour}
    private final Random rng;
    public int maxSouvenirs = 60;
    /** une histoire ou une légende vient de naître : le plugin la donne à Skript (za_monde_legende) */
    public java.util.function.Consumer<String> annonce = s -> { };

    public Memoire(Random rng) {
        this.rng = rng;
    }

    /** effet d'un type d'événement sur la relation de la cible (ou du témoin) envers l'auteur */
    private static final Map<String, double[]> EFFETS = new HashMap<>();   // confiance, gratitude, peur, ressentiment
    private static final Map<String, String> INTERPRETATION = new HashMap<>();

    static {
        regle("survivant_sauve", 10, 20, 0, -10, "m'a sauvé");
        regle("soin", 6, 12, 0, -5, "m'a soigné");
        regle("escorte", 6, 8, 0, 0, "m'a escorté");
        regle("aide", 5, 8, 0, 0, "m'a aidé");
        regle("livraison", 5, 4, 0, 0, "a livré ce qu'il devait");
        regle("promesse_tenue", 8, 3, 0, -3, "a tenu parole");
        regle("commerce", 2, 0, 0, 0, "a fait affaire avec nous");
        regle("abandon", -15, -10, 0, 20, "m'a laissé derrière");
        regle("promesse_brisee", -15, 0, 0, 15, "a oublié sa promesse");
        regle("vol", -25, 0, 0, 25, "nous a volés");
        regle("trahison", -40, -20, 10, 40, "nous a trahis");
        regle("attaque", -20, 0, 20, 15, "nous a attaqués");
        regle("menace", -10, 0, 15, 8, "nous a menacés");
        regle("mensonge_demasque", -30, 0, 0, 10, "nous a menti");
        regle("refus_aide", -5, 0, 0, 5, "a refusé de nous aider");
    }

    private static void regle(String t, double c, double g, double p, double r, String interp) {
        EFFETS.put(t, new double[]{c, g, p, r});
        INTERPRETATION.put(t, interp);
    }

    private static boolean joueur(String cle) {
        return cle.length() == 36 || cle.startsWith("joueur:");
    }

    private static String cle(String acteur) {
        return acteur.length() == 36 ? "joueur:" + acteur : acteur;
    }

    public Relation relation(String de, String envers) {
        return relations.computeIfAbsent(de + "|" + envers, k -> new Relation());
    }

    /** tout événement avec des acteurs ou des témoins laisse des souvenirs et change des relations */
    public void sur(Evenement e, String texteLisible) {
        if (e.acteurs.isEmpty() && e.temoins.isEmpty()) return;
        String t = texteLisible == null || texteLisible.isEmpty() ? e.type + (e.texte.isEmpty() ? "" : " : " + e.texte) : texteLisible;
        String interp = INTERPRETATION.getOrDefault(e.type, "");
        for (String a : e.acteurs) noter(cle(a), e, t, 100, interp);
        for (String w : e.temoins) noter(cle(w), e, t, 80, interp);
        // relations : acteurs[0] = l'auteur, les autres acteurs et les témoins réagissent
        double[] ef = EFFETS.get(e.type);
        if (ef != null && e.acteurs.size() >= 1) {
            String auteur = cle(e.acteurs.get(0));
            List<String> concernes = new ArrayList<>();
            for (int k = 1; k < e.acteurs.size(); k++) concernes.add(cle(e.acteurs.get(k)));
            for (String w : e.temoins) concernes.add(cle(w));
            for (int k = 0; k < concernes.size(); k++) {
                String qui = concernes.get(k);
                if (joueur(qui) && joueur(auteur)) continue;   // règle 12
                if (qui.equals(auteur)) continue;
                double f = k < e.acteurs.size() - 1 ? 1.0 : 0.5;   // un témoin réagit moitié moins
                Relation r = relation(qui, auteur);
                r.confiance = borne(r.confiance + ef[0] * f, -100, 100);
                r.gratitude = borne(r.gratitude + ef[1] * f, 0, 100);
                r.peur = borne(r.peur + ef[2] * f, 0, 100);
                r.ressentiment = borne(r.ressentiment + ef[3] * f, 0, 100);
                r.raisons.add("J" + e.jour + " : " + INTERPRETATION.get(e.type) + (f < 1 ? " (vu)" : ""));
                while (r.raisons.size() > 12) r.raisons.remove(0);
            }
        }
        // légendes et histoires détectées (S-6)
        if (e.importance >= 80) legende(e, t);
        for (String a : e.acteurs) suite(cle(a), e, t);
    }

    private static double borne(double v, double a, double b) {
        return Math.max(a, Math.min(b, v));
    }

    private void noter(String qui, Evenement e, String t, int certitude, String interp) {
        List<Souvenir> l = personnelle.computeIfAbsent(qui, k -> new ArrayList<>());
        Souvenir s = new Souvenir();
        s.evt = e.id;
        s.texte = t;
        s.certitude = certitude;
        s.importance = e.importance;
        s.jour = e.jour;
        s.interpretation = interp;
        l.add(s);
        // les petites choses s'oublient, les grandes presque jamais
        while (l.size() > maxSouvenirs) {
            int pire = 0;
            for (int k = 1; k < l.size(); k++) if (l.get(k).importance < l.get(pire).importance) pire = k;
            l.remove(pire);
        }
    }

    private void legende(Evenement e, String t) {
        for (Legende l : legendes) if (l.evt == e.id) return;
        Legende l = new Legende();
        l.evt = e.id;
        l.jour = e.jour;
        l.nom = titre(e);
        l.versions.put("chronique", t);
        l.versions.put("lea", adoucir(t));
        l.versions.put("rumeur", grossir(t));
        legendes.add(l);
        annonce.accept(l.nom + " — " + l.versions.get("rumeur"));
    }

    private static String titre(Evenement e) {
        switch (e.type) {
            case "boss_tue":
                return "La chute de " + (e.texte.isEmpty() ? "la bête" : e.texte);
            case "ville_tombee":
                return "La nuit où " + (e.texte.isEmpty() ? "la ville" : e.texte) + " est tombée";
            case "labo_detruit":
                return "Le jour où le labo a sauté";
            case "barrage_cede":
                return "La nuit du barrage";
            case "region_reprise":
                return "La reconquête";
            default:
                return "Ce qui s'est passé au jour " + e.jour;
        }
    }

    /** une suite d'événements liés à un même acteur, avec une grosse conséquence : une histoire a un titre */
    private void suite(String acteur, Evenement e, String t) {
        if (e.importance < 15) return;
        List<long[]> l = suites.computeIfAbsent(acteur, k -> new ArrayList<>());
        l.add(new long[]{e.id, e.importance, e.jour});
        l.removeIf(x -> x[2] < e.jour - 2);
        long somme = 0;
        for (long[] x : l) somme += x[1];
        if (somme >= 150 && l.size() >= 3) {
            l.clear();
            annonce.accept("Une histoire circule : " + t);
        }
    }

    // ---------------------------------------------------------------- les souvenirs se déforment (F10)

    public String raconter(String qui, Souvenir s, int jour) {
        s.repetitions++;
        int age = jour - s.jour;
        if (s.repetitions > 3 || age > 10) return grossir(s.texte);
        return s.texte;
    }

    private String grossir(String t) {
        String r = t.replaceAll("\\b([2-9]|1[0-9])\\b", "une vingtaine de").replaceAll("\\b[2-9][0-9]\\b", "une centaine de")
                .replaceAll("\\b\\d{3,}\\b", "des milliers de");
        if (rng.nextDouble() < 0.5) r = r.replace("une horde", "une armée de morts").replace("Un mort", "Un monstre");
        return r;
    }

    private static String adoucir(String t) {
        return "On raconte que " + Character.toLowerCase(t.charAt(0)) + t.substring(1);
    }

    /** chaque jour : la certitude des vieux souvenirs baisse, les rancunes s'apaisent un peu, les gratitudes restent */
    public void jour(int jour) {
        for (List<Souvenir> l : personnelle.values())
            for (Souvenir s : l) if (jour - s.jour > 3 && s.importance < 60) s.certitude = Math.max(20, s.certitude - 2);
        for (Relation r : relations.values()) {
            r.peur *= 0.95;
            r.ressentiment *= 0.98;
        }
    }

    public List<Souvenir> souvenirs(String qui) {
        List<Souvenir> l = personnelle.get(qui);
        return l == null ? new ArrayList<>() : new ArrayList<>(l);
    }

    // ---------------------------------------------------------------- sauvegarde

    public List<String> exporter() {
        List<String> o = new ArrayList<>();
        for (Map.Entry<String, List<Souvenir>> e : personnelle.entrySet())
            for (Souvenir s : e.getValue())
                o.add("S\t" + e.getKey() + "\t" + s.evt + "\t" + s.texte.replace('\t', ' ') + "\t" + s.certitude + "\t" + s.importance + "\t" + s.jour + "\t" + s.interpretation + "\t" + s.repetitions);
        for (Map.Entry<String, Relation> e : relations.entrySet()) {
            Relation r = e.getValue();
            o.add("R\t" + e.getKey() + "\t" + (int) r.confiance + "\t" + (int) r.gratitude + "\t" + (int) r.peur + "\t" + (int) r.ressentiment + "\t" + String.join("¦", r.raisons));
        }
        for (Legende l : legendes) {
            StringBuilder b = new StringBuilder("L\t" + l.nom + "\t" + l.evt + "\t" + l.jour + "\t" + l.popularite);
            for (Map.Entry<String, String> v : l.versions.entrySet()) b.append('\t').append(v.getKey()).append('=').append(v.getValue().replace('\t', ' '));
            o.add(b.toString());
        }
        return o;
    }

    public void importer(List<String> l) {
        for (String s : l) {
            String[] c = s.split("\t", -1);
            try {
                if (c[0].equals("S") && c.length >= 9) {
                    Souvenir v = new Souvenir();
                    v.evt = Long.parseLong(c[2]);
                    v.texte = c[3];
                    v.certitude = Integer.parseInt(c[4]);
                    v.importance = Integer.parseInt(c[5]);
                    v.jour = Integer.parseInt(c[6]);
                    v.interpretation = c[7];
                    v.repetitions = Integer.parseInt(c[8]);
                    personnelle.computeIfAbsent(c[1], k -> new ArrayList<>()).add(v);
                } else if (c[0].equals("R") && c.length >= 7) {
                    Relation r = new Relation();
                    r.confiance = Double.parseDouble(c[2]);
                    r.gratitude = Double.parseDouble(c[3]);
                    r.peur = Double.parseDouble(c[4]);
                    r.ressentiment = Double.parseDouble(c[5]);
                    if (!c[6].isEmpty()) for (String x : c[6].split("¦")) r.raisons.add(x);
                    relations.put(c[1], r);
                } else if (c[0].equals("L") && c.length >= 5) {
                    Legende g = new Legende();
                    g.nom = c[1];
                    g.evt = Long.parseLong(c[2]);
                    g.jour = Integer.parseInt(c[3]);
                    g.popularite = Integer.parseInt(c[4]);
                    for (int k = 5; k < c.length; k++) {
                        int i = c[k].indexOf('=');
                        if (i > 0) g.versions.put(c[k].substring(0, i), c[k].substring(i + 1));
                    }
                    legendes.add(g);
                }
            } catch (RuntimeException ignored) {
                // ligne abîmée
            }
        }
    }
}
