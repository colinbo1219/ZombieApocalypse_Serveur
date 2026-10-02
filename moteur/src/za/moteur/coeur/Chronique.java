package za.moteur.coeur;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/** La Chronique (bible F2) : une seule file d'événements, que tous les systèmes publient et écoutent. */
public final class Chronique {
    private final List<Evenement> recents = new ArrayList<>();
    private final List<Consumer<Evenement>> ecouteurs = new ArrayList<>();
    public int max = 3000;
    public long total;

    public synchronized void ecouter(Consumer<Evenement> c) {
        ecouteurs.add(c);
    }

    public void publier(Evenement e) {
        List<Consumer<Evenement>> ec;
        synchronized (this) {
            recents.add(e);
            total++;
            while (recents.size() > max) recents.remove(0);
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

    public synchronized List<Evenement> derniers(int n) {
        int a = Math.max(0, recents.size() - n);
        return new ArrayList<>(recents.subList(a, recents.size()));
    }

    public synchronized List<Evenement> parRegion(String region, int n) {
        List<Evenement> r = new ArrayList<>();
        for (int i = recents.size() - 1; i >= 0 && r.size() < n; i--) if (region.equals(recents.get(i).region)) r.add(recents.get(i));
        return r;
    }

    public synchronized List<Evenement> parActeur(String acteur, int n) {
        List<Evenement> r = new ArrayList<>();
        for (int i = recents.size() - 1; i >= 0 && r.size() < n; i--) if (recents.get(i).acteurs.contains(acteur)) r.add(recents.get(i));
        return r;
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
}
