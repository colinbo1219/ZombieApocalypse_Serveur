package za.moteur;

import org.bukkit.Location;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Player;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Region;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * Télémétrie et équilibrage (bible F5) : le serveur note tout, sort un rapport quotidien, repère les systèmes qui ne se
 * déclenchent jamais et les exploits (farm de zombies, pilier, AFK). Le réglage automatique reste borné ; tout
 * changement plus gros attend la validation de Colin.
 */
public final class Telemetrie {
    private final ZAMoteur z;
    public final Map<String, Integer> morts = new TreeMap<>();           // cause -> nombre
    public final Map<String, Integer> mortsRegion = new TreeMap<>();
    public final Map<String, Integer> killsArme = new TreeMap<>();
    public final Map<String, Integer> killsType = new TreeMap<>();
    public final Map<String, Integer> evenements = new TreeMap<>();
    public final Map<String, Integer> tempsRegion = new TreeMap<>();    // région -> minutes de joueur
    private final Map<Long, Integer> tuerieCase = new HashMap<>();       // case 16x16 -> morts dans la fenêtre
    private long fenetre = System.currentTimeMillis();
    public final List<String> suspects = new ArrayList<>();
    private final Map<String, Long> immobiles = new HashMap<>();
    private final Map<String, Location> dernierePos = new HashMap<>();
    /** refuges improvisés (67) : case de 16 x 16 -> minutes passées à l'abri hors de toute base enregistrée */
    public final Map<Long, Double> refuges = new HashMap<>();
    private final Map<String, Long> refugeAvis = new HashMap<>();
    public final List<String> dernierRapport = new ArrayList<>();
    private static final String[] SYSTEMES = {"horde_attaque_lieu", "colonne_refugies", "nid_ne", "megahorde", "nemesis_nee",
            "nemesis_vaincue", "region_perdue", "region_reprise", "quarantaine", "frappe_incendiaire", "mutation", "labo_detruit",
            "drone_abattu", "norda_drone", "norda_barrage", "norda_capture", "lea_silence", "legende_locale", "grande_nuit"};

    Telemetrie(ZAMoteur z) {
        this.z = z;
    }

    synchronized void evenement(Evenement e) {
        evenements.merge(e.type, 1, Integer::sum);
    }

    public synchronized void mortJoueur(String cause, String region) {
        morts.merge(cause, 1, Integer::sum);
        mortsRegion.merge(region, 1, Integer::sum);
    }

    /** un zombie tué : par quelle arme, quel type, et où (pour repérer les farms) */
    public synchronized void kill(String arme, String type, Location l) {
        killsArme.merge(arme, 1, Integer::sum);
        killsType.merge(type, 1, Integer::sum);
        long now = System.currentTimeMillis();
        if (now - fenetre > 10 * 60_000L) {
            tuerieCase.clear();
            fenetre = now;
        }
        long c = (((long) (l.getBlockX() >> 4)) << 32) ^ ((l.getBlockZ() >> 4) & 0xffffffffL);
        int n = tuerieCase.merge(c, 1, Integer::sum);
        if (n == 40) {
            String s = "J" + z.jour() + " : 40 morts en 10 min sur la case " + l.getBlockX() + ", " + l.getBlockZ() + " (piège à zombies ?)";
            suspects.add(s);
            synchronized (z.monde) {
                Region r = z.monde.graphe.region(l.getX(), l.getZ());
                if (r != null) r.habitudes.merge("farm", 25.0, Double::sum);
            }
        }
    }

    /** toutes les 30 s (depuis Ecosysteme.tick30s) : temps par zone, AFK, habitudes de joueurs */
    synchronized void echantillon(Player p) {
        Location l = p.getLocation();
        Region r;
        synchronized (z.monde) {
            r = z.monde.graphe.region(l.getX(), l.getZ());
        }
        if (r == null) return;
        tempsRegion.merge(r.id, 1, Integer::sum);
        String u = p.getUniqueId().toString();
        Location d = dernierePos.put(u, l);
        if (d != null && d.getWorld() == l.getWorld() && d.distanceSquared(l) < 1) {
            long t = immobiles.merge(u, 30_000L, Long::sum);
            if (t == 30 * 60_000L) suspects.add("J" + z.jour() + " : " + p.getName() + " immobile depuis 30 min à " + l.getBlockX() + ", " + l.getBlockZ() + " (AFK ?)");
        } else immobiles.remove(u);
        // habitudes (IA-6) : camper sur les toits, la lumière forte, les mêmes routes
        int sol = l.getWorld().getHighestBlockYAt(l);
        // à l'abri (toit au-dessus) et loin de toute base : un refuge improvisé que les morts finiront par connaître
        if (sol > l.getBlockY() + 1 && !z.mat.presBase(l, 60)) {
            long c = (((long) (l.getBlockX() >> 4)) << 32) ^ ((l.getBlockZ() >> 4) & 0xffffffffL);
            double m = refuges.merge(c, 0.5, Double::sum);
            String cle = u + c;
            long now = System.currentTimeMillis();
            Long av = refugeAvis.get(cle);
            if (m >= 60 && (av == null || now - av > 10 * 60_000L)) {
                refugeAvis.put(cle, now);
                if (m < 90) z.pont.zaevt("refuge_signe " + u);
                else z.pont.zaevt("refuge_embuscade " + u);
                if (m >= 150) z.publier(new za.moteur.coeur.Evenement("refuge_connu").a(l.getX(), l.getZ()).grav(2).acteur(u));
            }
        }
        synchronized (z.monde) {
            if (l.getBlockY() >= sol && l.getBlock().getRelative(0, -1, 0).getType().isSolid() && l.getBlockY() - l.getWorld().getHighestBlockYAt(l.getBlockX() + 3, l.getBlockZ() + 3) > 5)
                r.habitudes.merge("toits", 1.0, Double::sum);
            if (z.estNuit() && l.getBlock().getLightLevel() > 12) r.habitudes.merge("lumiere", 0.5, Double::sum);
            if (!r.routes.isEmpty()) {
                for (double[] q : r.routes) {
                    if (Math.hypot(q[0] - l.getX(), q[1] - l.getZ()) < 20) {
                        r.habitudes.merge("routes", 0.3, Double::sum);
                        break;
                    }
                }
            }
        }
    }

    /** le rapport quotidien (/zaadmin rapport, et un fichier par jour) */
    synchronized void jour() {
        dernierRapport.clear();
        dernierRapport.add("=== Rapport du jour " + z.jour() + " ===");
        dernierRapport.add("Morts de joueurs par cause : " + morts);
        dernierRapport.add("Zones les plus mortelles : " + top(mortsRegion, 5));
        dernierRapport.add("Morts abattus par arme : " + killsArme);
        dernierRapport.add("Types abattus : " + top(killsType, 8));
        dernierRapport.add("Zones les plus fréquentées : " + top(tempsRegion, 6));
        List<String> jamais = new ArrayList<>();
        for (String s : SYSTEMES) if (!evenements.containsKey(s)) jamais.add(s);
        dernierRapport.add("Systèmes jamais déclenchés (lisibilité ou bogue ?) : " + (jamais.isEmpty() ? "aucun" : jamais));
        dernierRapport.add("Exploits suspects : " + (suspects.isEmpty() ? "aucun" : ""));
        for (int i = Math.max(0, suspects.size() - 10); i < suspects.size(); i++) dernierRapport.add("  " + suspects.get(i));
        Map<String, Object> s = z.resumeSystemes();
        dernierRapport.add("Moteur : " + s);
        try {
            File d = new File(z.getDataFolder(), "rapports");
            d.mkdirs();
            Files.write(new File(d, "jour-" + z.jour() + ".txt").toPath(), dernierRapport, StandardCharsets.UTF_8);
        } catch (Exception e) {
            ZAMoteur.log().warning("Rapport : " + e.getMessage());
        }
        // les morts oublient lentement un refuge qu'on n'utilise plus
        refuges.replaceAll((k, v) -> v * 0.85);
        refuges.values().removeIf(v -> v < 5);
        // la journée suivante repart à zéro (le fichier garde l'historique)
        morts.clear();
        mortsRegion.clear();
        killsArme.clear();
        killsType.clear();
        tempsRegion.clear();
        suspects.clear();
    }

    private static String top(Map<String, Integer> m, int n) {
        List<Map.Entry<String, Integer>> l = new ArrayList<>(m.entrySet());
        l.sort((a, b) -> b.getValue() - a.getValue());
        Map<String, Integer> r = new LinkedHashMap<>();
        for (int i = 0; i < Math.min(n, l.size()); i++) r.put(l.get(i).getKey(), l.get(i).getValue());
        return r.toString();
    }

    synchronized void sauver(ConfigurationSection s) {
        for (Map.Entry<String, Integer> e : evenements.entrySet()) s.set("evenements." + e.getKey(), e.getValue());
    }

    synchronized void charger(ConfigurationSection s) {
        if (s == null) return;
        ConfigurationSection e = s.getConfigurationSection("evenements");
        if (e != null) for (String k : e.getKeys(false)) evenements.put(k, e.getInt(k));
    }
}
