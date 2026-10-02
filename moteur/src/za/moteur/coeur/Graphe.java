package za.moteur.coeur;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Le graphe du monde (bible F3) : régions, lieux, liens (routes, terres, rivière à sens unique). */
public final class Graphe {
    public static final class Lien {
        public final String a, b, type;
        public final double cout;
        public boolean coupe;   // pont détruit (86), barrage NORDA, route enneigée...

        Lien(String a, String b, double cout, String type) {
            this.a = a;
            this.b = b;
            this.cout = cout;
            this.type = type;
        }
    }

    public static final class Lieu {
        public final String id, type, nom, region;
        public final double x, z;

        Lieu(String id, String type, String nom, double x, double z, String region) {
            this.id = id;
            this.type = type;
            this.nom = nom;
            this.x = x;
            this.z = z;
            this.region = region;
        }
    }

    public final Map<String, Region> regions = new LinkedHashMap<>();
    public final Map<String, Lieu> lieux = new LinkedHashMap<>();

    /** un lieu créé en jeu (camp de joueurs, /camp) */
    public Lieu ajouterLieu(String id, String type, String nom, double x, double z) {
        String rid = regionId(x, z);
        Lieu l = new Lieu(id, type, nom, x, z, rid);
        Lieu ancien = lieux.put(id, l);
        Region r = regions.get(rid);
        if (r != null && (ancien == null || !r.lieux.contains(id))) r.lieux.add(id);
        return l;
    }
    public final List<Lien> liens = new ArrayList<>();
    public int taille = 1000, n = 10, limite = 5000;

    public static Graphe charger(Path p) throws IOException {
        Graphe g = new Graphe();
        Map<String, Object> y = MiniYaml.lire(p);
        g.taille = (int) MiniYaml.num(y.get("taille"), 1000);
        g.n = (int) MiniYaml.num(y.get("n"), 10);
        g.limite = (int) MiniYaml.num(y.get("limite"), 5000);
        for (Map.Entry<String, Object> e : MiniYaml.carte(y.get("regions")).entrySet()) {
            Map<String, Object> m = MiniYaml.carte(e.getValue());
            Region r = new Region(e.getKey(), MiniYaml.txt(m.get("nom"), e.getKey()), MiniYaml.num(m.get("x"), 0), MiniYaml.num(m.get("z"), 0));
            r.riviere = MiniYaml.vrai(m.get("riviere"));
            for (Object o : MiniYaml.liste(m.get("routes"))) {
                String[] c = String.valueOf(o).split(";");
                if (c.length >= 2) r.routes.add(new double[]{Double.parseDouble(c[0]), Double.parseDouble(c[1])});
            }
            g.regions.put(r.id, r);
        }
        for (Map.Entry<String, Object> e : MiniYaml.carte(y.get("lieux")).entrySet()) {
            Map<String, Object> m = MiniYaml.carte(e.getValue());
            Lieu l = new Lieu(e.getKey(), MiniYaml.txt(m.get("type"), "?"), MiniYaml.txt(m.get("nom"), e.getKey()),
                    MiniYaml.num(m.get("x"), 0), MiniYaml.num(m.get("z"), 0), MiniYaml.txt(m.get("region"), ""));
            g.lieux.put(l.id, l);
            Region r = g.regions.get(l.region);
            if (r != null) r.lieux.add(l.id);
        }
        for (Object o : MiniYaml.liste(y.get("liens"))) {
            String[] c = String.valueOf(o).split(";");
            if (c.length >= 4) g.liens.add(new Lien(c[0], c[1], Double.parseDouble(c[2]), c[3]));
        }
        if (g.regions.isEmpty()) g.grilleVide();
        return g;
    }

    /** graphe de secours (pas de graphe.yml) : une grille nue */
    public void grilleVide() {
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++) {
                String id = "r_" + i + "_" + j;
                regions.put(id, new Region(id, "Région " + i + "-" + j, -limite + i * taille + taille / 2.0, -limite + j * taille + taille / 2.0));
            }
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++) {
                if (i + 1 < n) liens.add(new Lien("r_" + i + "_" + j, "r_" + (i + 1) + "_" + j, 3, "terre"));
                if (j + 1 < n) liens.add(new Lien("r_" + i + "_" + j, "r_" + i + "_" + (j + 1), 3, "terre"));
            }
    }

    public String regionId(double x, double z) {
        int i = (int) Math.floor((x + limite) / taille);
        int j = (int) Math.floor((z + limite) / taille);
        i = Math.max(0, Math.min(n - 1, i));
        j = Math.max(0, Math.min(n - 1, j));
        return "r_" + i + "_" + j;
    }

    public Region region(double x, double z) {
        return regions.get(regionId(x, z));
    }

    /** voisins par la terre ou la route (dans les deux sens), liens non coupés */
    public List<Region> voisins(String id) {
        List<Region> r = new ArrayList<>();
        for (Lien l : liens) {
            if (l.coupe || l.type.equals("riviere")) continue;
            if (l.a.equals(id) && regions.containsKey(l.b)) r.add(regions.get(l.b));
            else if (l.b.equals(id) && regions.containsKey(l.a)) r.add(regions.get(l.a));
        }
        return r;
    }

    /** région en aval par la rivière (sens unique), null sinon */
    public Region aval(String id) {
        for (Lien l : liens) if (l.type.equals("riviere") && l.a.equals(id)) return regions.get(l.b);
        return null;
    }

    public Lien lien(String a, String b) {
        for (Lien l : liens)
            if ((l.a.equals(a) && l.b.equals(b)) || (l.a.equals(b) && l.b.equals(a))) return l;
        return null;
    }

    public Lieu lieuProche(double x, double z, double max) {
        Lieu best = null;
        double bd = max * max;
        for (Lieu l : lieux.values()) {
            double d = (l.x - x) * (l.x - x) + (l.z - z) * (l.z - z);
            if (d < bd) {
                bd = d;
                best = l;
            }
        }
        return best;
    }
}
