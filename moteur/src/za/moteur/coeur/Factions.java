package za.moteur.coeur;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Les factions qui jouent (bible IA-10) et l'économie réelle (S-3).
 * Chaque faction PNJ a une identité, des priorités, une personnalité collective, des stocks, des objectifs (dont un
 * caché) et un cerveau : regarder → besoins → menaces → occasions → choisir → agir. Les guerres naissent d'intérêts
 * opposés, jamais d'un tirage. Les ressources ont une origine et un trajet : production par région, convois sur le
 * graphe (qui peuvent être attaqués par les hordes), blocus, traités, rumeurs. Hors ligne aussi (règle 2 : jamais
 * contre une base de joueurs).
 * Les stocks et relations de départ viennent de Skript (za_p67) ; les décisions repartent vers Skript.
 */
public final class Factions {
    public static final String[] RESSOURCES = {"vivres", "medicaments", "munitions", "carburant", "energie"};

    public static final class Faction {
        public final String id;
        public String type = "civile", perso = "prudente";
        public final Map<String, Integer> stocks = new LinkedHashMap<>();
        public int territoires;
        public double moral = 60, stabilite = 70;
        public String objectif = "", secondaire = "", cache = "";
        public final List<String> carnet = new ArrayList<>();       // décisions et raisons (F5 « pourquoi »)
        public int dernierCycle = -1;

        Faction(String id) {
            this.id = id;
        }

        public int stock(String r) {
            return stocks.getOrDefault(r, 0);
        }
    }

    public static final class Traite {
        public String a, b, objet;
        public int fin;
        public boolean rompu;
    }

    public static final class Convoi {
        public int id;
        public String faction, ressource, depart, arrivee;
        public int quantite;
        public double x, z, tx, tz;
        public String etat = "en_route";   // en_route, arrive, attaque, pille
        public String escorte = "";         // uuid du joueur qui l'escorte (S-3, 89 : le joueur peut s'en mêler)
    }

    public static final class Blocus {
        public String faction, contre, ressource, region;
        public int fin;
    }

    /** une décision à appliquer côté serveur */
    public static final class Ordre {
        public final String type;
        public final String[] args;
        public final String texte;

        Ordre(String type, String texte, String... args) {
            this.type = type;
            this.texte = texte;
            this.args = args;
        }
    }

    public final Map<String, Faction> factions = new LinkedHashMap<>();
    public final Map<String, Integer> relations = new HashMap<>();
    public final List<Traite> traites = new ArrayList<>();
    public final List<Convoi> convois = new ArrayList<>();
    public final List<Blocus> blocus = new ArrayList<>();
    /** guerres en phases (IA-10) : clé a|b -> tension, incident, mobilisation, escarmouches, offensive, occupation, traite */
    public final Map<String, String> guerres = new HashMap<>();
    private final Random rng;
    private int prochainConvoi = 1;

    public Factions(Random rng) {
        this.rng = rng;
        identite("milice", "militaire", "prudente", "Tenir la route 117", "Trouver des munitions", "Retrouver un scientifique de Bravo");
        identite("scientifiques", "scientifique", "prudente", "Obtenir des échantillons du nouveau foyer", "Garder l'hôpital", "Reconstituer le programme Z-01");
        identite("marchands", "marchande", "commercante", "Garder les routes ouvertes", "Acheter du carburant bas, le revendre haut", "Devenir indispensables");
        identite("pilleurs", "criminelle", "agressive", "Prendre un dépôt de carburant", "Piller les convois", "Faire tomber la milice");
        identite("survivants", "civile", "isolationniste", "Nourrir tout le monde", "Garder les fermes", "Retrouver les familles");
        identite("culte", "criminelle", "expansionniste", "Convertir les camps", "Gagner la radio", "Ouvrir un nid « sacré »");
        // les Déserteurs de Bravo (88) : retranchés dans la station-service de l'est, NORDA les cherche
        identite("deserteurs", "militaire", "prudente", "Survivre loin de NORDA", "Vendre de l'équipement militaire", "Vendre les secrets de NORDA au plus offrant");
        faction("deserteurs").stocks.put("munitions", 40);
        faction("deserteurs").stocks.put("vivres", 10);
    }

    private void identite(String id, String type, String perso, String o, String s, String c) {
        Faction f = faction(id);
        f.type = type;
        f.perso = perso;
        f.objectif = o;
        f.secondaire = s;
        f.cache = c;
    }

    public Faction faction(String id) {
        return factions.computeIfAbsent(id, Faction::new);
    }

    public static String cle(String a, String b) {
        return a.compareTo(b) < 0 ? a + "|" + b : b + "|" + a;
    }

    public int relation(String a, String b) {
        return relations.getOrDefault(cle(a, b), 0);
    }

    /** la ressource dont une faction a le plus besoin (ses priorités selon son type) */
    private String besoin(Faction f) {
        String best = null;
        double pire = 999;
        for (String r : RESSOURCES) {
            double s = f.stock(r) - poids(f.type, r) * 5;
            if (s < pire) {
                pire = s;
                best = r;
            }
        }
        return pire < 8 ? best : null;
    }

    private static double poids(String type, String r) {
        switch (type) {
            case "militaire":
                return r.equals("munitions") ? 3 : r.equals("carburant") ? 2 : 1;
            case "scientifique":
                return r.equals("medicaments") ? 3 : r.equals("energie") ? 2 : 1;
            case "marchande":
                return r.equals("carburant") ? 3 : 1;
            case "criminelle":
                return r.equals("munitions") || r.equals("carburant") ? 2 : 1;
            default:
                return r.equals("vivres") ? 3 : 1;
        }
    }

    /** qui a du surplus de cette ressource ? */
    private Faction detenteur(String r, Faction sauf) {
        Faction best = null;
        for (Faction f : factions.values()) if (f != sauf && f.stock(r) >= 20 && (best == null || f.stock(r) > best.stock(r))) best = f;
        return best;
    }

    /**
     * Le cycle d'un cerveau de faction (une fois par jour serveur, et à mi-journée pour les convois).
     * Exemple de la bible : carburant au plus bas, le voisin contrôle le dépôt, la relation est mauvaise → on compare
     * commerce, espionnage, blocus, raid, guerre selon la personnalité.
     */
    public List<Ordre> cycle(int jour, Graphe g) {
        List<Ordre> o = new ArrayList<>();
        for (Faction f : factions.values()) {
            if (f.dernierCycle == jour) continue;
            f.dernierCycle = jour;
            if (f.territoires == 0 && !f.id.equals("marchands") && !f.id.equals("deserteurs")) continue;
            if (f.stabilite <= 0) continue;   // faction détruite
            String r = besoin(f);
            if (r == null) {
                // pas de besoin : renforcer ou commercer son surplus
                for (String x : RESSOURCES) {
                    if (f.stock(x) >= 40 && rng.nextDouble() < 0.4) {
                        Faction acheteur = null;
                        for (Faction k : factions.values()) if (k != f && k.stock(x) < 8 && relation(f.id, k.id) > -20) acheteur = k;
                        if (acheteur != null) o.add(convoi(f, acheteur, x, 12, g, jour, "surplus de " + x));
                        break;
                    }
                }
                continue;
            }
            Faction d = detenteur(r, f);
            int rel = d == null ? 0 : relation(f.id, d.id);
            // scores par option, selon la personnalité (IA-10)
            Map<String, Double> sc = new LinkedHashMap<>();
            sc.put("commerce", d == null ? -99 : 30 + rel / 2.0 + (f.perso.equals("commercante") ? 25 : 0) + (f.perso.equals("prudente") ? 10 : 0));
            sc.put("espionnage", 12.0 + (f.type.equals("scientifique") ? 10 : 0));
            sc.put("blocus", d == null ? -99 : 15 - rel / 4.0 + (f.perso.equals("prudente") ? 15 : 0) + (f.perso.equals("isolationniste") ? -10 : 0));
            sc.put("raid", d == null ? -99 : 5 - rel / 2.0 + (f.perso.equals("agressive") ? 30 : 0) + (f.perso.equals("expansionniste") ? 15 : 0) - (f.moral < 40 ? 15 : 0));
            sc.put("rationner", 10.0 + (f.perso.equals("isolationniste") ? 20 : 0));
            String choix = null;
            double mx = -999;
            for (Map.Entry<String, Double> e : sc.entrySet()) {
                double v = e.getValue() + rng.nextDouble() * 8;
                if (v > mx) {
                    mx = v;
                    choix = e.getKey();
                }
            }
            f.carnet.add("J" + jour + " : manque de " + r + " ; options " + arrondi(sc) + " → " + choix);
            while (f.carnet.size() > 20) f.carnet.remove(0);
            switch (choix) {
                case "commerce":
                    o.add(convoi(d, f, r, 10, g, jour, "achat négocié par " + f.id));
                    o.add(new Ordre("relation", null, f.id, d.id, "3"));
                    break;
                case "espionnage":
                    o.add(new Ordre("chronique", "Des éclaireurs de " + f.id + " fouinent autour des dépôts.", "faction_espionnage", f.id, "2"));
                    break;
                case "blocus": {
                    Blocus b = new Blocus();
                    b.faction = f.id;
                    b.contre = d.id;
                    b.ressource = r;
                    b.fin = jour + 3;
                    blocus.add(b);
                    o.add(new Ordre("blocus", f.id + " bloque la route : plus rien ne passe pour " + d.id + ".", f.id, d.id, r));
                    o.add(new Ordre("relation", null, f.id, d.id, "-8"));
                    escalader(f.id, d.id, o, jour);
                    break;
                }
                case "raid":
                    o.add(new Ordre("raid", f.id + " attaque un dépôt de " + d.id + ".", f.id, d.id, r));
                    o.add(new Ordre("relation", null, f.id, d.id, "-15"));
                    o.add(new Ordre("stock", null, f.id, r, "6"));
                    o.add(new Ordre("stock", null, d.id, r, "-6"));
                    escalader(f.id, d.id, o, jour);
                    break;
                default:
                    o.add(new Ordre("chronique", f.id + " rationne : moins de " + r + " pour tout le monde.", "faction_rationne", f.id, "1"));
                    f.moral = Math.max(0, f.moral - 5);
                    break;
            }
            // politique interne (IA-10) : un chef peut perdre le contrôle
            if (f.moral < 25 && rng.nextDouble() < 0.3) {
                f.stabilite = Math.max(0, f.stabilite - 20);
                o.add(new Ordre("chronique", "Ça gronde chez " + f.id + " : la milice conteste le chef.", "faction_crise", f.id, "3"));
            }
        }
        // traités qui expirent, blocus qui tombent
        for (Iterator<Traite> it = traites.iterator(); it.hasNext(); ) {
            Traite t = it.next();
            if (t.fin <= jour) {
                o.add(new Ordre("chronique", "Le traité entre " + t.a + " et " + t.b + " arrive à son terme.", "traite_fin", t.a, "2"));
                it.remove();
            }
        }
        blocus.removeIf(b -> b.fin <= jour);
        return o;
    }

    private static String arrondi(Map<String, Double> m) {
        StringBuilder b = new StringBuilder();
        for (Map.Entry<String, Double> e : m.entrySet()) if (e.getValue() > -50) b.append(e.getKey()).append(' ').append(Math.round(e.getValue())).append(", ");
        return b.length() > 2 ? b.substring(0, b.length() - 2) : "";
    }

    /** une guerre ne tombe pas du ciel : elle monte par phases, et un traité peut l'arrêter (IA-10) */
    private void escalader(String a, String b, List<Ordre> o, int jour) {
        String k = cle(a, b);
        String[] phases = {"tension", "incident", "mobilisation", "escarmouches", "offensive"};
        String p = guerres.get(k);
        int i = -1;
        for (int n = 0; n < phases.length; n++) if (phases[n].equals(p)) i = n;
        // la faction prudente propose un traité avant l'offensive
        Faction fa = factions.get(a), fb = factions.get(b);
        if (i >= 2 && ((fa != null && fa.perso.equals("prudente")) || (fb != null && fb.perso.equals("prudente"))) && rng.nextDouble() < 0.5) {
            Traite t = new Traite();
            t.a = a;
            t.b = b;
            t.objet = "passage des convois contre du carburant";
            t.fin = jour + 7;
            traites.add(t);
            guerres.remove(k);
            o.add(new Ordre("traite", "Traité de 7 jours entre " + a + " et " + b + " : " + t.objet + ".", a, b, "7"));
            o.add(new Ordre("relation", null, a, b, "15"));
            return;
        }
        if (i < phases.length - 1) {
            guerres.put(k, phases[i + 1]);
            o.add(new Ordre("chronique", "Entre " + a + " et " + b + " : " + phases[i + 1] + ".", "guerre_" + phases[i + 1], a, i + 1 >= 3 ? "4" : "2"));
        }
    }

    /** rompre un traité fait chuter la réputation du traître auprès de TOUS (IA-10, chaîne 13) */
    public List<Ordre> rompre(String traitre, String victime) {
        List<Ordre> o = new ArrayList<>();
        for (Traite t : traites) {
            if (!((t.a.equals(traitre) && t.b.equals(victime)) || (t.b.equals(traitre) && t.a.equals(victime)))) continue;
            t.rompu = true;
            t.fin = 0;
            for (Faction f : factions.values()) if (!f.id.equals(traitre)) o.add(new Ordre("relation", null, traitre, f.id, f.id.equals(victime) ? "-40" : "-12"));
            o.add(new Ordre("chronique", traitre + " a rompu son traité avec " + victime + ".", "traite_rompu", traitre, "4"));
        }
        return o;
    }

    // ---------------------------------------------------------------- convois (92) : de vrais trajets sur le graphe

    private Ordre convoi(Faction de, Faction vers, String r, int q, Graphe g, int jour, String raison) {
        Convoi c = new Convoi();
        c.id = prochainConvoi++;
        c.faction = de.id;
        c.ressource = r;
        c.quantite = Math.min(q, de.stock(r));
        // départ et arrivée : deux lieux au hasard, faute de territoires géolocalisés ici
        List<Graphe.Lieu> l = new ArrayList<>(g.lieux.values());
        if (l.size() < 2) return new Ordre("rien", "");
        Graphe.Lieu a = l.get(rng.nextInt(l.size())), b = l.get(rng.nextInt(l.size()));
        c.depart = a.nom;
        c.arrivee = b.nom;
        c.x = a.x;
        c.z = a.z;
        c.tx = b.x;
        c.tz = b.z;
        de.stocks.merge(r, -c.quantite, Integer::sum);
        c.etat = "en_route|" + vers.id;
        convois.add(c);
        return new Ordre("convoi", "Un convoi de " + de.id + " part de " + a.nom + " vers " + b.nom + " avec " + c.quantite + " " + r + " (" + raison + ").",
                String.valueOf(c.id), de.id, vers.id, r, String.valueOf(c.quantite));
    }

    /** toutes les 30 s : les convois avancent ; une horde proche peut les attaquer ; un blocus les arrête */
    public List<Ordre> avancer(List<Horde> hordes) {
        List<Ordre> o = new ArrayList<>();
        for (Iterator<Convoi> it = convois.iterator(); it.hasNext(); ) {
            Convoi c = it.next();
            String vers = c.etat.contains("|") ? c.etat.substring(c.etat.indexOf('|') + 1) : "";
            boolean bloque = false;
            for (Blocus b : blocus) if (b.contre.equals(vers) && b.ressource.equals(c.ressource)) bloque = true;
            if (bloque) {
                if (rng.nextDouble() < 0.05) {
                    it.remove();
                    o.add(new Ordre("convoi_bloque", "Le convoi de " + c.faction + " fait demi-tour au barrage.", String.valueOf(c.id), c.faction, String.valueOf((int) c.x), String.valueOf((int) c.z)));
                    o.add(new Ordre("stock", null, c.faction, c.ressource, String.valueOf(c.quantite)));
                }
                continue;
            }
            double dx = c.tx - c.x, dz = c.tz - c.z, d = Math.hypot(dx, dz);
            double pas = 1.2 * 30;   // à pied ou en charrette
            if (d <= pas) {
                it.remove();
                if (!c.escorte.isEmpty())
                    o.add(new Ordre("convoi_escorte_ok", null, String.valueOf(c.id), c.escorte, c.faction, c.ressource, String.valueOf((int) c.tx), String.valueOf((int) c.tz)));
                o.add(new Ordre("convoi_arrive", "Le convoi de " + c.faction + " est arrivé à " + c.arrivee + ".", String.valueOf(c.id), vers, c.ressource, String.valueOf(c.quantite), String.valueOf((int) c.tx), String.valueOf((int) c.tz)));
                continue;
            }
            c.x += dx / d * pas;
            c.z += dz / d * pas;
            for (Horde h : hordes) {
                if (Math.hypot(h.x - c.x, h.z - c.z) < 150 && rng.nextDouble() < 0.08 * Math.min(3, h.taille / 20.0)) {
                    // escorté : l'embuscade a lieu, mais l'escorte se bat (côté serveur) et le convoi passe
                    if (!c.escorte.isEmpty() && rng.nextDouble() < 0.75) {
                        o.add(new Ordre("convoi_embuscade", null, String.valueOf(c.id), c.escorte, c.faction));
                        break;
                    }
                    it.remove();
                    int perdu = rng.nextDouble() < 0.5 ? c.quantite : c.quantite / 2;
                    o.add(new Ordre("convoi_attaque", "Une horde est tombée sur le convoi de " + c.faction + " entre " + c.depart + " et " + c.arrivee + ".",
                            String.valueOf(c.id), c.faction, vers, c.ressource, String.valueOf(c.quantite - perdu), String.valueOf((int) c.x), String.valueOf((int) c.z)));
                    break;
                }
            }
        }
        return o;
    }

    // ---------------------------------------------------------------- l'économie des régions (S-3)

    /** production d'une région selon ses lieux (forêt, fermes, industrie, hôpital, station, base militaire) */
    public static Map<String, Double> production(Region r, Graphe g) {
        Map<String, Double> p = new HashMap<>();
        for (String id : r.lieux) {
            Graphe.Lieu l = g.lieux.get(id);
            if (l == null) continue;
            String t = l.type;
            if (t.contains("ferme")) p.merge("vivres", 4.0, Double::sum);
            else if (t.contains("chalet") || t.contains("chasse")) p.merge("vivres", 1.5, Double::sum);
            else if (t.contains("industri") || t.contains("carriere")) p.merge("energie", 3.0, Double::sum);
            else if (t.contains("station")) p.merge("carburant", 3.0, Double::sum);
            else if (t.contains("bravo") || t.contains("barrage_routier") || t.contains("militaire")) p.merge("munitions", 3.0, Double::sum);
            else if (t.contains("norda") || t.contains("clinique") || t.contains("hopital")) p.merge("medicaments", 2.0, Double::sum);
            else if (t.contains("village")) p.merge("vivres", 2.0, Double::sum);
        }
        double k = Math.max(0.1, 1 - r.contamination / 120.0);   // une région contaminée ne produit presque rien
        p.replaceAll((a, v) -> v * k);
        return p;
    }

    /** rareté locale : abondante, normale, tendue, rare, critique → multiplicateur de prix */
    public static double prixLocal(Region r, Graphe g, String res, List<Blocus> bl) {
        double prod = production(r, g).getOrDefault(res, 0.0);
        double m = prod >= 4 ? 0.8 : prod >= 2 ? 0.95 : prod > 0 ? 1.1 : 1.3;
        if (r.contamination > 60) m += 0.15;
        for (Blocus b : bl) if (b.ressource.equals(res)) m += 0.3;
        return Math.round(m * 100) / 100.0;
    }

    public static String rarete(double m) {
        return m <= 0.85 ? "abondante" : m <= 1.0 ? "normale" : m <= 1.2 ? "tendue" : m <= 1.5 ? "rare" : "critique";
    }

    // ---------------------------------------------------------------- sauvegarde

    public List<String> exporter() {
        List<String> l = new ArrayList<>();
        for (Faction f : factions.values())
            l.add("F\t" + f.id + "\t" + (int) f.moral + "\t" + (int) f.stabilite + "\t" + f.dernierCycle + "\t" + String.join("¦", f.carnet));
        for (Traite t : traites) l.add("T\t" + t.a + "\t" + t.b + "\t" + t.objet + "\t" + t.fin);
        for (Blocus b : blocus) l.add("B\t" + b.faction + "\t" + b.contre + "\t" + b.ressource + "\t" + b.fin);
        for (Map.Entry<String, String> e : guerres.entrySet()) l.add("G\t" + e.getKey() + "\t" + e.getValue());
        for (Convoi c : convois)
            l.add("C\t" + c.id + "\t" + c.faction + "\t" + c.ressource + "\t" + c.quantite + "\t" + (int) c.x + "\t" + (int) c.z + "\t" + (int) c.tx + "\t" + (int) c.tz
                    + "\t" + c.depart + "\t" + c.arrivee + "\t" + c.etat);
        return l;
    }

    public void importer(List<String> l) {
        for (String s : l) {
            String[] c = s.split("\t", -1);
            try {
                switch (c[0]) {
                    case "F": {
                        Faction f = faction(c[1]);
                        f.moral = Double.parseDouble(c[2]);
                        f.stabilite = Double.parseDouble(c[3]);
                        f.dernierCycle = Integer.parseInt(c[4]);
                        if (!c[5].isEmpty()) for (String x : c[5].split("¦")) f.carnet.add(x);
                        break;
                    }
                    case "T": {
                        Traite t = new Traite();
                        t.a = c[1];
                        t.b = c[2];
                        t.objet = c[3];
                        t.fin = Integer.parseInt(c[4]);
                        traites.add(t);
                        break;
                    }
                    case "B": {
                        Blocus b = new Blocus();
                        b.faction = c[1];
                        b.contre = c[2];
                        b.ressource = c[3];
                        b.fin = Integer.parseInt(c[4]);
                        blocus.add(b);
                        break;
                    }
                    case "G":
                        guerres.put(c[1], c[2]);
                        break;
                    case "C": {
                        Convoi v = new Convoi();
                        v.id = Integer.parseInt(c[1]);
                        v.faction = c[2];
                        v.ressource = c[3];
                        v.quantite = Integer.parseInt(c[4]);
                        v.x = Double.parseDouble(c[5]);
                        v.z = Double.parseDouble(c[6]);
                        v.tx = Double.parseDouble(c[7]);
                        v.tz = Double.parseDouble(c[8]);
                        v.depart = c[9];
                        v.arrivee = c[10];
                        v.etat = c[11];
                        convois.add(v);
                        prochainConvoi = Math.max(prochainConvoi, v.id + 1);
                        break;
                    }
                    default:
                        break;
                }
            } catch (RuntimeException ignored) {
                // ligne abîmée
            }
        }
    }
}
