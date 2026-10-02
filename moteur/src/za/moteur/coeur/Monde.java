package za.moteur.coeur;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Le monde simulé (bible F1, F3, F4, IA-6, IA-7, points 1, 3, 18, 25, 69, 80, 89, 108) — sans Bukkit, pour que le
 * simulateur accéléré (F6) puisse le faire tourner hors du serveur.
 */
public final class Monde {
    /** ce que le monde demande au plugin (radio, Skript, matérialisation...) */
    public interface Pont {
        void action(String action, Evenement source);
    }

    public final Graphe graphe;
    public final Chronique chronique = new Chronique();
    public final Reactions reactions;
    public final List<Horde> hordes = new ArrayList<>();
    public final Random rng;
    public int jour;
    public String saison = "ete";
    public boolean nuit;
    public Pont pont = (a, e) -> { };
    private int prochainId = 1;
    public long maintenant = System.currentTimeMillis();

    // plafonds de départ (à régler avec la télémétrie, F5)
    public int maxHordes = 40;
    public int maxNidsRegion = 3;
    public double maxPuissance = 60;
    public double equilibre = 15;           // contamination vers laquelle une région revient seule
    public int maxNidsMonde = 25;
    public int derniereMega = -99;

    public Monde(Graphe g, long graine) {
        this.graphe = g;
        this.rng = new Random(graine);
        this.reactions = new Reactions(rng);
        chronique.ecouter(e -> reactions.sur(e, this, maintenant));
    }

    // ================================================================ Chronique

    public Evenement publier(Evenement e) {
        if (e.region == null) e.region = graphe.regionId(e.x, e.z);
        e.jour = jour;
        Region r = graphe.regions.get(e.region);
        if (r != null) {
            appliquer(e, r);
            if (e.gravite >= 3) r.noter(jour, e.type + (e.texte.isEmpty() ? "" : " : " + e.texte));
        }
        chronique.publier(e);
        return e;
    }

    /** effets directs et simples de chaque type d'événement (le reste passe par reactions.yml) */
    private void appliquer(Evenement e, Region r) {
        switch (e.type) {
            case "mort_zombie":
                r.cadavres += 1;
                break;
            case "mort_joueur":
                r.cadavres += 3;
                r.contamination = Math.min(100, r.contamination + 2);
                break;
            case "explosion":
                bruit(e.x, e.z, 160);
                break;
            case "tir":
                bruit(e.x, e.z, 64);
                r.habitudes.merge("armes_feu", 1.0, Double::sum);
                break;
            case "nid_detruit":
                r.nids = Math.max(0, r.nids - 1);
                if (r.nids == 0) r.nidStade = 0;
                r.contamination = Math.max(0, r.contamination - 12);
                break;
            case "boss_tue":
                r.etat = Math.max(0, r.etat - 1);
                r.contamination = Math.max(0, r.contamination - 20);
                r.plaques.add("J" + jour + " : " + (e.texte.isEmpty() ? "un boss est tombé" : e.texte));
                break;
            case "cadavres_brules":
                r.cadavres = Math.max(0, r.cadavres - 40);
                bruit(e.x, e.z, 40);
                r.attentionZ += 10;
                break;
            case "cadavres_enterres":
            case "cadavres_chaux":
                r.cadavres = Math.max(0, r.cadavres - 30);
                break;
            case "labo_detruit":
                r.contamination = Math.min(100, r.contamination + 30);
                r.attentionN += 30;
                break;
            case "courant_retabli":
                r.courant = true;
                r.attentionN += 5;
                r.attentionZ += 5;
                break;
            case "courant_coupe":
                r.courant = false;
                break;
            case "ville_tombee":
                r.plaques.add("Chute de " + r.nom + " — Jour " + jour);
                break;
            default:
                break;
        }
    }

    // ================================================================ bruit (3) et attentions (108)

    /** un bruit : trace de 10 minutes dans la région, que les hordes entendent jusqu'à 300 blocs */
    public void bruit(double x, double z, double force) {
        Region r = graphe.region(x, z);
        if (r == null) return;
        synchronized (r.traces) {
            r.traces.add(new double[]{x, z, force, maintenant + 600_000});
            while (r.traces.size() > 30) r.traces.remove(0);
        }
        r.attentionZ = Math.min(100, r.attentionZ + force / 20);
    }

    public double[] plusFortBruit(double x, double z, double portee) {
        double[] best = null;
        double bs = 0;
        for (Region r : graphe.regions.values()) {
            if (Math.abs(r.cx - x) > portee + 600 || Math.abs(r.cz - z) > portee + 600) continue;
            synchronized (r.traces) {
                for (double[] t : r.traces) {
                    if (t[3] < maintenant) continue;
                    double d = Math.hypot(t[0] - x, t[1] - z);
                    double audible = Math.min(portee, t[2] * 2.5);
                    if (d > audible) continue;
                    double s = t[2] * (1 - d / (audible + 1)) * (0.5 + 0.5 * (t[3] - maintenant) / 600_000.0);
                    if (s > bs) {
                        bs = s;
                        best = t;
                    }
                }
            }
        }
        return best;
    }

    // ================================================================ conditions des réactions

    public boolean condition(String c, Evenement e) {
        String[] t = c.trim().split("\\s+");
        if (t.length != 3) return true;
        Region r = graphe.regions.get(e.region);
        if (r == null) return false;
        double v;
        switch (t[0].replace("region.", "")) {
            case "contamination":
                v = r.contamination;
                break;
            case "panique":
                v = r.panique;
                break;
            case "moral":
                v = r.moral;
                break;
            case "securite":
                v = r.securite;
                break;
            case "etat":
                v = r.etat;
                break;
            case "population":
                v = r.population;
                break;
            case "nids":
                v = r.nids;
                break;
            case "cadavres":
                v = r.cadavres;
                break;
            case "gravite":
                v = e.gravite;
                break;
            default:
                return true;
        }
        double w = MiniYaml.num(t[2], 0);
        switch (t[1]) {
            case ">":
                return v > w;
            case ">=":
                return v >= w;
            case "<":
                return v < w;
            case "<=":
                return v <= w;
            case "=":
            case "==":
                return v == w;
            default:
                return true;
        }
    }

    /** actions du cœur ; tout le reste est confié au plugin */
    public void executer(String action, Evenement src) {
        String[] t = action.trim().split("\\s+", 3);
        Region r = graphe.regions.get(src.region);
        String k = t[0];
        double n = t.length > 1 ? MiniYaml.num(t[1].replace("+", ""), 0) : 0;
        switch (k) {
            case "contamination":
                if (r != null) {
                    r.contamination = clamp(r.contamination + n);
                    if (t.length > 2 && t[2].contains("aval")) {
                        Region a = graphe.aval(r.id);
                        for (int i = 0; a != null && i < 4; i++) {
                            a.contamination = clamp(a.contamination + n * 0.6);
                            a.eau = clamp(a.eau - n * 0.8);
                            a = graphe.aval(a.id);
                        }
                    }
                }
                return;
            case "panique":
                if (r != null) r.panique = clamp(r.panique + n);
                return;
            case "moral":
                if (r != null) r.moral = clamp(r.moral + n);
                return;
            case "securite":
                if (r != null) r.securite = clamp(r.securite + n);
                return;
            case "population":
                if (r != null) r.population = Math.max(0, r.population + n);
                return;
            case "attentionZ":
                if (r != null) r.attentionZ = clamp(r.attentionZ + n);
                return;
            case "attentionN":
                if (r != null) r.attentionN = clamp(r.attentionN + n);
                return;
            case "cadavres":
                if (r != null) r.cadavres = Math.max(0, r.cadavres + n);
                return;
            case "eau":
                if (r != null) r.eau = clamp(r.eau + n);
                return;
            case "nid":
                if (r != null && r.nids < maxNidsRegion) {
                    r.nids++;
                    r.nidStade = Math.max(1, r.nidStade);
                }
                return;
            case "quarantaine":
                if (r != null) {
                    r.quarantaineJusqua = jour + (int) Math.max(1, n);
                    publier(new Evenement("quarantaine").a(r.cx, r.cz).grav(4).dit(r.nom));
                }
                return;
            case "calme":
                if (r != null) r.calmeJusqua = jour + (int) Math.max(1, n);
                return;
            case "plaque":
                if (r != null) r.plaques.add("J" + jour + " : " + (t.length > 1 ? action.substring(action.indexOf(' ') + 1) : src.type));
                return;
            case "horde":
                if (t.length > 1 && t[1].equals("attirer")) {
                    attirerHorde(src.x, src.z, 600);
                    return;
                }
                if (t.length > 1 && t[1].equals("creer")) {
                    creerHorde(r, 10 + rng.nextInt(20));
                    return;
                }
                break;
            case "evenement":
                if (t.length > 1) {
                    Evenement e = new Evenement(t[1]).a(src.x, src.z).grav(t.length > 2 ? (int) MiniYaml.num(t[2], 2) : 2);
                    e.acteurs.addAll(src.acteurs);
                    e.source = "reaction";
                    publier(e);
                }
                return;
            default:
                break;
        }
        pont.action(action, src);
    }

    private static double clamp(double v) {
        return Math.max(0, Math.min(100, v));
    }

    // ================================================================ hordes-agents (IA-7)

    public Horde creerHorde(Region r, int taille) {
        if (r == null || hordes.size() >= maxHordes) return null;
        Horde h = new Horde(prochainId++);
        h.taille = taille;
        h.region = r.id;
        h.x = r.cx + (rng.nextDouble() - 0.5) * 800;
        h.z = r.cz + (rng.nextDouble() - 0.5) * 800;
        h.cx = h.x;
        h.cz = h.z;
        h.alpha = taille > 15 && rng.nextDouble() < 0.5;
        h.perso = new String[]{"agressive", "prudente", "nomade"}[rng.nextInt(3)];
        h.genome.putAll(r.genome);
        hordes.add(h);
        return h;
    }

    public Horde attirerHorde(double x, double z, double rayon) {
        Horde best = null;
        double bd = rayon;
        for (Horde h : hordes) {
            double d = Math.hypot(h.x - x, h.z - z);
            if (d < bd) {
                bd = d;
                best = h;
            }
        }
        if (best != null) {
            best.objectif = "suivre_son";
            best.cx = x;
            best.cz = z;
        }
        return best;
    }

    /** toutes les 30 secondes */
    public void tick30s() {
        maintenant = System.currentTimeMillis();
        for (Region r : graphe.regions.values()) {
            synchronized (r.traces) {
                r.traces.removeIf(t -> t[3] < maintenant);
            }
            r.attentionZ = Math.max(0, r.attentionZ - 0.5);
            r.attentionN = Math.max(0, r.attentionN - 0.1);
        }
        Iterator<Horde> it = hordes.iterator();
        while (it.hasNext()) {
            Horde h = it.next();
            if (h.taille <= 0) {
                Region r = graphe.regions.get(h.region);
                if (r != null) r.noter(jour, "La horde #" + h.id + " a été anéantie.");
                it.remove();
                continue;
            }
            penser(h);
            bouger(h, 30);
        }
        fusionner();
        reactions.tick(maintenant, this::executerReaction);
    }

    private void executerReaction(String a, Evenement src, Reactions.Regle r) {
        executer(a, src);
    }

    /** choisit l'objectif le plus utile maintenant (score) */
    private void penser(Horde h) {
        Region r = graphe.regions.get(h.region);
        if (r == null) return;
        h.faim = Math.min(100, h.faim + 0.4);
        h.moral = Math.min(100, h.moral + 1);
        if (!h.traquee.isEmpty() && h.objectif.equals("traquer")) return;
        if (h.moral < 30) {
            h.objectif = "fuir";
            double a = rng.nextDouble() * Math.PI * 2;
            h.cx = h.x + Math.cos(a) * 500;
            h.cz = h.z + Math.sin(a) * 500;
            return;
        }
        if ("hiver".equals(saison) && !h.mega) {
            h.objectif = "hiberner";
            return;
        }
        double sSon = 0, sManger = 0, sNicher = 0, sMigrer = 8, sFuir = 0;
        double[] son = plusFortBruit(h.x, h.z, 300);
        if (son != null) sSon = son[2] * (h.perso.equals("agressive") ? 1.5 : 1.0);
        Region meilleureNourriture = r;
        for (Region v : graphe.voisins(r.id)) if (v.cadavres > meilleureNourriture.cadavres) meilleureNourriture = v;
        sManger = meilleureNourriture.cadavres * h.faim / 60;
        if (r.nids == 0 && h.taille > 25 && (nuit || h.faim < 30) && nidsTotal() < maxNidsMonde) sNicher = 20;
        if (r.securite > 75) sFuir = 30;
        if (h.perso.equals("nomade")) sMigrer += 10;
        if (h.perso.equals("prudente")) sFuir *= 1.5;
        double max = Math.max(Math.max(sSon, sManger), Math.max(Math.max(sNicher, sMigrer), sFuir));
        if (max == sSon && son != null) {
            h.objectif = "suivre_son";
            h.cx = son[0];
            h.cz = son[1];
        } else if (max == sManger) {
            h.objectif = "manger";
            h.cx = meilleureNourriture.cx;
            h.cz = meilleureNourriture.cz;
            if (meilleureNourriture == r && r.cadavres > 5) {
                double m = Math.min(r.cadavres, h.taille * 0.3);
                r.cadavres -= m;
                h.faim = Math.max(0, h.faim - m * 2);
            }
        } else if (max == sNicher) {
            h.objectif = "nicher";
            if (rng.nextDouble() < 0.01 && r.nids < maxNidsRegion && nidsTotal() < maxNidsMonde) {
                r.nids++;
                r.nidStade = Math.max(1, r.nidStade);
                publier(new Evenement("nid_ne").a(h.x, h.z).grav(3).dit("une horde fait son nid"));
            }
        } else if (max == sFuir) {
            h.objectif = "fuir";
            List<Region> vs = graphe.voisins(r.id);
            if (!vs.isEmpty()) {
                Region v = vs.get(rng.nextInt(vs.size()));
                h.cx = v.cx;
                h.cz = v.cz;
            }
        } else if (!h.objectif.equals("migrer") || Math.hypot(h.cx - h.x, h.cz - h.z) < 50) {
            h.objectif = "migrer";
            // le long des routes si possible, sinon vers un voisin
            List<Region> vs = graphe.voisins(r.id);
            Region v = vs.isEmpty() ? r : vs.get(rng.nextInt(vs.size()));
            if (!v.routes.isEmpty()) {
                double[] p = v.routes.get(rng.nextInt(v.routes.size()));
                h.cx = p[0];
                h.cz = p[1];
            } else {
                h.cx = v.cx + (rng.nextDouble() - 0.5) * 600;
                h.cz = v.cz + (rng.nextDouble() - 0.5) * 600;
            }
        }
    }

    private void bouger(Horde h, double secondes) {
        if (h.objectif.equals("hiberner") || h.reels > 0) return;   // matérialisée : c'est le monde réel qui la déplace
        double dx = h.cx - h.x, dz = h.cz - h.z;
        double d = Math.hypot(dx, dz);
        double pas = h.vitesse(saison, nuit) * secondes;
        if (d > 1) {
            double k = Math.min(1, pas / d);
            h.x += dx * k;
            h.z += dz * k;
        }
        h.x = Math.max(-graphe.limite + 10, Math.min(graphe.limite - 10, h.x));
        h.z = Math.max(-graphe.limite + 10, Math.min(graphe.limite - 10, h.z));
        String avant = h.region;
        h.region = graphe.regionId(h.x, h.z);
        Region r = graphe.regions.get(h.region);
        if (r == null) return;
        r.attentionZ = Math.min(100, r.attentionZ + h.taille / 40.0);
        if (!h.region.equals(avant)) {
            // elle emporte son génome (épidémiologie, IA-6)
            for (Map.Entry<String, Double> e : h.genome.entrySet())
                r.genome.merge(e.getKey(), e.getValue() * 0.05, (a, b) -> a * 0.95 + b);
            if (h.taille >= 40) publier(new Evenement("horde_passe").a(h.x, h.z).grav(h.mega ? 5 : 3).dit(h.nom.isEmpty() ? h.taille + " morts" : h.nom));
            // un camp ou un village sur la route
            for (String lid : r.lieux) {
                Graphe.Lieu l = graphe.lieux.get(lid);
                if (l != null && (l.type.equals("camp") || l.type.equals("village") || l.type.equals("refuge"))
                        && Math.hypot(l.x - h.x, l.z - h.z) < 250 && rng.nextDouble() < 0.4) {
                    Evenement e = new Evenement("horde_attaque_lieu").a(l.x, l.z).grav(4).dit(l.nom);
                    e.acteurs.add("lieu:" + l.id);
                    e.acteurs.add("horde:" + h.id);
                    publier(e);
                    h.proies.add(r.id);
                }
            }
        }
    }

    /** deux hordes qui se croisent fusionnent ; une horde trop grosse se divise ; rarement : une Mégahorde */
    private void fusionner() {
        for (int i = 0; i < hordes.size(); i++) {
            Horde a = hordes.get(i);
            for (int j = i + 1; j < hordes.size(); j++) {
                Horde b = hordes.get(j);
                if (a.reels > 0 || b.reels > 0) continue;
                if (Math.hypot(a.x - b.x, a.z - b.z) < 60) {
                    Horde fort = a.taille >= b.taille ? a : b, faible = fort == a ? b : a;
                    fort.taille += faible.taille;
                    fort.alpha |= faible.alpha;
                    faible.taille = 0;
                    if (fort.taille >= 200 && !fort.mega && megaActive() == 0 && jour - derniereMega >= 10 && rng.nextDouble() < 0.3) {
                        derniereMega = jour;
                        fort.mega = true;
                        Region r = graphe.regions.get(fort.region);
                        boolean autoroute = r != null && !r.routes.isEmpty();
                        fort.nom = autoroute ? "La Marée de la 40" : "La Marée de " + (r == null ? "nulle part" : r.nom);
                        publier(new Evenement("megahorde").a(fort.x, fort.z).grav(5).dit(fort.nom));
                    } else if (fort.taille >= 60 && fort.nom.isEmpty()) {
                        Region r = graphe.regions.get(fort.region);
                        fort.nom = "La Horde de " + (r == null ? "nulle part" : r.nom);
                    }
                }
            }
        }
        hordes.removeIf(h -> h.taille <= 0);
        List<Horde> nouvelles = new ArrayList<>();
        for (Horde h : hordes) {
            boolean trop = h.taille > 260 || (!h.alpha && h.taille > 80 && rng.nextDouble() < 0.02);
            if (trop && h.reels == 0 && hordes.size() + nouvelles.size() < maxHordes) {
                Horde f = new Horde(prochainId++);
                f.taille = h.taille / 2;
                h.taille -= f.taille;
                f.region = h.region;
                f.x = h.x + 40;
                f.z = h.z + 40;
                f.perso = h.perso;
                f.genome.putAll(h.genome);
                nouvelles.add(f);
                if (h.mega && h.taille < 200) h.mega = false;
            }
        }
        hordes.addAll(nouvelles);
    }

    // ================================================================ le jour passe

    public void tickJour() {
        jour++;
        int rouges = 0;
        for (Region r : graphe.regions.values()) {
            // cadavres -> nid (1, 25)
            r.cadavres *= 0.85;
            if (r.cadavres > 60 && r.contamination > 50 && r.nids < maxNidsRegion && nidsTotal() < maxNidsMonde && rng.nextDouble() < 0.15) {
                r.nids++;
                r.nidStade = Math.max(1, r.nidStade);
                publier(new Evenement("nid_ne").a(r.cx, r.cz).grav(3).dit("les cadavres ont nourri un nid"));
            }
            // les nids grandissent : germe -> foyer -> ruche -> matrice (une seule matrice par région)
            // un nid mal nourri dépérit ; un germe meurt seul
            if (r.nids > 0 && r.cadavres < 5 && !nuitLongue() && rng.nextDouble() < 0.06) {
                r.nidStade--;
                if (r.nidStade <= 0) {
                    r.nids--;
                    r.nidStade = r.nids > 0 ? 1 : 0;
                }
            }
            if (r.nids > 0 && r.nidStade < 4 && rng.nextDouble() < (r.courant ? 0.06 : 0.15) + Math.min(0.15, r.cadavres / 200)) {
                r.nidStade++;
                if (r.nidStade == 4) publier(new Evenement("matrice").a(r.cx, r.cz).grav(5).dit(r.nom));
            }
            // sources de contamination
            r.contamination += r.nids * 1.5 + r.nidStade * 0.5 + r.cadavres / 40;
            // freins naturels (80) : retour lent vers l'équilibre
            r.contamination += (equilibre - r.contamination) * 0.10;
            if (r.courant) r.contamination -= 1.5;
            if (r.calmeJusqua >= jour) r.contamination -= 2;
            r.contamination = clamp(r.contamination);
            // eau (85)
            r.eau = clamp(r.eau + (r.stationEau ? 10 : 2) - r.contamination * 0.05);
            // panique et moral se calment
            r.panique = clamp(r.panique * 0.8);
            r.moral = clamp(r.moral + (50 - r.moral) * 0.1);
            // végétation (115) : elle reprend là où personne ne passe ; grise près des nids
            r.vegetation = clamp(r.vegetation + (r.attentionZ < 10 ? 2 : -1));
            // population : on fuit le rouge (89)
            if (r.etat >= 3 && r.population > 5) {
                double part = Math.min(r.population, 3 + rng.nextInt(8));
                r.population -= part;
                Region dest = null;
                for (Region v : graphe.voisins(r.id)) if (dest == null || v.etat < dest.etat) dest = v;
                if (dest != null) {
                    dest.population += part;
                    Evenement e = new Evenement("colonne_refugies").a(r.cx, r.cz).grav(3).dit((int) part + " civils vers " + dest.nom);
                    e.acteurs.add("vers:" + dest.id);
                    publier(e);
                }
            }
            if (r.quarantaineJusqua >= 0 && r.quarantaineJusqua < jour) r.quarantaineJusqua = -1;
            calculerEtat(r);
            if (r.etat >= 3) rouges++;
            evoluer(r);
        }
        // diffusion par le graphe (18) : un peu vers les voisins, beaucoup vers l'aval de la rivière
        Map<String, Double> delta = new java.util.HashMap<>();
        for (Region r : graphe.regions.values()) {
            for (Region v : graphe.voisins(r.id))
                if (r.contamination > v.contamination) delta.merge(v.id, (r.contamination - v.contamination) * 0.02, Double::sum);
            Region a = graphe.aval(r.id);
            if (a != null && r.contamination > a.contamination) {
                delta.merge(a.id, (r.contamination - a.contamination) * 0.12, Double::sum);
                a.eau = clamp(a.eau - r.contamination * 0.05);
            }
        }
        for (Map.Entry<String, Double> e : delta.entrySet()) {
            Region r = graphe.regions.get(e.getKey());
            r.contamination = clamp(r.contamination + e.getValue());
        }
        // réaction immunitaire du monde (80) : trop de rouge -> l'armée, NORDA ou les factions frappent
        int total = graphe.regions.size();
        int frappes = rouges > total / 4 ? Math.min(3, 1 + (rouges - total / 4) / 5) : 0;
        for (int f = 0; f < frappes; f++) {
            Region pire = null;
            for (Region r : graphe.regions.values()) if (r.quarantaineJusqua < jour && (pire == null || r.contamination > pire.contamination)) pire = r;
            if (pire != null) {
                pire.contamination = clamp(pire.contamination - 40);
                pire.cadavres = 0;
                pire.nids = Math.max(0, pire.nids - 1);
                if (pire.nids == 0) pire.nidStade = 0;
                pire.quarantaineJusqua = jour + 3;
                pire.plaques.add("J" + jour + " : frappe incendiaire sur " + pire.nom);
                publier(new Evenement("frappe_incendiaire").a(pire.cx, pire.cz).grav(5).dit(pire.nom));
            }
        }
        // nouvelles hordes nées des nids
        for (Region r : graphe.regions.values()) {
            if (r.nids > 0 && rng.nextDouble() < 0.2 * r.nids) creerHorde(r, 8 + rng.nextInt(14) + r.nidStade * 3);
        }
        // les morts reviennent toujours : quelques hordes errantes naissent partout (plus dans les régions déjà touchées)
        for (Region r : graphe.regions.values()) {
            if (rng.nextDouble() < 0.015 + r.etat * 0.02) creerHorde(r, 6 + rng.nextInt(12));
            // un nid peut germer seul dans une région sale et sombre
            if (r.contamination > 35 && r.nids == 0 && !r.courant && nidsTotal() < maxNidsMonde && rng.nextDouble() < 0.05) {
                r.nids = 1;
                r.nidStade = 1;
                publier(new Evenement("nid_ne").a(r.cx, r.cz).grav(3).dit("un germe dans le noir"));
            }
        }
        // une Mégahorde s'use : elle se disperse peu à peu
        for (Horde h : hordes) if (h.mega) h.taille = (int) (h.taille * 0.93);
        // habitudes qui s'effacent
        for (Region r : graphe.regions.values()) {
            for (Map.Entry<String, Double> e : r.habitudes.entrySet()) e.setValue(e.getValue() * 0.8);
            r.succes.clear();
            r.pertes.clear();
        }
    }

    private boolean nuitLongue() {
        return "hiver".equals(saison);
    }

    public int nidsTotal() {
        int n = 0;
        for (Region r : graphe.regions.values()) n += r.nids;
        return n;
    }

    public int megaActive() {
        int n = 0;
        for (Horde h : hordes) if (h.mega) n++;
        return n;
    }

    public void calculerEtat(Region r) {
        double s = r.contamination * 0.5 + Math.min(60, r.cadavres) * 0.2 + r.nids * 10 + r.nidStade * 6 + r.attentionZ * 0.15;
        int e;
        if (s < 20) e = 0;
        else if (s < 35) e = 1;
        else if (s < 50) e = 2;
        else if (s < 70) e = 3;
        else e = 4;
        if (e != r.etat) {
            int avant = r.etat;
            r.etat = e;
            if (e == 4 && avant < 4) {
                r.plaques.add("Chute de " + r.nom + " — Jour " + jour);
                publier(new Evenement("region_perdue").a(r.cx, r.cz).grav(5).dit(r.nom));
            } else if (e <= 1 && avant >= 3) {
                publier(new Evenement("region_reprise").a(r.cx, r.cz).grav(4).dit(r.nom));
            }
        }
    }

    /** sélection naturelle et pression des habitudes (IA-6) */
    private void evoluer(Region r) {
        // les types qui ont fait des dégâts gagnent du poids, ceux qui meurent vite en perdent
        for (String t : Region.TYPES) {
            double s = r.succes.getOrDefault(t, 0.0), p = r.pertes.getOrDefault(t, 0.0);
            double w = r.genome.getOrDefault(t, 1.0);
            w += (s - p * 0.3) * 0.05;
            w += (Region.base(t) - w) * 0.05;     // mémoire qui s'efface
            r.genome.put(t, Math.max(0.5, Math.min(60, w)));
        }
        // réponses aux habitudes (tableau d'IA-6) ; toujours une réponse, jamais un mur
        double puis = 0;
        puis += pousser(r, "armes_feu", "ZA_Screamer", null, 3);
        puis += pousser(r, "melee", "ZA_Armored", "blinde", 3);
        puis += pousser(r, "melee", "ZA_Bloater", null, 2);
        puis += pousser(r, "lumiere", "ZA_Phototrope", null, 3);
        puis += pousser(r, "toits", "ZA_Leaper", "grimpeur", 3);
        puis += pousser(r, "toits", "ZA_Spitter", null, 2);
        puis += pousser(r, "feu", null, "carbonise", 3);
        puis += pousser(r, "barricades", "ZA_Brute", null, 3);
        puis += pousser(r, "routes", "ZA_FakeDead", null, 3);
        puis += pousser(r, "leurres", null, "sourd_aux_leurres", 3);
        if (r.habitudes.getOrDefault("farm", 0.0) > 20) {
            r.interdictionFarm = jour + 1;
            r.traits.merge("evite_pieges", 10.0, Double::sum);
        }
        // traits qui s'effacent
        for (Map.Entry<String, Double> e : r.traits.entrySet()) e.setValue(Math.max(0, e.getValue() * 0.9));
        r.puissance = puis;
        // arbre de mutations : un trait qui dépasse le seuil fait naître une variante
        for (Map.Entry<String, Double> e : r.traits.entrySet()) {
            if (e.getValue() >= 80 && rng.nextDouble() < 0.2) {
                Evenement ev = new Evenement("mutation").a(r.cx, r.cz).grav(4).dit(e.getKey());
                ev.acteurs.add("trait:" + e.getKey());
                publier(ev);
                e.setValue(40.0);
            }
        }
        // une région nettoyée perd ses mutations (80)
        if (r.etat == 0 && r.nettoyeeJour >= jour - 3) {
            for (Map.Entry<String, Double> e : r.traits.entrySet()) e.setValue(e.getValue() * 0.5);
        }
    }

    private double pousser(Region r, String habitude, String type, String trait, double k) {
        double h = r.habitudes.getOrDefault(habitude, 0.0);
        if (h < 5) return 0;
        double gain = Math.min(10, h / 10 * k);
        if (r.puissance > maxPuissance) gain *= 0.2;   // plafond de puissance par région
        if (type != null) r.genome.merge(type, gain, Double::sum);
        if (trait != null) r.traits.merge(trait, gain * 2, Double::sum);
        return gain;
    }

    // ================================================================ résumé

    public String carteEtats() {
        StringBuilder b = new StringBuilder();
        for (int j = 0; j < graphe.n; j++) {
            for (int i = 0; i < graphe.n; i++) {
                Region r = graphe.regions.get("r_" + i + "_" + j);
                b.append(r == null ? '?' : "SCDRP".charAt(r.etat));
            }
            b.append('\n');
        }
        return b.toString();
    }

    public int[] compteEtats() {
        int[] c = new int[5];
        for (Region r : graphe.regions.values()) c[r.etat]++;
        return c;
    }
}
