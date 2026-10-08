package za.moteur.coeur;

import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/** Une horde-agent (bible IA-7) : un personnage avec un but, une mémoire et un moral. Vit comme des données (F4). */
public final class Horde {
    public final int id;
    public String nom = "";
    public int taille;
    public String region;
    public double x, z;
    public double cx, cz;               // cible courante
    public String objectif = "errer";   // suivre_son | migrer | manger | nicher | hiberner | fuir | assieger | errer | traquer
    public double moral = 100, faim = 30;
    public boolean alpha;
    public String perso = "nomade";     // agressive | prudente | nomade
    public final Map<String, Double> genome = new LinkedHashMap<>();
    public final Set<String> proies = new HashSet<>();       // régions où elle a trouvé des proies
    public final Set<String> resistee = new HashSet<>();     // bases (uuid) qui lui ont résisté
    public int reels;                    // zombies matérialisés en ce moment
    public long horsVue;                 // ms depuis que plus personne n'est près
    public boolean mega;
    public String traquee = "";          // uuid d'un joueur visé par le Directeur

    public Horde(int id) {
        this.id = id;
    }

    public double vitesse(String saison, boolean nuit) {
        double v = 1.2;
        if ("hiver".equals(saison)) v *= 0.6;
        if (nuit) v *= 1.3;
        if (perso.equals("agressive")) v *= 1.2;
        if (objectif.equals("fuir")) v *= 1.5;
        return v;
    }

    public String resume() {
        return "#" + id + (nom.isEmpty() ? "" : " « " + nom + " »") + " " + taille + " morts, " + objectif + ", moral "
                + (int) moral + (alpha ? ", Alpha" : "") + (mega ? ", MÉGAHORDE" : "") + " — " + region
                + " (" + (int) x + ", " + (int) z + ")";
    }
}
