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

    private static long suivant = 1;

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
