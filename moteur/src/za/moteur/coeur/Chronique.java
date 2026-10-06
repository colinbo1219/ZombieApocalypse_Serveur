package za.moteur.coeur;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

/**
 * La Chronique (bible F2) : une seule file d'événements, que tous les systèmes publient et écoutent.
 * Elle garde la vérité. Chaque entrée a une importance (0-100) qui décide de sa durée de vie : les petits faits sont
 * compressés en résumés (« 41 morts abattus — r_3_4 — Jour 73 »), les grands restent entiers (historique, légendaire).
 */
public final class Chronique {
    private final List<Evenement> recents = new ArrayList<>();
    private final List<Evenement> historiques = new ArrayList<>();
    private final Map<String, Integer> resumes = new LinkedHashMap<>();
    private final List<Consumer<Evenement>> ecouteurs = new ArrayList<>();
    public int max = 3000, maxHistoriques = 2500;
    public long total;

    /** importance de départ par type (F2) ; sinon selon la gravité */
    private static final Map<String, Integer> IMPORTANCE = new HashMap<>();

    static {
        IMPORTANCE.put("mort_zombie", 1);
        IMPORTANCE.put("tir", 2);
        IMPORTANCE.put("survivant_sauve", 15);
        IMPORTANCE.put("mort_joueur", 20);
        IMPORTANCE.put("nid_detruit", 30);
        IMPORTANCE.put("convoi_detruit", 35);
        IMPORTANCE.put("horde_attaque_lieu", 40);
        IMPORTANCE.put("nemesis_nee", 45);
        IMPORTANCE.put("nemesis_vaincue", 60);
        IMPORTANCE.put("base_perdue", 60);
        IMPORTANCE.put("region_perdue", 65);
        IMPORTANCE.put("region_reprise", 70);
        IMPORTANCE.put("megahorde", 70);
        IMPORTANCE.put("boss_tue", 80);
        IMPORTANCE.put("barrage_cede", 85);
        IMPORTANCE.put("ville_tombee", 90);
        IMPORTANCE.put("labo_detruit", 100);
    }

    public static int importanceDe(Evenement e) {
        Integer i = IMPORTANCE.get(e.type);
        if (i != null) return i;
        return new int[]{0, 3, 10, 25, 45, 70}[Math.max(1, Math.min(5, e.gravite))];
    }

    /** instantanee (minutes) | recente (jours) | historique (semaines) | legendaire (saison) */
    public static String duree(Evenement e) {
        if (e.importance >= 80) return "legendaire";
        if (e.importance >= 40) return "historique";
        if (e.importance >= 10) return "recente";
        return "instantanee";
    }

    public synchronized void ecouter(Consumer<Evenement> c) {
        ecouteurs.add(c);
    }

    public void publier(Evenement e) {
        if (e.importance < 0) e.importance = importanceDe(e);
        List<Consumer<Evenement>> ec;
        synchronized (this) {
            recents.add(e);
            total++;
            while (recents.size() > max) oublier(recents.remove(0));
            ec = new ArrayList<>(ecouteurs);
        }
        for (Consumer<Evenement> c : ec) {
            try {
                c.accept(e);
            } catch (RuntimeException ex) {
                // un écouteur qui plante ne doit jamais casser la chaîne
            }
        }
    }

    /** un vieil événement sort de la file récente : gardé entier s'il compte, sinon résumé */
    private void oublier(Evenement e) {
        if (e.importance >= 40) {
            historiques.add(e);
            while (historiques.size() > maxHistoriques) {
                // on garde toujours les légendaires
                int k = 0;
                while (k < historiques.size() - 1 && historiques.get(k).importance >= 80) k++;
                Evenement v = historiques.remove(k);
                resumer(v);
            }
        } else resumer(e);
    }

    private void resumer(Evenement e) {
        String cle = e.jour + "|" + (e.region == null ? "?" : e.region) + "|" + e.type;
        resumes.merge(cle, 1, Integer::sum);
        while (resumes.size() > 5000) resumes.remove(resumes.keySet().iterator().next());
    }

    public synchronized List<String> resumes(String region, int n) {
        List<String> r = new ArrayList<>();
        List<String> cles = new ArrayList<>(resumes.keySet());
        for (int i = cles.size() - 1; i >= 0 && r.size() < n; i--) {
            String[] c = cles.get(i).split("\\|");
            if (region != null && !region.equals(c[1])) continue;
            r.add("Jour " + c[0] + " : " + resumes.get(cles.get(i)) + " × " + c[2] + " (" + c[1] + ")");
        }
        return r;
    }

    public synchronized List<Evenement> derniers(int n) {
        int a = Math.max(0, recents.size() - n);
        return new ArrayList<>(recents.subList(a, recents.size()));
    }

    public synchronized List<Evenement> legendaires() {
        List<Evenement> r = new ArrayList<>();
        for (Evenement e : historiques) if (e.importance >= 80) r.add(e);
        for (Evenement e : recents) if (e.importance >= 80) r.add(e);
        return r;
    }

    public synchronized List<Evenement> parRegion(String region, int n) {
        List<Evenement> r = new ArrayList<>();
        for (int i = recents.size() - 1; i >= 0 && r.size() < n; i--) if (region.equals(recents.get(i).region)) r.add(recents.get(i));
        for (int i = historiques.size() - 1; i >= 0 && r.size() < n; i--) if (region.equals(historiques.get(i).region)) r.add(historiques.get(i));
        return r;
    }

    public synchronized List<Evenement> parActeur(String acteur, int n) {
        List<Evenement> r = new ArrayList<>();
        for (int i = recents.size() - 1; i >= 0 && r.size() < n; i--) if (recents.get(i).acteurs.contains(acteur)) r.add(recents.get(i));
        for (int i = historiques.size() - 1; i >= 0 && r.size() < n; i--) if (historiques.get(i).acteurs.contains(acteur)) r.add(historiques.get(i));
        return r;
    }

    public synchronized Evenement parId(long id) {
        for (int i = recents.size() - 1; i >= 0; i--) if (recents.get(i).id == id) return recents.get(i);
        for (int i = historiques.size() - 1; i >= 0; i--) if (historiques.get(i).id == id) return historiques.get(i);
        return null;
    }

    public synchronized List<Evenement> nonDiffuses(int jourMin) {
        List<Evenement> r = new ArrayList<>();
        for (Evenement e : recents) if (!e.diffuse && e.jour >= jourMin) r.add(e);
        return r;
    }

    public synchronized int compte(String type, int depuisJour) {
        int n = 0;
        for (Evenement e : recents) if (e.type.equals(type) && e.jour >= depuisJour) n++;
        return n;
    }

    // ---------------------------------------------------------------- sauvegarde : seulement l'historique (le récent se reconstruit)

    public synchronized List<String> exporter() {
        List<String> l = new ArrayList<>();
        List<Evenement> tous = new ArrayList<>(historiques);
        for (Evenement e : recents) if (e.importance >= 40) tous.add(e);
        for (Evenement e : tous)
            l.add(e.jour + "\t" + e.type + "\t" + (e.region == null ? "" : e.region) + "\t" + (int) e.x + "\t" + (int) e.z + "\t" + e.gravite
                    + "\t" + e.importance + "\t" + e.verite + "\t" + String.join(",", e.acteurs) + "\t" + e.texte.replace('\t', ' ')
                    + "\t" + e.secret.replace('\t', ' ') + "\t" + String.join(",", e.savent));
        for (Map.Entry<String, Integer> r : resumes.entrySet()) l.add("#" + r.getKey() + "\t" + r.getValue());
        return l;
    }

    public synchronized void importer(List<String> l) {
        for (String s : l) {
            String[] c = s.split("\t", -1);
            if (s.startsWith("#")) {
                if (c.length == 2) resumes.put(c[0].substring(1), Integer.parseInt(c[1]));
                continue;
            }
            if (c.length < 10) continue;
            try {
                Evenement e = new Evenement(c[1]).a(Double.parseDouble(c[3]), Double.parseDouble(c[4])).grav(Integer.parseInt(c[5])).imp(Integer.parseInt(c[6])).dit(c[9]);
                e.jour = Integer.parseInt(c[0]);
                e.region = c[2].isEmpty() ? null : c[2];
                e.verite = c[7];
                e.diffuse = true;
                if (!c[8].isEmpty()) for (String a : c[8].split(",")) e.acteur(a);
                if (c.length > 11) {
                    e.secret = c[10];
                    if (!c[11].isEmpty()) for (String q : c[11].split(",")) e.savent.add(q);
                }
                historiques.add(e);
            } catch (RuntimeException ignored) {
                // ligne abîmée : on passe
            }
        }
    }
}
