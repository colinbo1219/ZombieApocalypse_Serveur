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

    /** les Déserteurs de Bravo (88) : chaque jour NORDA s'approche ; au palier 4, les joueurs choisissent leur sort */
    private void deserteurs() {
        Factions.Faction f = cerveau.faction("deserteurs");
        if (f.stabilite <= 0 || f.moral >= 200) return;   // détruits, ou déjà protégés (moral 200 = sous protection)
        int palier;
        synchronized (z.monde) {
            za.moteur.coeur.Norda.Dossier d = z.norda.dossier("faction:deserteurs");
            d.nom = "Déserteurs de Bravo";
            z.norda.preuve("faction:deserteurs", "rumeur", 6, 4050, 330, z.jour(), 0);
            palier = d.palier;
        }
        if (palier >= 4) {
            z.pont.zaevt("deserteurs_menaces");
            z.pont.radio("bravo", "Bravo à tous les postes. Opération de récupération demain, secteur station-service est. Cibles : anciens de Bravo-3. Fin.");
        }
    }

    /** zam deserteurs <proteger|livrer> <uuid> */
    void deserteursChoix(String choix, String u) {
        Factions.Faction f = cerveau.faction("deserteurs");
        if (f.stabilite <= 0) return;
        if (choix.equals("livrer")) {
            f.stabilite = 0;
            synchronized (z.monde) {
                z.norda.effacer(u, 0, -30, z.jour());
            }
            publier("deserteurs_livres", 4050, 330, 4, "Les Déserteurs de Bravo ont été livrés à NORDA", "deserteurs");
            z.pont.radio("pirate", "Quelqu'un a vendu les gars de Bravo à NORDA. On sait que ça s'est fait. On finira par savoir qui.");
        } else {
            f.moral = 200;
            synchronized (z.monde) {
                z.norda.preuve(u, "complice", 15, 4050, 330, z.jour(), 0);
                z.norda.effacer("faction:deserteurs", 0, -50, z.jour());
            }
            publier("deserteurs_proteges", 4050, 330, 3, "Des survivants ont protégé les Déserteurs de Bravo", "deserteurs");
            z.pont.radio("lea", "Il paraît que des gens se sont levés pour protéger les anciens soldats de Bravo. Il reste des gens bien.");
        }
    }

    void jour() {
        deserteurs();
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
                    z.pont.zaevt("convoi_proche " + p.getUniqueId() + " " + c.faction + " " + c.ressource + " " + c.quantite + " " + c.id);
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
                case "convoi_embuscade":
                    z.pont.zaevt("convoi_embuscade " + a[1] + " " + a[2]);
                    break;
                case "convoi_escorte_ok": {
                    Evenement e = new Evenement("escorte").a(Double.parseDouble(a[4]), Double.parseDouble(a[5])).grav(2)
                            .acteur(a[1]).acteur("faction:" + a[2]).dit("escorte du convoi de " + a[2] + " jusqu'au bout");
                    z.publier(e);
                    z.pont.zaevt("convoi_escorte_ok " + a[1] + " " + a[2] + " " + a[3]);
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

    // ---------------------------------------------------------------- le joueur s'en mêle (S-3)

    /** zam convoi <escorter|attaquer> <uuid> <id> : le joueur doit être à moins de 200 blocs du convoi */
    void convoiAction(String choix, String u, int id) {
        Player p = null;
        for (Player o : z.mondePrincipal().getPlayers()) if (o.getUniqueId().toString().equals(u)) p = o;
        if (p == null) return;
        Factions.Convoi c = null;
        synchronized (z.monde) {
            for (Factions.Convoi o : cerveau.convois) if (o.id == id) c = o;
            if (c == null || Math.hypot(c.x - p.getLocation().getX(), c.z - p.getLocation().getZ()) > 200) {
                z.pont.zaevt("msg " + u + " Le convoi est déjà loin, ou il n'existe plus.");
                return;
            }
            if (choix.equals("escorter")) {
                c.escorte = u;
                z.pont.zaevt("msg " + u + " Le chef du convoi hoche la tête. « Reste avec nous jusqu'à " + c.arrivee + ". »");
                return;
            }
            // attaquer : le convoi est pillé, la faction s'en souviendra, la destination manquera de sa ressource
            cerveau.convois.remove(c);
        }
        double x = p.getLocation().getX(), zz = p.getLocation().getZ();
        Evenement e = new Evenement("vol").a(x, zz).grav(3).acteur(u).acteur("faction:" + c.faction)
                .dit("le convoi de " + c.faction + " (" + c.quantite + " " + c.ressource + ") a été pillé");
        z.publier(e);
        String vers = c.etat.contains("|") ? c.etat.substring(c.etat.indexOf('|') + 1) : "";
        if (!vers.isEmpty()) {
            cerveau.faction(vers).stocks.merge(c.ressource, -Math.min(c.quantite, 5), Integer::sum);
            z.pont.zaevt("fac_stock " + vers + " " + c.ressource + " -" + Math.min(c.quantite, 5));
        }
        z.pont.zaevt("convoi_pille " + u + " " + c.faction + " " + c.ressource + " " + c.quantite);
        z.pont.zaevt("convoi_epave " + (int) x + " " + (int) zz + " " + c.faction + " " + c.ressource + " " + c.quantite);
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
