package za.moteur.coeur;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Le simulateur accéléré (bible F6) : 60 jours de monde sans joueurs, ou avec des « joueurs fantômes » qui imitent
 * des habitudes, en quelques secondes. C'est le test obligatoire des freins (80) : si toute la carte est rouge au
 * jour 40, un frein manque.
 *   java -cp ZAMoteur.jar za.moteur.coeur.Simulateur <graphe.yml> [jours] [fantomes] [reactions.yml]
 */
public final class Simulateur {
    private Simulateur() {
    }

    public static List<String> simuler(Monde m, int jours, int fantomes) {
        List<String> r = new ArrayList<>();
        Random rng = m.rng;
        // les joueurs fantômes : ils tirent, tuent, nettoient, rétablissent parfois le courant
        List<double[]> f = new ArrayList<>();
        for (int i = 0; i < fantomes; i++) f.add(new double[]{(rng.nextDouble() - 0.5) * 3000, (rng.nextDouble() - 0.5) * 3000});
        int megas = 0, frappes = 0;
        for (int j = 1; j <= jours; j++) {
            for (int t = 0; t < 40; t++) {        // un jour serveur = 20 minutes = 40 fois 30 s
                m.maintenant += 30_000;
                m.nuit = t >= 28;
                for (double[] p : f) {
                    p[0] += (rng.nextDouble() - 0.5) * 60;
                    p[1] += (rng.nextDouble() - 0.5) * 60;
                    if (rng.nextDouble() < 0.05) m.publier(new Evenement("tir").a(p[0], p[1]).grav(1));
                    if (rng.nextDouble() < 0.2) m.publier(new Evenement("mort_zombie").a(p[0], p[1]).grav(1));
                    if (rng.nextDouble() < 0.004) m.publier(new Evenement("nid_detruit").a(p[0], p[1]).grav(3));
                    if (rng.nextDouble() < 0.01) m.publier(new Evenement("cadavres_enterres").a(p[0], p[1]).grav(1));
                    Region rg = m.graphe.region(p[0], p[1]);
                    if (rng.nextDouble() < 0.02) rg.habitudes.merge("toits", 2.0, Double::sum);
                    for (Horde h : m.hordes) {
                        if (Math.hypot(h.x - p[0], h.z - p[1]) < 100) {
                            int k = Math.min(h.taille, 1 + rng.nextInt(4));
                            h.taille -= k;
                            h.moral -= k * 2;
                        }
                    }
                }
                m.tick30s();
            }
            int avantM = m.chronique.compte("megahorde", 0), avantF = m.chronique.compte("frappe_incendiaire", 0);
            m.tickJour();
            megas = m.chronique.compte("megahorde", 0);
            frappes = m.chronique.compte("frappe_incendiaire", 0);
            int[] c = m.compteEtats();
            double cont = 0;
            int nids = 0, pop = 0;
            for (Region rg : m.graphe.regions.values()) {
                cont += rg.contamination;
                nids += rg.nids;
                pop += (int) rg.population;
            }
            cont /= m.graphe.regions.size();
            if (j % 5 == 0 || j == 1 || j == jours)
                r.add(String.format("Jour %3d : 🟢%3d 🟡%3d 🟠%3d 🔴%3d ☣%3d | contamination moy. %4.1f | nids %3d | hordes %2d | méga %d | frappes %d | population %d",
                        j, c[0], c[1], c[2], c[3], c[4], cont, nids, m.hordes.size(), megas, frappes, pop));
            if (avantM != megas || avantF != frappes) {
                // rien : déjà compté
            }
        }
        int[] c = m.compteEtats();
        r.add("Carte finale (S stable, C contaminée, D dangereuse, R critique, P perdue) :");
        for (String l : m.carteEtats().split("\n")) r.add("  " + l);
        if (c[3] + c[4] > m.graphe.regions.size() * 0.6) r.add("⚠ PLUS DE 60 % DE LA CARTE EST ROUGE : un frein manque (point 80).");
        else r.add("Freins : OK (la carte ne s'emballe pas).");
        return r;
    }

    public static void main(String[] a) throws Exception {
        Path g = Paths.get(a.length > 0 ? a[0] : "plugins/ZAMoteur/graphe.yml");
        int jours = a.length > 1 ? Integer.parseInt(a[1]) : 60;
        int fant = a.length > 2 ? Integer.parseInt(a[2]) : 0;
        Monde m = new Monde(Graphe.charger(g), 1250);
        if (a.length > 3) m.reactions.charger(Paths.get(a[3]));
        // départ : Saint-Aurèle contaminée, quelques nids
        Region sa = m.graphe.region(0, 0);
        sa.contamination = 60;
        sa.nids = 1;
        sa.nidStade = 2;
        for (int i = 0; i < 6; i++) m.creerHorde(m.graphe.regions.values().stream().skip(m.rng.nextInt(m.graphe.regions.size())).findFirst().orElse(sa), 15 + m.rng.nextInt(20));
        long t0 = System.currentTimeMillis();
        for (String l : simuler(m, jours, fant)) System.out.println(l);
        System.out.println("Événements dans la Chronique : " + m.chronique.total + " — réactions déclenchées : " + m.reactions.declenchees
                + " — en " + (System.currentTimeMillis() - t0) + " ms");
    }
}
