package za.moteur;

import org.bukkit.Location;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Factions;
import za.moteur.coeur.Graphe;
import za.moteur.coeur.Horde;
import za.moteur.coeur.Information;
import za.moteur.coeur.Region;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Le pont entre les cerveaux de factions + l'économie (coeur.Factions, IA-10 / S-3) et le serveur.
 * Skript (za_p67) donne les stocks et les relations ; le moteur décide une fois par jour et fait avancer les convois
 * toutes les 30 s ; les décisions reviennent à Skript (zaevt fac_rel, fac_stock, convoi_epave...) et dans la Chronique,
 * donc à Léa, aux rumeurs et aux mémoires.
 */
public final class Societe {
    private final ZAMoteur z;
    public final Factions cerveau = new Factions(new java.util.Random());

    Societe(ZAMoteur z) {
        this.z = z;
    }

    // ---------------------------------------------------------------- ce que Skript décrit

    /** zam fac <faction> vivres:12 medicaments:3 ... terr:4 */
    void decrire(String[] a) {
        Factions.Faction f = cerveau.faction(a[1]);
        for (int k = 2; k < a.length; k++) {
            int i = a[k].indexOf(':');
            if (i < 0) continue;
            String c = a[k].substring(0, i);
            int v = (int) Math.round(Double.parseDouble(a[k].substring(i + 1)));
            if (c.equals("terr")) f.territoires = v;
            else f.stocks.put(c, v);
        }
    }

    /** zam rel <a> <b> <valeur> */
    void relation(String[] a) {
        cerveau.relations.put(Factions.cle(a[1], a[2]), (int) Math.round(Double.parseDouble(a[3])));
    }

    // ---------------------------------------------------------------- les cycles

    void jour() {
        List<Factions.Ordre> o;
        synchronized (z.monde) {
            o = cerveau.cycle(z.jour(), z.monde.graphe);
        }
        executer(o);
        // les prix voyagent moins vite que les marchandises (F9, S-3) : chaque jour, une nouvelle « prix » par région rare
        synchronized (z.monde) {
            int n = 0;
            for (Region r : z.monde.graphe.regions.values()) {
                if (n >= 6) break;
                for (String res : new String[]{"carburant", "vivres", "medicaments"}) {
                    double m = Factions.prixLocal(r, z.monde.graphe, res, cerveau.blocus);
                    if (m < 1.25) continue;
                    Information.Info i = z.monde.info.nouvelle("prix", "À " + r.nom + ", " + res + " : " + Factions.rarete(m) + " (prix x" + m + ").", r.id, r.cx, r.cz, z.jour());
                    i.source = "marchand";
                    i.fiabilite = 70;
                    i.importance = 20;
                    z.monde.info.apprendre("region:" + r.id, i, i.texte, 70, "marchand", 0);
                    n++;
                    break;
                }
            }
        }
    }

    /** toutes les 30 s (fil principal) : convois, prix locaux des joueurs */
    void tick30s() {
        List<Factions.Ordre> o;
        synchronized (z.monde) {
            o = cerveau.avancer(new ArrayList<>(z.monde.hordes));
        }
        executer(o);
        for (Player p : z.mondePrincipal().getPlayers()) {
            Location l = p.getLocation();
            Region r;
            synchronized (z.monde) {
                r = z.monde.graphe.region(l.getX(), l.getZ());
                if (r == null) continue;
                for (String res : Factions.RESSOURCES)
                    z.pont.set("prix::" + p.getUniqueId() + "::" + res, String.valueOf(Factions.prixLocal(r, z.monde.graphe, res, cerveau.blocus)));
            }
            // un convoi qui passe près d'un joueur : il le voit (et peut décider quoi faire)
            for (Factions.Convoi c : cerveau.convois) {
                if (Math.hypot(c.x - l.getX(), c.z - l.getZ()) < 120 && !c.etat.contains("vu:" + p.getUniqueId())) {
                    c.etat = c.etat + ";vu:" + p.getUniqueId();
                    z.pont.zaevt("convoi_proche " + p.getUniqueId() + " " + c.faction + " " + c.ressource + " " + c.quantite);
                }
            }
        }
    }

    private void executer(List<Factions.Ordre> ordres) {
        for (Factions.Ordre o : ordres) {
            String[] a = o.args;
            switch (o.type) {
                case "relation": {
                    int d = Integer.parseInt(a[2]);
                    cerveau.relations.merge(Factions.cle(a[0], a[1]), d, Integer::sum);
                    z.pont.zaevt("fac_rel " + a[0] + " " + a[1] + " " + d);
                    break;
                }
                case "stock": {
                    int d = Integer.parseInt(a[2]);
                    cerveau.faction(a[0]).stocks.merge(a[1], d, Integer::sum);
                    z.pont.zaevt("fac_stock " + a[0] + " " + a[1] + " " + d);
                    break;
                }
                case "chronique":
                    publier(a[0], 0, 0, Integer.parseInt(a[2]), o.texte, a[1]);
                    break;
                case "blocus":
                    publier("faction_blocus", 0, 0, 3, o.texte, a[0]);
                    z.pont.set("blocus::" + a[2], "1");
                    z.pont.radio("lea", "On me dit que " + a[0] + " a fermé la route. Le " + a[2] + " va manquer, et les prix vont suivre.");
                    break;
                case "raid":
                    publier("faction_raid", 0, 0, 3, o.texte, a[0]);
                    break;
                case "traite":
                    publier("traite_signe", 0, 0, 3, o.texte, a[0]);
                    z.pont.radio("lea", "Bonne nouvelle, pour une fois : " + o.texte);
                    z.pont.set("blocus::carburant", "0");
                    break;
                case "convoi":
                    for (Factions.Convoi c : cerveau.convois)
                        if (String.valueOf(c.id).equals(a[0])) publier("convoi_parti", c.x, c.z, 2, o.texte, a[1]);
                    break;
                case "convoi_arrive":
                    cerveau.faction(a[1]).stocks.merge(a[2], Integer.parseInt(a[3]), Integer::sum);
                    z.pont.zaevt("fac_stock " + a[1] + " " + a[2] + " " + a[3]);
                    publier("convoi_arrive", Double.parseDouble(a[4]), Double.parseDouble(a[5]), 1, o.texte, a[1]);
                    break;
                case "convoi_attaque": {
                    double x = Double.parseDouble(a[5]), zz = Double.parseDouble(a[6]);
                    publier("convoi_detruit", x, zz, 3, o.texte, a[1]);
                    // ce qui reste du chargement gît sur la route : les joueurs peuvent le récupérer (S-3)
                    z.pont.zaevt("convoi_epave " + (int) x + " " + (int) zz + " " + a[1] + " " + a[3] + " " + a[4]);
                    synchronized (z.monde) {
                        z.monde.bruit(x, zz, 80);
                    }
                    break;
                }
                case "convoi_bloque":
                    publier("convoi_bloque", Double.parseDouble(a[2]), Double.parseDouble(a[3]), 2, o.texte, a[1]);
                    break;
                default:
                    break;
            }
        }
    }

    private void publier(String type, double x, double zz, int g, String texte, String faction) {
        Evenement e = new Evenement(type).a(x, zz).grav(g).dit(texte).acteur("faction:" + faction);
        e.source = "faction";
        z.publier(e);
    }

    // ---------------------------------------------------------------- /zaadmin factions

    void admin(CommandSender s, String[] a) {
        if (a.length >= 2 && a[1].equals("rompre") && a.length >= 4) {
            executer(cerveau.rompre(a[2], a[3]));
            s.sendMessage("§cTraité rompu par " + a[2] + ".");
            return;
        }
        if (a.length >= 2 && a[1].equals("cycle")) {
            for (Factions.Faction f : cerveau.factions.values()) f.dernierCycle = -1;
            jour();
            s.sendMessage("§aCycle des factions forcé.");
            return;
        }
        for (Factions.Faction f : cerveau.factions.values()) {
            s.sendMessage("§6" + f.id + " §7(" + f.type + ", " + f.perso + ") territoires " + f.territoires + ", moral " + (int) f.moral + " — stocks " + f.stocks);
            s.sendMessage("§8  objectif : " + f.objectif + " · secondaire : " + f.secondaire + " · caché : " + f.cache);
            for (int i = Math.max(0, f.carnet.size() - 2); i < f.carnet.size(); i++) s.sendMessage("§8  " + f.carnet.get(i));
        }
        for (Factions.Traite t : cerveau.traites) s.sendMessage("§aTraité §7" + t.a + " ↔ " + t.b + " : " + t.objet + " (jusqu'au jour " + t.fin + ")");
        for (Factions.Blocus b : cerveau.blocus) s.sendMessage("§cBlocus §7" + b.faction + " contre " + b.contre + " (" + b.ressource + ", jusqu'au jour " + b.fin + ")");
        for (Map.Entry<String, String> g : cerveau.guerres.entrySet()) s.sendMessage("§4Guerre §7" + g.getKey() + " : " + g.getValue());
        for (Factions.Convoi c : cerveau.convois)
            s.sendMessage("§eConvoi #" + c.id + " §7" + c.faction + " " + c.quantite + " " + c.ressource + " " + c.depart + " → " + c.arrivee + " (" + (int) c.x + ", " + (int) c.z + ")");
        s.sendMessage("§8/zaadmin factions cycle · /zaadmin factions rompre <traître> <victime>");
    }

    /** /zaadmin prix [région] : profil économique (S-3) */
    void prix(CommandSender s, Region r) {
        synchronized (z.monde) {
            Graphe g = z.monde.graphe;
            s.sendMessage("§6[Économie] §f" + r.nom + " — production " + Factions.production(r, g));
            for (String res : Factions.RESSOURCES) {
                double m = Factions.prixLocal(r, g, res, cerveau.blocus);
                s.sendMessage("§7  " + res + " : " + Factions.rarete(m) + " (x" + m + ")");
            }
        }
    }
}
