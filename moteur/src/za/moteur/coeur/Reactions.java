package za.moteur.coeur;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Règles de réaction (bible F2 et point 20), lues dans reactions.yml :
 *   « si tel événement arrive (à tel endroit), alors telle conséquence, avec telle probabilité, après tel délai »
 * Chaque règle a un délai, une probabilité, une condition et un plafond par jour, pour éviter les avalanches.
 * Les chaînes ne sont pas écrites d'avance : elles naissent de ces règles simples.
 */
public final class Reactions {
    public static final class Regle {
        public String si = "";
        public String type_lieu = "";        // filtre : type de lieu le plus proche (labo, village, camp...)
        public double proba = 100;
        public int delaiMin, delaiMax;       // minutes réelles
        public String condition = "";
        public int plafond = 99;             // déclenchements par jour serveur
        public final List<String> alors = new ArrayList<>();
        public String nom = "";
    }

    public static final class Prevue {
        public final Regle regle;
        public final Evenement source;
        public final long quand;

        Prevue(Regle r, Evenement s, long q) {
            regle = r;
            source = s;
            quand = q;
        }
    }

    /** ce qui exécute une action (le monde pour les actions du cœur, le plugin pour le reste) */
    public interface Executant {
        void executer(String action, Evenement source, Regle r);
    }

    public final List<Regle> regles = new ArrayList<>();
    private final List<Prevue> prevues = new ArrayList<>();
    private final Map<String, Integer> compteJour = new HashMap<>();
    private int jourCompte = -1;
    private final Random rng;
    public long declenchees;

    public Reactions(Random rng) {
        this.rng = rng;
    }

    public void charger(Path p) throws IOException {
        regles.clear();
        if (!Files.exists(p)) return;
        Map<String, Object> y = MiniYaml.lire(p);
        int k = 0;
        for (Object o : MiniYaml.liste(y.get("reactions"))) {
            Map<String, Object> m = MiniYaml.carte(o);
            Regle r = new Regle();
            r.nom = MiniYaml.txt(m.get("nom"), "regle" + (++k));
            r.si = MiniYaml.txt(m.get("si"), "");
            r.type_lieu = MiniYaml.txt(m.get("lieu"), "");
            r.proba = MiniYaml.num(m.get("proba"), 100);
            String d = MiniYaml.txt(m.get("delai"), "0");
            if (d.contains("-")) {
                String[] c = d.split("-");
                r.delaiMin = (int) MiniYaml.num(c[0], 0);
                r.delaiMax = (int) MiniYaml.num(c[1], r.delaiMin);
            } else {
                r.delaiMin = r.delaiMax = (int) MiniYaml.num(d, 0);
            }
            r.condition = MiniYaml.txt(m.get("condition"), "");
            r.plafond = (int) MiniYaml.num(m.get("plafond"), 99);
            Object a = m.get("alors");
            if (a instanceof List) for (Object x : MiniYaml.liste(a)) r.alors.add(String.valueOf(x));
            else if (a != null) r.alors.add(String.valueOf(a));
            if (!r.si.isEmpty() && !r.alors.isEmpty()) regles.add(r);
        }
    }

    /** un événement arrive : on programme les réactions qui s'appliquent */
    public synchronized void sur(Evenement e, Monde monde, long maintenant) {
        if (e.jour != jourCompte) {
            jourCompte = e.jour;
            compteJour.clear();
        }
        for (Regle r : regles) {
            if (!r.si.equals(e.type) && !r.si.equals("*")) continue;
            if (!r.type_lieu.isEmpty()) {
                Graphe.Lieu l = monde.graphe.lieuProche(e.x, e.z, 400);
                if (l == null || !r.type_lieu.contains(l.type)) continue;
            }
            int c = compteJour.getOrDefault(r.nom, 0);
            if (c >= r.plafond) continue;
            if (!r.condition.isEmpty() && !monde.condition(r.condition, e)) continue;
            if (rng.nextDouble() * 100 >= r.proba) continue;
            compteJour.put(r.nom, c + 1);
            int d = r.delaiMin + (r.delaiMax > r.delaiMin ? rng.nextInt(r.delaiMax - r.delaiMin + 1) : 0);
            prevues.add(new Prevue(r, e, maintenant + d * 60_000L));
        }
    }

    /** exécute ce qui est dû */
    public void tick(long maintenant, Executant ex) {
        List<Prevue> dues = new ArrayList<>();
        synchronized (this) {
            Iterator<Prevue> it = prevues.iterator();
            while (it.hasNext()) {
                Prevue p = it.next();
                if (p.quand <= maintenant) {
                    dues.add(p);
                    it.remove();
                }
            }
            // garde-fou contre l'avalanche
            while (prevues.size() > 500) prevues.remove(0);
        }
        for (Prevue p : dues) {
            declenchees++;
            for (String a : p.regle.alors) ex.executer(a, p.source, p.regle);
        }
    }

    public synchronized int enAttente() {
        return prevues.size();
    }
}
