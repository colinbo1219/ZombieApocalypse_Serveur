package za.moteur.coeur;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * NORDA, une IA qui CROIT des choses (bible IA-11, points 79 à 83, 96, 98 à 101, 108).
 * Elle n'est pas omnisciente : elle tient un dossier par joueur et par faction, nourri de preuves bruitées,
 * peut se tromper, hésiter entre deux coupables, apprendre des tromperies, et n'a que des moyens limités.
 */
public final class Norda {
    public static final class Dossier {
        public final String cle;            // uuid du joueur ou "faction:<nom>"
        public String nom = "";
        public double soupcon;              // 0-100
        public double certitude;            // 0-100 : NORDA est-elle sûre de QUI c'est ?
        public String identiteSupposee = "";
        public String affiliationSupposee = "";
        public double posX, posZ, rayon = 99999;   // dernière position connue et son incertitude
        public int posJour = -1;
        public final Map<String, Integer> routes = new LinkedHashMap<>();   // régions fréquentées (habitudes)
        public final List<String> preuves = new ArrayList<>();
        public final List<String> croyances = new ArrayList<>();          // ce que NORDA croit, erreurs comprises
        public int palier;
        public int tromperies;              // fausses traces démasquées par NORDA
        public int prudenceJusqua = -1;     // NORDA vérifie davantage (elle s'est fait avoir)

        Dossier(String cle) {
            this.cle = cle;
        }

        public String palierNom() {
            return new String[]{"Inconnu", "Intérêt", "Surveillance", "Identifié", "Intervention", "Priorité"}[palier];
        }

        public String routeHabituelle() {
            String best = null;
            int bv = 0;
            for (Map.Entry<String, Integer> e : routes.entrySet())
                if (e.getValue() > bv) {
                    bv = e.getValue();
                    best = e.getKey();
                }
            return best;
        }
    }

    /** un ordre que le plugin exécute dans le monde réel */
    public static final class Ordre {
        public final String type;    // drone | patrouille | barrage | chasse | capture | sms | radio | marche
        public final String cible;   // clé du dossier
        public final String region;
        public final String texte;

        Ordre(String type, String cible, String region, String texte) {
            this.type = type;
            this.cible = cible;
            this.region = region;
            this.texte = texte;
        }
    }

    public final Map<String, Dossier> dossiers = new LinkedHashMap<>();
    public int drones = 2, patrouilles = 1, barrages = 1, chasses = 1;
    private final Random rng;

    public Norda(Random rng) {
        this.rng = rng;
    }

    public Dossier dossier(String cle) {
        return dossiers.computeIfAbsent(cle, Dossier::new);
    }

    /**
     * Une preuve. type : elec | radio | cel | drone | temoin | doc | labo | convoi | camera | agent.
     * La précision de la position dépend du type (et du nombre de tours pour le cellulaire, point 82).
     */
    public void preuve(String cle, String type, double force, double x, double z, int jour, int tours) {
        Dossier d = dossier(cle);
        double bruit;
        double gainCert;
        switch (type) {
            case "cel":
                bruit = tours <= 0 ? 99999 : 900.0 / tours;      // une tour : rayon trop grand ; trois tours : précis
                gainCert = 4;
                break;
            case "drone":
            case "camera":
                bruit = 15;
                gainCert = 12;
                break;
            case "temoin":
            case "agent":
                bruit = 120;
                gainCert = 8;
                break;
            case "radio":
                bruit = 300;
                gainCert = 3;
                break;
            case "elec":
                bruit = 60;
                gainCert = 1;
                break;
            default:
                bruit = 250;
                gainCert = 5;
                break;
        }
        // NORDA a été trompée récemment : elle recoupe davantage
        double k = d.prudenceJusqua >= jour ? 0.6 : 1.0;
        d.soupcon = Math.min(100, d.soupcon + force * k);
        d.certitude = Math.min(100, d.certitude + gainCert * k * (force / 10));
        if (bruit < 99999 && (bruit < d.rayon || jour > d.posJour)) {
            d.posX = x + (rng.nextDouble() - 0.5) * bruit;
            d.posZ = z + (rng.nextDouble() - 0.5) * bruit;
            d.rayon = bruit;
            d.posJour = jour;
        }
        d.preuves.add("J" + jour + " " + type + " (" + (int) force + ")");
        while (d.preuves.size() > 30) d.preuves.remove(0);
        recalculer(d, jour);
    }

    /** une fausse trace (81) : elle accuse quelqu'un d'autre ; NORDA peut la détecter selon sa qualité */
    public boolean fausseTrace(String auteur, String accuse, double qualite, int jour) {
        Dossier a = dossier(auteur);
        Dossier v = dossier(accuse);
        double detection = Math.max(5, 60 - qualite) + a.tromperies * 5;
        if (rng.nextDouble() * 100 < detection) {
            // démasquée : le soupçon du faussaire explose
            a.soupcon = Math.min(100, a.soupcon + 30);
            a.certitude = Math.min(100, a.certitude + 20);
            a.croyances.add("J" + jour + " : a fabriqué de fausses preuves contre " + accuse);
            recalculer(a, jour);
            return false;
        }
        v.soupcon = Math.min(100, v.soupcon + 15 + qualite / 5);
        v.croyances.add("J" + jour + " : impliqué dans un sabotage (preuve plantée)");
        recalculer(v, jour);
        return true;
    }

    /** faux papiers (83) : brouillent l'identité, pas le soupçon */
    public void fauxPapiers(String cle, double qualite, int jour) {
        Dossier d = dossier(cle);
        double eff = d.palier >= 5 ? qualite / 4 : qualite / 2;
        d.certitude = Math.max(0, d.certitude - eff);
        d.identiteSupposee = "inconnu (papiers au nom d'un autre)";
        recalculer(d, jour);
    }

    /** détruire des preuves, son dossier physique, changer ses habitudes... */
    public void effacer(String cle, double certitude, double soupcon, int jour) {
        Dossier d = dossier(cle);
        d.certitude = Math.max(0, d.certitude - certitude);
        d.soupcon = Math.max(0, d.soupcon - soupcon);
        recalculer(d, jour);
    }

    public void route(String cle, String region) {
        dossier(cle).routes.merge(region, 1, Integer::sum);
    }

    void recalculer(Dossier d, int jour) {
        int p;
        double s = d.soupcon, c = d.certitude;
        if (s < 10) p = 0;
        else if (s < 25) p = 1;
        else if (s < 45) p = 2;
        else if (s < 65 || c < 40) p = 3;
        else if (s < 85 || c < 60) p = 4;
        else p = 5;
        if (p >= 3 && c < 25) p = 2;    // on ne peut pas identifier quelqu'un dont on ne sait rien
        d.palier = p;
        d.croyances.removeIf(x -> x.startsWith("POS "));
        if (d.rayon < 99999) d.croyances.add("POS dernière position : X " + (int) d.posX + ", Z " + (int) d.posZ + " (± " + (int) d.rayon + ")");
    }

    /**
     * Le plan de la journée : NORDA envoie ses moyens limités là où la menace lui paraît la plus grande,
     * sur les routes qu'elle croit que la cible prend (prédiction des habitudes).
     */
    public List<Ordre> planDuJour(int jour) {
        List<Ordre> o = new ArrayList<>();
        // le soupçon retombe avec le temps (règle 2 : l'absence ne punit pas)
        for (Dossier d : dossiers.values()) {
            d.soupcon = Math.max(0, d.soupcon - 3);
            d.certitude = Math.max(0, d.certitude - 1);
            recalculer(d, jour);
        }
        List<Dossier> tri = new ArrayList<>(dossiers.values());
        tri.sort((a, b) -> Double.compare(b.soupcon * (0.5 + b.certitude / 100), a.soupcon * (0.5 + a.certitude / 100)));
        int dr = drones, pa = patrouilles, ba = barrages, ch = chasses;
        for (Dossier d : tri) {
            if (d.palier <= 0) break;
            String reg = d.routeHabituelle();
            if (d.palier == 1) o.add(new Ordre("sms", d.cle, reg, "1"));
            if (d.palier >= 2 && dr > 0) {
                dr--;
                o.add(new Ordre("drone", d.cle, reg, ""));
            }
            if (d.palier >= 3) o.add(new Ordre("sms", d.cle, reg, "3"));
            if (d.palier >= 3 && ba > 0 && reg != null) {
                ba--;
                o.add(new Ordre("barrage", d.cle, reg, ""));
            }
            if (d.palier >= 4 && pa > 0) {
                pa--;
                o.add(new Ordre("patrouille", d.cle, reg, ""));
            }
            if (d.palier >= 5 && ch > 0) {
                ch--;
                o.add(new Ordre("capture", d.cle, reg, ""));
                o.add(new Ordre("radio", d.cle, reg, "publique"));
            }
            if (d.palier >= 4 && rng.nextDouble() < 0.15) o.add(new Ordre("marche", d.cle, reg, ""));
        }
        return o;
    }

    public int palierMax() {
        int m = 0;
        for (Dossier d : dossiers.values()) m = Math.max(m, d.palier);
        return m;
    }
}
