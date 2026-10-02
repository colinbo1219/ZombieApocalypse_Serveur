package za.moteur.coeur;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Un nœud-région du graphe du monde (bible F3) : son état complet, son génome de zombies (IA-6), ses habitudes de joueurs,
 * ses traces de bruit (3) et son état rouge → vert (80).
 */
public final class Region {
    public final String id;
    public String nom;
    public final double cx, cz;
    public boolean riviere;
    public final List<double[]> routes = new ArrayList<>();
    public final List<String> lieux = new ArrayList<>();

    // ----- état (0-100 sauf mention)
    public double contamination = 10;
    public double cadavres;            // charge de cadavres (1)
    public int nids;                   // nids virtuels (25) — stade max 4
    public int nidStade;               // 0 aucun, 1 germe, 2 foyer, 3 ruche, 4 matrice
    public double attentionZ;          // attention des zombies (108)
    public double attentionN;          // attention de NORDA (108)
    public double securite = 40, moral = 50, panique = 10;
    public double population = 20;     // civils et PNJ (virtuels)
    public double eau = 80;            // eau saine (85)
    public double vegetation = 10;     // la nature reprend (115)
    public boolean courant;            // une sous-station produit dans la région (p61)
    public boolean stationEau;         // station d'eau réparée (106)
    public boolean meteo;              // station météo réparée (106)
    public int tours;                  // tours cellulaires réparées (82, 106)
    public int repeteurs;              // répéteurs radio (106)
    public String faction = "";        // faction dominante (p45)
    public int etat;                   // 0 Stable, 1 Contaminée, 2 Dangereuse, 3 Critique, 4 Perdue (80)
    public int calmeJusqua;            // jour de fin de la période calme (69)
    public int nettoyeeJour = -1;      // marque « Nettoyé — Jour N »
    public int quarantaineJusqua = -1; // quarantaine militaire (33)
    public int interdictionFarm = -1;  // les morts évitent un piège jusqu'à ce jour (4)
    public double puissance;           // somme des adaptations (plafond, IA-6)
    public final List<String> plaques = new ArrayList<>();     // ce qui reste gravé (règle 1)
    public final List<String> historique = new ArrayList<>();

    // ----- génome (IA-6) : poids de chaque type, traits fréquents
    public final Map<String, Double> genome = new LinkedHashMap<>();
    public final Map<String, Double> traits = new LinkedHashMap<>();
    public final Map<String, Double> succes = new LinkedHashMap<>();   // dégâts / survie du jour par type
    public final Map<String, Double> pertes = new LinkedHashMap<>();
    // ----- habitudes des joueurs dans la région (mémoire qui s'efface)
    public final Map<String, Double> habitudes = new LinkedHashMap<>();
    // ----- traces de bruit : {x, z, force, expire(ms)}
    public final List<double[]> traces = new ArrayList<>();

    public static final String[] TYPES = {"ZA_Shambler", "ZA_Runner", "ZA_Crawler", "ZA_Spitter", "ZA_Bloater", "ZA_Leaper",
            "ZA_Brute", "ZA_Screamer", "ZA_Stalker", "ZA_Armored", "ZA_Shielded", "ZA_FakeDead", "ZA_Phototrope",
            "ZA_Citoyen_Infecte", "ZA_Observer"};
    public static final String[] HABITUDES = {"armes_feu", "melee", "lumiere", "toits", "feu", "barricades", "routes",
            "refuges", "leurres", "farm"};
    public static final String[] TRAITS = {"grimpeur", "carbonise", "blinde", "sourd_aux_leurres", "evite_pieges",
            "obstine", "aveugle", "boiteux", "affame", "craintif"};

    public Region(String id, String nom, double cx, double cz) {
        this.id = id;
        this.nom = nom;
        this.cx = cx;
        this.cz = cz;
        for (String t : TYPES) genome.put(t, base(t));
        for (String h : HABITUDES) habitudes.put(h, 0.0);
        for (String t : TRAITS) traits.put(t, 0.0);
    }

    static double base(String t) {
        switch (t) {
            case "ZA_Shambler":
            case "ZA_Citoyen_Infecte":
                return 30;
            case "ZA_Runner":
                return 12;
            case "ZA_Crawler":
                return 8;
            case "ZA_Spitter":
            case "ZA_Leaper":
            case "ZA_Stalker":
                return 5;
            case "ZA_Brute":
            case "ZA_Screamer":
            case "ZA_Bloater":
                return 4;
            default:
                return 2;
        }
    }

    /** tirage d'un type selon le génome */
    public String tirerType(java.util.Random r) {
        double tot = 0;
        for (double v : genome.values()) tot += Math.max(0.1, v);
        double x = r.nextDouble() * tot;
        for (Map.Entry<String, Double> e : genome.entrySet()) {
            x -= Math.max(0.1, e.getValue());
            if (x <= 0) return e.getKey();
        }
        return "ZA_Shambler";
    }

    public String etatNom() {
        switch (etat) {
            case 0:
                return "🟢 Stable";
            case 1:
                return "🟡 Contaminée";
            case 2:
                return "🟠 Dangereuse";
            case 3:
                return "🔴 Critique";
            default:
                return "☣ Perdue";
        }
    }

    public void noter(int jour, String t) {
        historique.add("J" + jour + " " + t);
        while (historique.size() > 40) historique.remove(0);
    }

    public double danger() {
        return contamination * 0.4 + Math.min(100, cadavres) * 0.2 + nids * 15 + nidStade * 8 + attentionZ * 0.2;
    }
}
