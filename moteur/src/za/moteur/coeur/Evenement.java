package za.moteur.coeur;

import java.util.ArrayList;
import java.util.List;

/** Un événement de la Chronique (bible F2) : ce qui s'est passé, où, qui, à quel point c'est grave, et si c'est vrai. */
public final class Evenement {
    public final long id;
    public final String type;
    public String region;
    public String monde = "world";
    public double x, z;
    public final List<String> acteurs = new ArrayList<>();
    public int gravite = 1;
    /** vrai | faux | inconnu */
    public String verite = "vrai";
    public final List<String> temoins = new ArrayList<>();
    public String source = "monde";
    public int jour;
    public long quand = System.currentTimeMillis();
    public String texte = "";
    public boolean diffuse;
    /** importance 0-100 (F2) : -1 = calculée par la Chronique selon le type et la gravité */
    public int importance = -1;
    /** public | prive | faction | secret (F2) ; ceux qui savent : savent */
    public String visibilite = "public";
    public final List<String> savent = new ArrayList<>();
    /** la partie cachée d'un événement (F10) : connue seulement de « savent » */
    public String secret = "";
    /** certitude de la source, en % (F2, F9) */
    public int fiabilite = 100;

    private static long suivant = System.currentTimeMillis();

    public Evenement(String type) {
        synchronized (Evenement.class) {
            this.id = suivant++;
        }
        this.type = type;
    }

    public Evenement a(double x, double z) {
        this.x = x;
        this.z = z;
        return this;
    }

    public Evenement grav(int g) {
        this.gravite = Math.max(1, Math.min(5, g));
        return this;
    }

    public Evenement acteur(String a) {
        if (a != null && !a.isEmpty()) acteurs.add(a);
        return this;
    }

    public Evenement dit(String t) {
        this.texte = t == null ? "" : t;
        return this;
    }

    public Evenement imp(int i) {
        this.importance = Math.max(0, Math.min(100, i));
        return this;
    }

    public Evenement temoin(String t) {
        if (t != null && !t.isEmpty() && !temoins.contains(t)) temoins.add(t);
        return this;
    }

    public Evenement cache(String secretTexte, String... qui) {
        this.secret = secretTexte;
        for (String q : qui) savent.add(q);
        return this;
    }

    public Evenement faux() {
        this.verite = "faux";
        return this;
    }

    public String ligne() {
        return "J" + jour + " [" + type + "] " + (region == null ? "?" : region) + " g" + gravite
                + (verite.equals("vrai") ? "" : " (" + verite + ")") + (acteurs.isEmpty() ? "" : " " + acteurs)
                + (texte.isEmpty() ? "" : " : " + texte);
    }
}
