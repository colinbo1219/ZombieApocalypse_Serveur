package za.moteur;

import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import za.moteur.coeur.Horde;
import za.moteur.coeur.Norda;
import za.moteur.coeur.Region;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Sauvegarde du moteur (F1) : plugins/ZAMoteur/etat.yml, copiée chaque jour (etat-jourN.yml, 7 gardées).
 * Le moteur garde ses propres données ; les variables Skript restent dans Skript.
 */
public final class Persistance {
    private final ZAMoteur z;
    private final File fichier;
    private YamlConfiguration y;
    private int dernierJourCopie = -1;

    Persistance(ZAMoteur z) {
        this.z = z;
        this.fichier = new File(z.getDataFolder(), "etat.yml");
    }

    void charger() {
        y = YamlConfiguration.loadConfiguration(fichier);
        z.monde.jour = y.getInt("jour", 0);
        z.monde.saison = y.getString("saison", "ete");
        z.monde.derniereMega = y.getInt("derniere_mega", -99);
        ConfigurationSection rs = y.getConfigurationSection("regions");
        if (rs != null) {
            for (String id : rs.getKeys(false)) {
                Region r = z.monde.graphe.regions.get(id);
                ConfigurationSection s = rs.getConfigurationSection(id);
                if (r == null || s == null) continue;
                r.contamination = s.getDouble("contamination", r.contamination);
                r.cadavres = s.getDouble("cadavres");
                r.nids = s.getInt("nids");
                r.nidStade = s.getInt("nid_stade");
                r.securite = s.getDouble("securite", r.securite);
                r.moral = s.getDouble("moral", r.moral);
                r.panique = s.getDouble("panique", r.panique);
                r.population = s.getDouble("population", r.population);
                r.eau = s.getDouble("eau", r.eau);
                r.vegetation = s.getDouble("vegetation", r.vegetation);
                r.courant = s.getBoolean("courant");
                r.stationEau = s.getBoolean("station_eau");
                r.meteo = s.getBoolean("meteo");
                r.tours = s.getInt("tours");
                r.repeteurs = s.getInt("repeteurs");
                r.faction = s.getString("faction", "");
                r.etat = s.getInt("etat");
                r.calmeJusqua = s.getInt("calme");
                r.nettoyeeJour = s.getInt("nettoyee", -1);
                r.quarantaineJusqua = s.getInt("quarantaine", -1);
                r.attentionN = s.getDouble("attention_norda");
                r.plaques.addAll(s.getStringList("plaques"));
                r.historique.addAll(s.getStringList("historique"));
                lireCarte(s.getConfigurationSection("genome"), r.genome);
                lireCarte(s.getConfigurationSection("traits"), r.traits);
                lireCarte(s.getConfigurationSection("habitudes"), r.habitudes);
            }
        }
        ConfigurationSection hs = y.getConfigurationSection("hordes");
        if (hs != null) {
            for (String k : hs.getKeys(false)) {
                ConfigurationSection s = hs.getConfigurationSection(k);
                if (s == null) continue;
                Region r = z.monde.graphe.regions.get(s.getString("region", ""));
                Horde h = z.monde.creerHorde(r != null ? r : z.monde.graphe.regions.values().iterator().next(), s.getInt("taille", 10));
                if (h == null) continue;
                h.nom = s.getString("nom", "");
                h.x = s.getDouble("x");
                h.z = s.getDouble("z");
                h.cx = h.x;
                h.cz = h.z;
                h.objectif = s.getString("objectif", "errer");
                h.moral = s.getDouble("moral", 100);
                h.alpha = s.getBoolean("alpha");
                h.mega = s.getBoolean("mega");
                h.perso = s.getString("perso", "nomade");
                h.region = z.monde.graphe.regionId(h.x, h.z);
                lireCarte(s.getConfigurationSection("genome"), h.genome);
            }
        }
        ConfigurationSection ns = y.getConfigurationSection("norda");
        if (ns != null) {
            for (String k : ns.getKeys(false)) {
                ConfigurationSection s = ns.getConfigurationSection(k);
                if (s == null) continue;
                Norda.Dossier d = z.norda.dossier(k.replace('_', ':').replace("faction:", "faction:"));
                d.nom = s.getString("nom", "");
                d.soupcon = s.getDouble("soupcon");
                d.certitude = s.getDouble("certitude");
                d.identiteSupposee = s.getString("identite", "");
                d.affiliationSupposee = s.getString("affiliation", "");
                d.posX = s.getDouble("x");
                d.posZ = s.getDouble("z");
                d.rayon = s.getDouble("rayon", 99999);
                d.posJour = s.getInt("pos_jour", -1);
                d.palier = s.getInt("palier");
                d.tromperies = s.getInt("tromperies");
                d.preuves.addAll(s.getStringList("preuves"));
                d.croyances.addAll(s.getStringList("croyances"));
                ConfigurationSection ro = s.getConfigurationSection("routes");
                if (ro != null) for (String rk : ro.getKeys(false)) d.routes.put(rk, ro.getInt(rk));
            }
        }
        z.monde.chronique.importer(lire("chronique.txt"));
        z.monde.info.importer(lire("informations.txt"));
        z.monde.memoire.importer(lire("memoire.txt"));
        // au premier démarrage : quelques hordes et Saint-Aurèle contaminée
        if (z.monde.hordes.isEmpty() && !y.contains("jour")) {
            Region sa = z.monde.graphe.region(0, 0);
            if (sa != null) {
                sa.contamination = 55;
                sa.nids = 1;
                sa.nidStade = 2;
            }
            List<Region> l = new ArrayList<>(z.monde.graphe.regions.values());
            for (int i = 0; i < 8; i++) z.monde.creerHorde(l.get(z.monde.rng.nextInt(l.size())), 12 + z.monde.rng.nextInt(25));
        }
    }

    /** après la création des modules */
    void chargerModules() {
        z.nemesis.charger(y.getConfigurationSection("nemesis"));
        z.telemetrie.charger(y.getConfigurationSection("telemetrie"));
        z.directeur.charger(y.getConfigurationSection("directeur"));
        z.lea.charger(y.getConfigurationSection("lea"));
        z.vivantes.cerveau.importer(lire("bases.txt"));
        z.societe.cerveau.importer(lire("factions.txt"));
    }

    private static void lireCarte(ConfigurationSection s, Map<String, Double> m) {
        if (s == null) return;
        for (String k : s.getKeys(false)) m.put(k, s.getDouble(k));
    }

    public synchronized void sauver() {
        YamlConfiguration o = new YamlConfiguration();
        synchronized (z.monde) {
            o.set("jour", z.monde.jour);
            o.set("saison", z.monde.saison);
            o.set("derniere_mega", z.monde.derniereMega);
            for (Region r : z.monde.graphe.regions.values()) {
                String p = "regions." + r.id + ".";
                o.set(p + "contamination", arr(r.contamination));
                o.set(p + "cadavres", arr(r.cadavres));
                o.set(p + "nids", r.nids);
                o.set(p + "nid_stade", r.nidStade);
                o.set(p + "securite", arr(r.securite));
                o.set(p + "moral", arr(r.moral));
                o.set(p + "panique", arr(r.panique));
                o.set(p + "population", arr(r.population));
                o.set(p + "eau", arr(r.eau));
                o.set(p + "vegetation", arr(r.vegetation));
                o.set(p + "courant", r.courant);
                o.set(p + "station_eau", r.stationEau);
                o.set(p + "meteo", r.meteo);
                o.set(p + "tours", r.tours);
                o.set(p + "repeteurs", r.repeteurs);
                o.set(p + "faction", r.faction);
                o.set(p + "etat", r.etat);
                o.set(p + "calme", r.calmeJusqua);
                o.set(p + "nettoyee", r.nettoyeeJour);
                o.set(p + "quarantaine", r.quarantaineJusqua);
                o.set(p + "attention_norda", arr(r.attentionN));
                o.set(p + "plaques", r.plaques);
                o.set(p + "historique", r.historique);
                for (Map.Entry<String, Double> e : r.genome.entrySet()) o.set(p + "genome." + e.getKey(), arr(e.getValue()));
                for (Map.Entry<String, Double> e : r.traits.entrySet()) o.set(p + "traits." + e.getKey(), arr(e.getValue()));
                for (Map.Entry<String, Double> e : r.habitudes.entrySet()) o.set(p + "habitudes." + e.getKey(), arr(e.getValue()));
            }
            for (Horde h : z.monde.hordes) {
                String p = "hordes.h" + h.id + ".";
                o.set(p + "taille", h.taille);   // taille compte déjà les membres réels (audit N3)
                o.set(p + "nom", h.nom);
                o.set(p + "x", arr(h.x));
                o.set(p + "z", arr(h.z));
                o.set(p + "region", h.region);
                o.set(p + "objectif", h.objectif);
                o.set(p + "moral", arr(h.moral));
                o.set(p + "alpha", h.alpha);
                o.set(p + "mega", h.mega);
                o.set(p + "perso", h.perso);
                for (Map.Entry<String, Double> e : h.genome.entrySet()) o.set(p + "genome." + e.getKey(), arr(e.getValue()));
            }
            for (Norda.Dossier d : z.norda.dossiers.values()) {
                String p = "norda." + d.cle.replace(':', '_') + ".";
                o.set(p + "nom", d.nom);
                o.set(p + "soupcon", arr(d.soupcon));
                o.set(p + "certitude", arr(d.certitude));
                o.set(p + "identite", d.identiteSupposee);
                o.set(p + "affiliation", d.affiliationSupposee);
                o.set(p + "x", (int) d.posX);
                o.set(p + "z", (int) d.posZ);
                o.set(p + "rayon", (int) d.rayon);
                o.set(p + "pos_jour", d.posJour);
                o.set(p + "palier", d.palier);
                o.set(p + "tromperies", d.tromperies);
                o.set(p + "preuves", d.preuves);
                o.set(p + "croyances", d.croyances);
                for (Map.Entry<String, Integer> e : d.routes.entrySet()) o.set(p + "routes." + e.getKey(), e.getValue());
            }
        }
        z.nemesis.sauver(o.createSection("nemesis"));
        z.telemetrie.sauver(o.createSection("telemetrie"));
        z.directeur.sauver(o.createSection("directeur"));
        z.lea.sauver(o.createSection("lea"));
        // Chronique historique, informations et mémoire : fichiers texte à part (F2, F9, F10)
        List<String> chron, infos, mem;
        synchronized (z.monde) {
            chron = z.monde.chronique.exporter();
            infos = z.monde.info.exporter();
            mem = z.monde.memoire.exporter();
        }
        ecrire("chronique.txt", chron);
        ecrire("informations.txt", infos);
        ecrire("memoire.txt", mem);
        ecrire("bases.txt", z.vivantes.cerveau.exporter());
        ecrire("factions.txt", z.societe.cerveau.exporter());
        try {
            File tmp = new File(z.getDataFolder(), "etat.yml.tmp");
            o.save(tmp);
            Files.move(tmp.toPath(), fichier.toPath(), StandardCopyOption.REPLACE_EXISTING);
            if (z.monde.jour != dernierJourCopie) {
                dernierJourCopie = z.monde.jour;
                Files.copy(fichier.toPath(), new File(z.getDataFolder(), "etat-jour" + (z.monde.jour % 7) + ".yml").toPath(), StandardCopyOption.REPLACE_EXISTING);
            }
            y = o;
        } catch (Exception e) {
            ZAMoteur.log().warning("Sauvegarde impossible : " + e.getMessage());
        }
    }

    private void ecrire(String nom, List<String> l) {
        try {
            File tmp = new File(z.getDataFolder(), nom + ".tmp");
            Files.write(tmp.toPath(), l, java.nio.charset.StandardCharsets.UTF_8);
            Files.move(tmp.toPath(), new File(z.getDataFolder(), nom).toPath(), StandardCopyOption.REPLACE_EXISTING);
        } catch (Exception e) {
            ZAMoteur.log().warning("Sauvegarde de " + nom + " impossible : " + e.getMessage());
        }
    }

    private List<String> lire(String nom) {
        File f = new File(z.getDataFolder(), nom);
        if (!f.exists()) return new ArrayList<>();
        try {
            return Files.readAllLines(f.toPath(), java.nio.charset.StandardCharsets.UTF_8);
        } catch (Exception e) {
            ZAMoteur.log().warning("Lecture de " + nom + " impossible : " + e.getMessage());
            return new ArrayList<>();
        }
    }

    private static double arr(double v) {
        return Math.round(v * 100) / 100.0;
    }
}
