package za.moteur.coeur;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Les bases vivantes (bible IA-15) et le cerveau des survivants (IA-8).
 * Une base regarde ses besoins (« le bois est à 12, le minimum souhaité est 30 »), crée le travail, et choisit QUI le
 * fait par un score (compétence, fatigue, nuit, aversions, moral, contamination, courage). Le survivant peut remettre
 * à plus tard (« J'irai demain matin »). Joueur absent : mode prudent (règle 2) — production modeste, jamais de mort.
 * Les corps, les sacs et les vraies sorties restent dans Skript (za_p43, za_p92) : ce cerveau donne les ordres.
 */
public final class Bases {
    public static final String[] RESSOURCES = {"nourriture", "bois", "materiaux", "medicaments", "carburant"};
    /** la tâche de za_p92 qui remplit chaque ressource */
    public static final Map<String, String> TACHE = new HashMap<>();

    static {
        TACHE.put("nourriture", "nourriture");
        TACHE.put("bois", "bois");
        TACHE.put("materiaux", "materiaux");
        TACHE.put("medicaments", "plantes");
        TACHE.put("carburant", "minerais");
    }

    public static final class Survivant {
        public int id;
        public String nom = "", metier = "", base = "", etat = "base", role = "", trait = "", aversion = "";
        public boolean enMission, blesse;
        public double fatigue, sante = 100, moral = 50;
        // personnalité 0-100 (IA-8) : elle change avec les événements
        public double courage = 50, honnetete = 60, loyaute = 50, avidite = 30, empathie = 50, paranoia = 30, sociabilite = 50;
        public final Map<String, Double> competences = new LinkedHashMap<>();   // recolte, combat, medical, meca : 0-100
        public final Map<String, Integer> xp = new HashMap<>();
        public final List<String> journal = new ArrayList<>();
        public String intention = "";        // « bois@matin » : ce qu'il a décidé de faire plus tard
        public int intentionJour = -1;
        public int infecteDepuis = -1;      // jour où l'infection cachée a été notée (110)
        public int missions, reussites;
        public String derniereMission = "";
        public long vu;                      // dernière mise à jour par Skript
        /** secret (IA-8, IA-9) : informateur (NORDA), voleur, ancien_pillard, agent_double ; "" = aucun */
        public String secret = "";
        boolean personnaliteFaite;

        public double comp(String k) {
            return competences.getOrDefault(k, 30.0);
        }
    }

    public static final class Base {
        public String proprio;               // uuid
        public String nom = "";
        public double x, z;
        public final Map<String, Integer> stocks = new LinkedHashMap<>();
        public final Map<String, Integer> minimums = new LinkedHashMap<>();
        public final Map<String, Integer> hier = new LinkedHashMap<>();
        public final List<String> bilan = new ArrayList<>();
        public final List<String> absence = new ArrayList<>();
        public final List<String> historique = new ArrayList<>();
        public boolean sortiesInterdites, courant;
        public String etat = "fondation";
        public double moral = 60, securite = 50;
        public int stocksJour = -1, tension;   // jours de pénurie d'affilée
        public long derniereSortie;

        public int stock(String r) {
            return stocks.getOrDefault(r, 0);
        }

        public int min(String r) {
            Integer m = minimums.get(r);
            if (m != null) return m;
            switch (r) {
                case "nourriture":
                    return 30;
                case "bois":
                    return 32;
                case "materiaux":
                    return 20;
                case "medicaments":
                    return 4;
                default:
                    return 16;
            }
        }
    }

    /** un ordre pour le plugin (qui le passe à Skript) */
    public static final class Ordre {
        public final String type, base, texte;
        public final int survivant;
        public final String tache;
        public final int quantite;

        Ordre(String type, String base, int survivant, String tache, int quantite, String texte) {
            this.type = type;
            this.base = base;
            this.survivant = survivant;
            this.tache = tache;
            this.quantite = quantite;
            this.texte = texte;
        }
    }

    public final Map<String, Base> bases = new LinkedHashMap<>();
    public final Map<Integer, Survivant> survivants = new LinkedHashMap<>();
    private final Random rng;

    public Bases(Random rng) {
        this.rng = rng;
    }

    public Base base(String proprio) {
        return bases.computeIfAbsent(proprio, k -> {
            Base b = new Base();
            b.proprio = k;
            return b;
        });
    }

    public Survivant survivant(int id) {
        return survivants.computeIfAbsent(id, k -> {
            Survivant s = new Survivant();
            s.id = k;
            return s;
        });
    }

    /** la personnalité de départ découle du trait de za_p92, puis d'un peu de hasard stable */
    public void personnalite(Survivant s) {
        if (s.personnaliteFaite) return;
        s.personnaliteFaite = true;
        Random r = new Random(s.id * 7919L);
        s.courage = 35 + r.nextInt(31);
        s.honnetete = 40 + r.nextInt(50);
        s.loyaute = 35 + r.nextInt(40);
        s.avidite = 10 + r.nextInt(50);
        s.empathie = 30 + r.nextInt(55);
        s.paranoia = 10 + r.nextInt(50);
        s.sociabilite = 30 + r.nextInt(55);
        switch (s.trait) {
            case "prudent":
                s.courage = 25 + r.nextInt(15);
                break;
            case "tete_brulee":
                s.courage = 80 + r.nextInt(15);
                break;
            case "loyal":
                s.loyaute = 85 + r.nextInt(12);
                break;
            case "bavard":
                s.sociabilite = 80 + r.nextInt(15);
                break;
            case "volontaire":
                s.courage = 60 + r.nextInt(15);
                break;
            default:
                break;
        }
        // un secret, parfois : il décidera de mentir pour le protéger (IA-9)
        double t = r.nextDouble();
        if (t < 0.05) s.secret = "infecte_cache";
        else if (t < 0.10 && s.honnetete < 55) s.secret = "informateur";
        else if (t < 0.13 && s.avidite > 35) s.secret = "voleur";
        else if (t < 0.22) s.secret = "ancien_pillard";
    }

    // ================================================================ la décision (IA-8) : un score, des raisons

    /** le score d'un survivant pour une tâche, avec le détail (affiché par /zaadmin base) */
    public double score(Survivant s, Base b, String ressource, boolean nuit, double contamination, List<String> raisons) {
        double sc = 0;
        double manque = Math.max(0, b.min(ressource) - b.stock(ressource)) / (double) Math.max(1, b.min(ressource));
        double besoin = Math.min(45, manque * 50);
        sc += besoin;
        raisons.add("besoin de " + ressource + " +" + (int) besoin);
        String k = ressource.equals("medicaments") ? "medical" : ressource.equals("carburant") || ressource.equals("materiaux") ? "meca" : "recolte";
        double comp = s.comp(k) * 0.4;
        sc += comp;
        raisons.add("compétence +" + (int) comp);
        double fat = -s.fatigue / 3;
        sc += fat;
        if (fat < -5) raisons.add("fatigue " + (int) fat);
        if (nuit) {
            double n = s.aversion.equals("nuit") ? -35 : -20;
            sc += n;
            raisons.add("la nuit " + (int) n);
        }
        if ((s.aversion.equals("foret") && ressource.equals("bois")) || (s.aversion.equals("ville") && ressource.equals("materiaux"))
                || (s.aversion.equals("souterrains") && ressource.equals("carburant"))) {
            sc -= 15;
            raisons.add("il n'aime pas y aller -15");
        }
        if (s.moral < 30) {
            sc -= 10;
            raisons.add("moral bas -10");
        }
        if (contamination > 60 && s.courage < 70) {
            sc -= 15;
            raisons.add("région rouge -15");
        }
        double cou = (s.courage - 50) / 5;
        sc += cou;
        if (s.derniereMission.startsWith("reussie")) {
            sc += 5;
            raisons.add("sa dernière sortie s'est bien passée +5");
        } else if (s.derniereMission.startsWith("ratee")) {
            sc -= 8;
            raisons.add("sa dernière sortie a mal tourné -8");
        }
        return sc;
    }

    /**
     * Toutes les 5 minutes : chaque base regarde ses besoins et décide. proprioEnLigne : les vraies sorties n'ont lieu
     * que si le joueur est là (règle 2) ; sinon, petite production prudente et rapport d'absence.
     */
    public List<Ordre> decider(int jour, boolean nuit, boolean matin, java.util.function.Predicate<String> proprioEnLigne,
                               java.util.function.ToDoubleFunction<Base> contamination, long maintenant) {
        List<Ordre> o = new ArrayList<>();
        for (Base b : bases.values()) {
            List<Survivant> dispo = new ArrayList<>();
            for (Survivant s : survivants.values()) {
                if (!b.proprio.equals(s.base) || !s.etat.equals("base") || s.enMission || s.blesse) continue;
                if (s.metier.equals("enfant")) continue;
                personnalite(s);
                dispo.add(s);
            }
            if (dispo.isEmpty() || b.sortiesInterdites) continue;
            if (maintenant - b.derniereSortie < 8 * 60_000L) continue;   // une sortie à la fois, pas de ruée
            boolean enLigne = proprioEnLigne.test(b.proprio);
            double cont = contamination.applyAsDouble(b);
            // la ressource la plus en manque
            String res = null;
            double pire = 0;
            for (String r : RESSOURCES) {
                double m = (b.min(r) - b.stock(r)) / (double) Math.max(1, b.min(r));
                if (m > pire) {
                    pire = m;
                    res = r;
                }
            }
            // les intentions de la veille d'abord (« demain matin »)
            for (Survivant s : dispo) {
                if (s.intention.isEmpty() || !matin || s.intentionJour >= jour) continue;
                String r = s.intention;
                s.intention = "";
                o.add(ordreSortie(s, b, r, enLigne, jour, "Comme promis hier, " + s.nom + " part chercher du " + r + "."));
                b.derniereSortie = maintenant;
                res = null;
                break;
            }
            if (res == null || pire <= 0.05) continue;
            Survivant meilleur = null;
            double ms = -999;
            List<String> rs = null;
            for (Survivant s : dispo) {
                List<String> r = new ArrayList<>();
                double sc = score(s, b, res, nuit, cont, r);
                if (sc > ms) {
                    ms = sc;
                    meilleur = s;
                    rs = r;
                }
            }
            if (meilleur == null) continue;
            if (ms >= 40) {
                o.add(ordreSortie(meilleur, b, res, enLigne, jour, meilleur.nom + " décide d'aller chercher du " + res + " (" + String.join(", ", rs) + ")."));
                b.derniereSortie = maintenant;
            } else if (ms >= 15 && meilleur.intention.isEmpty() && (nuit || meilleur.fatigue > 50)) {
                meilleur.intention = res;
                meilleur.intentionJour = jour;
                String t = meilleur.nom + " : « J'irai demain matin, pas maintenant. » (" + String.join(", ", rs) + ")";
                o.add(new Ordre("journal", b.proprio, meilleur.id, res, 0, t));
                if (!enLigne) b.absence.add(t);
            }
        }
        return o;
    }

    private Ordre ordreSortie(Survivant s, Base b, String res, boolean enLigne, int jour, String texte) {
        b.historique.add("J" + jour + " : " + texte);
        while (b.historique.size() > 40) b.historique.remove(0);
        if (enLigne) return new Ordre("sortie", b.proprio, s.id, TACHE.get(res), 0, texte);
        // hors ligne : sortie courte et prudente, production modeste, au pire une blessure (règle 2)
        double k = 0.25 + s.comp(res.equals("medicaments") ? "medical" : "recolte") / 200.0;
        int q = Math.max(1, (int) Math.round(objectif(res) * k));
        s.fatigue = Math.min(100, s.fatigue + 15);
        String fin;
        if (rng.nextDouble() < 0.05) {
            s.blesse = true;
            q = q / 2;
            fin = s.nom + " est revenu blessé, avec " + q + " " + unite(res) + ".";
        } else fin = s.nom + " a rapporté " + q + " " + unite(res) + ".";
        b.absence.add(fin);
        xp(s, res);
        return new Ordre("prudent", b.proprio, s.id, res, q, fin);
    }

    static int objectif(String r) {
        switch (r) {
            case "bois":
                return 32;
            case "nourriture":
                return 16;
            case "materiaux":
                return 20;
            case "medicaments":
                return 6;
            default:
                return 16;
        }
    }

    static String unite(String r) {
        switch (r) {
            case "bois":
                return "bûches";
            case "nourriture":
                return "rations";
            case "materiaux":
                return "matériaux";
            case "medicaments":
                return "plantes médicinales";
            default:
                return "morceaux de charbon";
        }
    }

    /** l'expérience au poste (IA-8) : un vieux bûcheron produit plus qu'un nouveau */
    public boolean xp(Survivant s, String res) {
        String k = res.equals("medicaments") ? "medical" : res.equals("carburant") || res.equals("materiaux") ? "meca" : "recolte";
        int n = s.xp.merge(k, 1, Integer::sum);
        if (n % 4 == 0) {
            s.competences.put(k, Math.min(100, s.comp(k) + 3));
            return true;
        }
        return false;
    }

    /** le résultat d'une vraie sortie (za_p92) : mémoire de mission, personnalité qui bouge (IA-8) */
    public String resultat(Survivant s, String tache, String issue, int n, int jour) {
        s.missions++;
        String res = "bois";
        for (Map.Entry<String, String> e : TACHE.entrySet()) if (e.getValue().equals(tache)) res = e.getKey();
        String ligne;
        if (issue.equals("ok") || issue.equals("rentre")) {
            s.reussites++;
            s.derniereMission = "reussie";
            s.courage = Math.min(100, s.courage + 1);
            xp(s, res);
            ligne = "Mission " + s.missions + " : " + tache + ", " + n + " " + unite(res) + ", expérience +1.";
        } else if (issue.equals("blesse")) {
            s.derniereMission = "ratee";
            s.courage = Math.max(0, s.courage - 4);
            s.moral = Math.max(0, s.moral - 8);
            ligne = "Mission " + s.missions + " : " + tache + ", revenu blessé.";
        } else {
            s.derniereMission = "ratee";
            s.courage = Math.max(0, s.courage - 2);
            ligne = "Mission " + s.missions + " : " + tache + ", " + issue + ".";
        }
        s.journal.add("J" + jour + " : " + ligne);
        while (s.journal.size() > 30) s.journal.remove(0);
        return ligne;
    }

    // ================================================================ chaque jour : bilan, états, pénurie, conflits (90)

    public List<Ordre> jour(int jour, java.util.function.Predicate<String> proprioEnLigne) {
        List<Ordre> o = new ArrayList<>();
        for (Base b : bases.values()) {
            int pop = 0;
            List<Survivant> gens = new ArrayList<>();
            for (Survivant s : survivants.values()) {
                if (!b.proprio.equals(s.base) || s.etat.equals("mort")) continue;
                pop++;
                gens.add(s);
                s.fatigue = Math.max(0, s.fatigue - 30);   // une nuit de repos
                if (s.blesse && rng.nextDouble() < 0.35) s.blesse = false;
            }
            // bilan : variation des stocks depuis hier
            b.bilan.clear();
            StringBuilder t = new StringBuilder();
            for (String r : RESSOURCES) {
                int d = b.stock(r) - b.hier.getOrDefault(r, b.stock(r));
                if (d != 0) t.append(d > 0 ? "+" : "").append(d).append(' ').append(r).append(", ");
                b.hier.put(r, b.stock(r));
            }
            int joursNourriture = pop == 0 ? 99 : b.stock("nourriture") / Math.max(1, pop * 2);
            b.bilan.add((t.length() == 0 ? "stocks stables" : t.substring(0, t.length() - 2)) + " ; la nourriture tient encore " + joursNourriture + " jour(s).");
            // état de la base
            String avant = b.etat;
            if (pop <= 1) b.etat = "fondation";
            else if (joursNourriture < 1 || b.moral < 20) b.etat = "critique";
            else if (joursNourriture < 3 || b.securite < 25) b.etat = "sous_tension";
            else b.etat = "stable";
            if (!b.etat.equals(avant)) b.historique.add("J" + jour + " : la base passe « " + b.etat + " ».");
            boolean enLigne = proprioEnLigne.test(b.proprio);
            if (!enLigne) b.absence.add("Bilan du jour " + jour + " : " + b.bilan.get(0));
            // pénurie (IA-15) : rationnement, puis moral, puis disputes ; départs seulement si le joueur est là
            boolean penurie = b.stock("nourriture") < b.min("nourriture") * 0.2 && pop >= 2;
            if (penurie) {
                b.tension++;
                b.moral = Math.max(0, b.moral - 6);
                o.add(new Ordre("avis", b.proprio, 0, "", 0, "Le cuisinier rationne : la nourriture est sous 20 %. Le moral baisse."));
                if (b.tension >= 2 && gens.size() >= 3 && enLigne) {
                    Survivant a = null, c = null;
                    for (Survivant s : gens) if (a == null || s.avidite + s.paranoia > a.avidite + a.paranoia) a = s;
                    for (Survivant s : gens) if (s != a && (c == null || s.empathie < c.empathie)) c = s;
                    if (a != null && c != null) {
                        o.add(new Ordre("conflit", b.proprio, a.id, String.valueOf(c.id), 0,
                                a.nom + " et " + c.nom + " se disputent les rations près du feu : « Pourquoi les gardes mangent-ils plus ? »"));
                        if (b.tension >= 3 && a.loyaute < 40) {
                            o.add(new Ordre("depart", b.proprio, a.id, "", 0, a.nom + " fait son sac. « Je ne crèverai pas de faim ici. »"));
                            a.etat = "parti";
                        }
                    }
                }
            } else {
                b.tension = 0;
                b.moral = Math.min(100, b.moral + 2);
            }
            while (b.absence.size() > 25) b.absence.remove(0);
        }
        return o;
    }

    // ================================================================ sauvegarde

    public List<String> exporter() {
        List<String> l = new ArrayList<>();
        for (Base b : bases.values()) {
            StringBuilder s = new StringBuilder("B\t" + b.proprio + "\t" + b.etat + "\t" + (int) b.moral + "\t" + b.tension + "\t" + b.sortiesInterdites);
            for (Map.Entry<String, Integer> e : b.minimums.entrySet()) s.append("\tmin:").append(e.getKey()).append('=').append(e.getValue());
            for (Map.Entry<String, Integer> e : b.hier.entrySet()) s.append("\thier:").append(e.getKey()).append('=').append(e.getValue());
            l.add(s.toString());
            for (String a : b.absence) l.add("A\t" + b.proprio + "\t" + a);
            for (String h : b.historique) l.add("H\t" + b.proprio + "\t" + h);
        }
        for (Survivant v : survivants.values()) {
            StringBuilder s = new StringBuilder("V\t" + v.id + "\t" + (int) v.courage + "\t" + (int) v.honnetete + "\t" + (int) v.loyaute + "\t" + (int) v.avidite
                    + "\t" + (int) v.empathie + "\t" + (int) v.paranoia + "\t" + (int) v.sociabilite + "\t" + v.missions + "\t" + v.reussites
                    + "\t" + v.derniereMission + "\t" + v.intention + "\t" + v.intentionJour);
            for (Map.Entry<String, Double> e : v.competences.entrySet()) s.append("\tc:").append(e.getKey()).append('=').append(e.getValue().intValue());
            for (Map.Entry<String, Integer> e : v.xp.entrySet()) s.append("\tx:").append(e.getKey()).append('=').append(e.getValue());
            l.add(s.toString());
            for (String j : v.journal) l.add("J\t" + v.id + "\t" + j);
            l.add("S\t" + v.id + "\t" + v.secret);
        }
        return l;
    }

    public void importer(List<String> l) {
        for (String s : l) {
            String[] c = s.split("\t", -1);
            try {
                switch (c[0]) {
                    case "B": {
                        Base b = base(c[1]);
                        b.etat = c[2];
                        b.moral = Double.parseDouble(c[3]);
                        b.tension = Integer.parseInt(c[4]);
                        b.sortiesInterdites = Boolean.parseBoolean(c[5]);
                        for (int k = 6; k < c.length; k++) {
                            int i = c[k].indexOf('=');
                            if (i < 0) continue;
                            String key = c[k].substring(0, i);
                            int v = Integer.parseInt(c[k].substring(i + 1));
                            if (key.startsWith("min:")) b.minimums.put(key.substring(4), v);
                            else if (key.startsWith("hier:")) b.hier.put(key.substring(5), v);
                        }
                        break;
                    }
                    case "A":
                        base(c[1]).absence.add(c[2]);
                        break;
                    case "H":
                        base(c[1]).historique.add(c[2]);
                        break;
                    case "V": {
                        Survivant v = survivant(Integer.parseInt(c[1]));
                        v.personnaliteFaite = true;
                        v.courage = Double.parseDouble(c[2]);
                        v.honnetete = Double.parseDouble(c[3]);
                        v.loyaute = Double.parseDouble(c[4]);
                        v.avidite = Double.parseDouble(c[5]);
                        v.empathie = Double.parseDouble(c[6]);
                        v.paranoia = Double.parseDouble(c[7]);
                        v.sociabilite = Double.parseDouble(c[8]);
                        v.missions = Integer.parseInt(c[9]);
                        v.reussites = Integer.parseInt(c[10]);
                        v.derniereMission = c[11];
                        v.intention = c[12];
                        v.intentionJour = Integer.parseInt(c[13]);
                        for (int k = 14; k < c.length; k++) {
                            int i = c[k].indexOf('=');
                            if (i < 0) continue;
                            String key = c[k].substring(0, i);
                            if (key.startsWith("c:")) v.competences.put(key.substring(2), Double.parseDouble(c[k].substring(i + 1)));
                            else if (key.startsWith("x:")) v.xp.put(key.substring(2), Integer.parseInt(c[k].substring(i + 1)));
                        }
                        break;
                    }
                    case "J":
                        survivant(Integer.parseInt(c[1])).journal.add(c[2]);
                        break;
                    case "S":
                        survivant(Integer.parseInt(c[1])).secret = c[2];
                        break;
                    default:
                        break;
                }
            } catch (RuntimeException ignored) {
                // ligne abîmée
            }
        }
    }
}
