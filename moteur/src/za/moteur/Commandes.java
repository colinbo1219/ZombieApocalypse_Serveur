package za.moteur;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Player;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Graphe;
import za.moteur.coeur.Horde;
import za.moteur.coeur.Norda;
import za.moteur.coeur.Region;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Commandes du moteur.
 * /zam : réservée à la console (Skript l'appelle) — elle nourrit le moteur.
 * /zaadmin : outils de Colin (voir, forcer, simuler, rejouer les chaînes de la bible, Partie 5).
 */
final class Commandes {
    private Commandes() {
    }

    private static double d(String s) {
        return Double.parseDouble(s.replace(",", "."));
    }

    private static int i(String s) {
        return (int) Math.round(d(s));
    }

    private static String reste(String[] a, int depuis) {
        return depuis >= a.length ? "" : String.join(" ", Arrays.copyOfRange(a, depuis, a.length));
    }

    // ================================================================ /zam (Skript -> moteur)

    static boolean zam(ZAMoteur z, CommandSender s, String[] a) {
        if (s instanceof Player && !s.hasPermission("za.admin")) {
            s.sendMessage("§cCommande interne du serveur.");
            return true;
        }
        if (a.length == 0) {
            s.sendMessage("zam jour|saison|evt|bruit|preuve|faux|papiers|effacer|base|camp|courant|habitude|nettoie|tours|infra|faction|lea");
            return true;
        }
        switch (a[0]) {
            case "jour":
                z.jourSkript = i(a[1]);
                return true;
            case "saison":
                synchronized (z.monde) {
                    z.monde.saison = a[1];
                }
                return true;
            case "evt": {
                // zam evt <type> <x> <z> <grav> <acteurs|-> [texte]
                Evenement e = new Evenement(a[1]).a(d(a[2]), d(a[3])).grav(i(a[4]));
                if (a.length > 5 && !a[5].equals("-")) for (String ac : a[5].split(",")) e.acteur(ac);
                e.dit(reste(a, 6));
                e.source = "joueur";
                z.publier(e);
                return true;
            }
            case "bruit":
                synchronized (z.monde) {
                    z.monde.bruit(d(a[1]), d(a[2]), d(a[3]));
                }
                return true;
            case "preuve":
                // zam preuve <uuid> <type> <force> <x> <z> [tours]
                synchronized (z.monde) {
                    z.norda.preuve(a[1], a[2], d(a[3]), d(a[4]), d(a[5]), z.jour(), a.length > 6 ? i(a[6]) : tours(z, d(a[4]), d(a[5])));
                }
                return true;
            case "faux": {
                boolean ok;
                synchronized (z.monde) {
                    ok = z.norda.fausseTrace(a[1], a[2], d(a[3]), z.jour());
                }
                // Skript apprend si NORDA a mordu
                z.pont.zaevt("faux_resultat " + a[1] + " " + (ok ? "1" : "0"));
                return true;
            }
            case "papiers":
                synchronized (z.monde) {
                    z.norda.fauxPapiers(a[1], d(a[2]), z.jour());
                }
                return true;
            case "effacer":
                synchronized (z.monde) {
                    z.norda.effacer(a[1], d(a[2]), d(a[3]), z.jour());
                }
                return true;
            case "base": {
                // zam base <uuid> <x> <y> <z> <monde> | zam base <uuid> suppr (audit N5)
                if (a.length >= 3 && a[2].equals("suppr")) {
                    z.bases.remove(UUID.fromString(a[1]));
                    z.basesVues.remove(UUID.fromString(a[1]));
                    return true;
                }
                World w = Bukkit.getWorld(a[5]);
                if (w == null) return true;
                z.bases.put(UUID.fromString(a[1]), new Location(w, d(a[2]), d(a[3]), d(a[4])));
                z.basesVues.put(UUID.fromString(a[1]), System.currentTimeMillis());
                return true;
            }
            case "basesdebut":
                z.basesTour = System.currentTimeMillis();
                return true;
            case "basesfin":
                // toute base qui n'a pas été renvoyée pendant ce tour n'existe plus côté Skript
                for (UUID u : new ArrayList<>(z.bases.keySet()))
                    if (z.basesVues.getOrDefault(u, 0L) < z.basesTour) {
                        z.bases.remove(u);
                        z.basesVues.remove(u);
                    }
                return true;
            case "camp":
                // zam camp <id> <x> <z> <nom...>
                synchronized (z.monde) {
                    z.monde.graphe.ajouterLieu("camp_" + a[1], "camp", reste(a, 4), d(a[2]), d(a[3]));
                }
                return true;
            case "courant": {
                boolean on = a[3].equals("on");
                z.publier(new Evenement(on ? "courant_retabli" : "courant_coupe").a(d(a[1]), d(a[2])).grav(on ? 3 : 2));
                return true;
            }
            case "habitude":
                synchronized (z.monde) {
                    Region r = z.monde.graphe.region(d(a[1]), d(a[2]));
                    if (r != null) r.habitudes.merge(a[3], d(a[4]), Double::sum);
                }
                return true;
            case "nettoie": {
                // zam nettoie <x> <z> <methode> : brules | enterres | chaux
                String m = a[3];
                z.publier(new Evenement("cadavres_" + m).a(d(a[1]), d(a[2])).grav(1));
                synchronized (z.monde) {
                    Region r = z.monde.graphe.region(d(a[1]), d(a[2]));
                    if (r != null && r.cadavres < 5 && r.nids == 0 && r.contamination < 30 && r.nettoyeeJour < 0) {
                        r.nettoyeeJour = z.jour();
                        r.plaques.add("Nettoyé — Jour " + z.jour());
                        z.pont.zaevt("region_nettoyee " + r.id + " " + r.nom.replace(' ', '_'));
                    }
                }
                return true;
            }
            case "tours":
                synchronized (z.monde) {
                    Region r = z.monde.graphe.region(d(a[1]), d(a[2]));
                    if (r != null) r.tours = Math.max(0, i(a[3]));
                }
                return true;
            case "infra": {
                // zam infra <x> <z> <eau|meteo|repeteur|tour> on|off
                boolean on = a[4].equals("on");
                synchronized (z.monde) {
                    Region r = z.monde.graphe.region(d(a[1]), d(a[2]));
                    if (r == null) return true;
                    switch (a[3]) {
                        case "eau":
                            r.stationEau = on;
                            break;
                        case "meteo":
                            r.meteo = on;
                            break;
                        case "repeteur":
                            r.repeteurs = Math.max(0, r.repeteurs + (on ? 1 : -1));
                            break;
                        case "tour":
                            r.tours = Math.max(0, r.tours + (on ? 1 : -1));
                            break;
                        default:
                            break;
                    }
                }
                z.publier(new Evenement("infra_" + a[3] + (on ? "_on" : "_off")).a(d(a[1]), d(a[2])).grav(on ? 3 : 2));
                return true;
            }
            case "faction": {
                UUID u = UUID.fromString(a[1]);
                if (a.length < 3 || a[2].equals("-")) z.factions.remove(u);
                else z.factions.put(u, a[2]);
                synchronized (z.monde) {
                    Norda.Dossier dd = z.norda.dossiers.get(a[1]);
                    if (dd != null && a.length >= 3 && !a[2].equals("-") && dd.certitude > 50) dd.affiliationSupposee = a[2];
                }
                return true;
            }
            case "lea":
                if (a.length > 1 && a[1].equals("retour")) z.lea.retour();
                return true;
            // bases vivantes (IA-15) et survivants (IA-8)
            case "basestock":
                z.vivantes.stocks(a);
                return true;
            case "surv":
                if (a.length >= 17) z.vivantes.survivant(a);
                return true;
            case "survres":
                z.vivantes.resultat(a);
                return true;
            case "basemin":
                z.vivantes.minimum(a[1], a[2], i(a[3]));
                return true;
            case "fac":
                z.societe.decrire(a);
                return true;
            // la science (19) : autopsie, prévisions, décontamination
            case "autopsie": {
                Nemesis.Fiche f = z.nemesis.pourAutopsie(UUID.fromString(a[1]));
                if (f == null) {
                    z.pont.zaevt("msg " + a[1] + " L'autopsie ne révèle rien qu'on ne sache déjà.");
                    return true;
                }
                z.nemesis.faiblesse(f.id);
                z.pont.zaevt("msg " + a[1] + " Autopsie : les tissus réagissent mal à " + Nemesis.faiblesseMots(f.faiblesse) + ". " + f.nom + " a la même souche. Le bestiaire le note.");
                z.pont.zaevt("bestiaire_avis " + f.nom + " (craint " + Nemesis.faiblesseMots(f.faiblesse) + ")");
                return true;
            }
            case "prevoir":
                prevoir(z, a[1]);
                return true;
            case "brouiller": {
                Player bp = Bukkit.getPlayer(UUID.fromString(a[1]));
                if (bp != null) {
                    int n = z.nordaReel.brouiller(bp);
                    z.pont.zaevt("msg " + a[1] + " " + (n == 0 ? "Le brouilleur grésille. Aucun drone à portée." : n + " drone(s) tombe(nt) comme des pierres."));
                }
                return true;
            }
            case "decontaminer":
                synchronized (z.monde) {
                    Region r = z.monde.graphe.region(d(a[1]), d(a[2]));
                    if (r != null) {
                        r.contamination = Math.max(0, r.contamination - d(a[3]));
                        r.eau = Math.min(100, r.eau + d(a[3]) / 2);
                    }
                }
                z.publier(new Evenement("decontamination").a(d(a[1]), d(a[2])).grav(3).dit("une équipe a décontaminé le secteur"));
                return true;
            case "infodonner": {
                // zam infodonner <vendeur> <acheteur> <n°> : une information vendue (F9, 91)
                synchronized (z.monde) {
                    List<za.moteur.coeur.Information.Connue> l = z.monde.info.savoir("joueur:" + a[1]);
                    int n = i(a[3]) - 1;
                    if (n >= 0 && n < l.size()) {
                        za.moteur.coeur.Information.Connue c = l.get(n);
                        z.monde.info.apprendre("joueur:" + a[2], c.info, c.texte, Math.min(c.fiabilite, 75), "achat", c.sauts + 1);
                        z.pont.zaevt("msg " + a[2] + " Tu as acheté : « " + z.monde.info.vu(c) + " » (" + za.moteur.coeur.Information.age(System.currentTimeMillis() - c.info.cree) + ")");
                    }
                }
                return true;
            }
            // le mensonge lisible (IA-9)
            case "demander":
                z.mensonges.demander(a[1], i(a[2]));
                return true;
            case "accuser":
                z.mensonges.accuser(a[1], i(a[2]));
                return true;
            case "retourner":
                z.mensonges.retourner(a[1], i(a[2]));
                return true;
            case "convoi":
                z.societe.convoiAction(a[1], a[2], i(a[3]));
                return true;
            case "deserteurs":
                z.societe.deserteursChoix(a[1], a[2]);
                return true;
            case "testpnj":
                z.mensonges.tester(a[1], i(a[2]), a.length > 3 && a[3].equals("1"));
                return true;
            case "soignerpnj":
                z.mensonges.soigner(a[1], i(a[2]));
                return true;
            case "rel":
                z.societe.relation(a);
                return true;
            case "basesorties":
                z.vivantes.interdire(a[1], a[2].equals("off"));
                return true;
            default:
                s.sendMessage("zam : sous-commande inconnue " + a[0]);
                return true;
        }
    }

    /** nombre de tours cellulaires actives dans la région (précision de la géolocalisation, 82) */
    private static int tours(ZAMoteur z, double x, double zz) {
        Region r = z.monde.graphe.region(x, zz);
        return r == null ? 0 : r.tours;
    }

    // ================================================================ /zaadmin (Colin)

    static boolean zaadmin(ZAMoteur z, CommandSender s, String[] a) {
        if (!s.hasPermission("za.admin")) {
            s.sendMessage("§cRéservé aux administrateurs.");
            return true;
        }
        if (a.length == 0) {
            aide(s);
            return true;
        }
        Player p = s instanceof Player ? (Player) s : null;
        switch (a[0]) {
            case "directeur": {
                Player c = a.length > 1 ? Bukkit.getPlayerExact(a[1]) : p;
                if (c == null) {
                    s.sendMessage("§cJoueur introuvable.");
                    return true;
                }
                s.sendMessage("§6[Directeur] §f" + c.getName());
                for (String l : z.directeur.rapport(c.getUniqueId())) s.sendMessage("§7" + l);
                return true;
            }
            case "region": {
                Region r;
                synchronized (z.monde) {
                    if (a.length > 1 && !a[1].equals("ici")) r = z.monde.graphe.regions.get(a[1]);
                    else r = p == null ? null : z.monde.graphe.region(p.getLocation().getX(), p.getLocation().getZ());
                    if (r == null) {
                        s.sendMessage("§cRégion inconnue. Liste : " + z.monde.graphe.regions.keySet());
                        return true;
                    }
                    s.sendMessage("§6[Région " + r.id + "] §f" + r.nom + " — §e" + r.etatNom());
                    s.sendMessage("§7contamination " + (int) r.contamination + ", cadavres " + (int) r.cadavres + ", nids " + r.nids
                            + " (stade " + r.nidStade + "), danger " + (int) r.danger());
                    s.sendMessage("§7sécurité " + (int) r.securite + ", moral " + (int) r.moral + ", panique " + (int) r.panique
                            + ", population " + (int) r.population + ", eau " + (int) r.eau + ", végétation " + (int) r.vegetation);
                    s.sendMessage("§7attention Z " + (int) r.attentionZ + ", attention NORDA " + (int) r.attentionN + ", courant "
                            + (r.courant ? "oui" : "non") + ", tours " + r.tours + ", faction " + (r.faction.isEmpty() ? "-" : r.faction));
                    s.sendMessage("§7génome : " + top(r.genome, 5));
                    s.sendMessage("§7traits : " + top(r.traits, 5));
                    s.sendMessage("§7habitudes des joueurs : " + top(r.habitudes, 5));
                    if (!r.plaques.isEmpty()) s.sendMessage("§7plaques : " + r.plaques.subList(Math.max(0, r.plaques.size() - 4), r.plaques.size()));
                    for (String h : r.historique.subList(Math.max(0, r.historique.size() - 5), r.historique.size())) s.sendMessage("§8  " + h);
                }
                return true;
            }
            case "carte":
                synchronized (z.monde) {
                    for (String l : z.monde.carteEtats().split("\n")) s.sendMessage("§7" + l);
                }
                return true;
            case "hordes":
                if (a.length > 1 && a[1].equals("creer")) {
                    if (p == null) return true;
                    int n = a.length > 2 ? i(a[2]) : 20;
                    Horde h;
                    synchronized (z.monde) {
                        Region r = z.monde.graphe.region(p.getLocation().getX(), p.getLocation().getZ());
                        h = z.monde.creerHorde(r, n);
                        if (h != null) {
                            Location l = z.mat.pointHorsVue(p, 300, 400);
                            if (l != null) {
                                h.x = l.getX();
                                h.z = l.getZ();
                            }
                        }
                    }
                    s.sendMessage(h == null ? "§cPlafond de hordes atteint." : "§aHorde créée : " + h.resume());
                    return true;
                }
                if (a.length > 1 && a[1].equals("attirer")) {
                    if (p == null) return true;
                    Horde h;
                    synchronized (z.monde) {
                        h = z.monde.attirerHorde(p.getLocation().getX(), p.getLocation().getZ(), 1500);
                    }
                    s.sendMessage(h == null ? "§cAucune horde à portée." : "§aAttirée : " + h.resume());
                    return true;
                }
                synchronized (z.monde) {
                    s.sendMessage("§6[Hordes] §f" + z.monde.hordes.size() + " (méga actives : " + z.monde.megaActive() + ")");
                    List<Horde> l = new ArrayList<>(z.monde.hordes);
                    if (p != null) {
                        double px = p.getLocation().getX(), pz = p.getLocation().getZ();
                        l.sort((h1, h2) -> Double.compare(Math.hypot(h1.x - px, h1.z - pz), Math.hypot(h2.x - px, h2.z - pz)));
                    }
                    for (int k = 0; k < Math.min(15, l.size()); k++) s.sendMessage("§7" + l.get(k).resume());
                }
                return true;
            case "norda": {
                synchronized (z.monde) {
                    if (a.length > 1) {
                        Player c = Bukkit.getPlayerExact(a[1]);
                        String cle = c != null ? c.getUniqueId().toString() : a[1];
                        Norda.Dossier dd = z.norda.dossiers.get(cle);
                        if (dd == null) {
                            s.sendMessage("§7NORDA n'a pas de dossier sur " + a[1] + ".");
                            return true;
                        }
                        s.sendMessage("§6[Dossier NORDA] §f" + (dd.nom.isEmpty() ? cle : dd.nom) + " — palier " + dd.palier + " " + dd.palierNom());
                        s.sendMessage("§7soupçon " + (int) dd.soupcon + ", certitude " + (int) dd.certitude + ", identité supposée « "
                                + dd.identiteSupposee + " », affiliation « " + dd.affiliationSupposee + " »");
                        s.sendMessage("§7position crue : " + (int) dd.posX + ", " + (int) dd.posZ + " ± " + (int) dd.rayon + " (jour " + dd.posJour
                                + "), route habituelle : " + dd.routeHabituelle() + ", tromperies démasquées : " + dd.tromperies);
                        for (String c2 : dd.croyances.subList(Math.max(0, dd.croyances.size() - 5), dd.croyances.size())) s.sendMessage("§8  croit : " + c2);
                        for (String c2 : dd.preuves.subList(Math.max(0, dd.preuves.size() - 6), dd.preuves.size())) s.sendMessage("§8  preuve : " + c2);
                        return true;
                    }
                    s.sendMessage("§6[NORDA] §f" + z.norda.dossiers.size() + " dossiers, palier max " + z.norda.palierMax()
                            + " — moyens : " + z.norda.drones + " drones, " + z.norda.patrouilles + " patrouilles, " + z.norda.barrages + " barrages");
                    for (Norda.Dossier dd : z.norda.dossiers.values())
                        if (dd.soupcon > 5) s.sendMessage("§7  " + (dd.nom.isEmpty() ? dd.cle : dd.nom) + " : " + dd.palierNom() + " (" + (int) dd.soupcon + "/" + (int) dd.certitude + ")");
                }
                for (String l : z.nordaReel.etat()) s.sendMessage("§7" + l);
                return true;
            }
            case "nemesis": {
                List<Nemesis.Fiche> l = z.nemesis.toutes();
                s.sendMessage("§6[Némésis] §f" + l.size());
                for (Nemesis.Fiche f : l)
                    s.sendMessage("§7  " + f.nom + " — rang " + f.rang + ", " + f.tues + " victime(s), a tué " + f.nomVictime
                            + (f.resistance.isEmpty() ? "" : ", résiste à " + f.resistance) + ", faiblesse " + f.faiblesse
                            + (f.faiblesseConnue ? " (connue)" : " (cachée)") + (f.entite != null && Bukkit.getEntity(f.entite) != null ? ", PRÉSENT" : ""));
                return true;
            }
            case "simuler": {
                int j = a.length > 1 ? i(a[1]) : 30;
                int f = a.length > 2 ? i(a[2]) : 4;
                s.sendMessage("§7Simulation de " + j + " jours en arrière-plan...");
                z.simuler(s, Math.min(365, j), Math.min(50, f));
                return true;
            }
            case "chaine":
                if (p == null || a.length < 2) {
                    s.sendMessage("§c/zaadmin chaine <1-8> (en jeu)");
                    return true;
                }
                chaine(z, p, i(a[1]));
                return true;
            case "evt": {
                // /zaadmin evt <type> [grav] [texte] : publier un événement à sa position
                if (p == null || a.length < 2) return true;
                Evenement e = new Evenement(a[1]).a(p.getLocation().getX(), p.getLocation().getZ())
                        .grav(a.length > 2 ? i(a[2]) : 3).acteur(p.getUniqueId().toString()).dit(reste(a, 3));
                z.publier(e);
                s.sendMessage("§aPublié : " + e.ligne());
                return true;
            }
            case "rapport": {
                List<String> l;
                synchronized (z.telemetrie) {
                    l = new ArrayList<>(z.telemetrie.dernierRapport);
                }
                if (l.isEmpty()) s.sendMessage("§7Pas encore de rapport (il sort à chaque changement de jour). État : " + z.resumeSystemes());
                for (String x : l) s.sendMessage("§7" + x);
                return true;
            }
            case "systeme":
                if (a.length < 3) {
                    s.sendMessage("§6[Systèmes] §7" + z.systemes);
                    return true;
                }
                if (!z.systemes.containsKey(a[1])) {
                    s.sendMessage("§cSystème inconnu : " + z.systemes.keySet());
                    return true;
                }
                z.systemes.put(a[1], a[2].equals("on"));
                z.getConfig().set("systemes." + a[1], a[2].equals("on"));
                z.saveConfig();
                if (a[1].equals("materialisation") && a[2].equals("off")) z.mat.toutDematerialiser();
                s.sendMessage("§a" + a[1] + " : " + a[2]);
                return true;
            case "reactions":
                try {
                    synchronized (z.monde) {
                        z.monde.reactions.charger(new File(z.getDataFolder(), "reactions.yml").toPath());
                    }
                    s.sendMessage("§a" + z.monde.reactions.regles.size() + " règles chargées.");
                } catch (Exception e) {
                    s.sendMessage("§creactions.yml : " + e.getMessage());
                }
                return true;
            case "chronique": {
                int n = a.length > 1 ? i(a[1]) : 15;
                List<Evenement> l;
                synchronized (z.monde) {
                    l = z.monde.chronique.derniers(Math.min(100, n));
                }
                for (Evenement e : l) s.sendMessage("§7" + e.ligne());
                return true;
            }
            case "sauver":
                z.persistance.sauver();
                s.sendMessage("§aÉtat du moteur sauvegardé.");
                return true;
            case "cerveau": {
                if (p == null) return true;
                org.bukkit.util.RayTraceResult rt = p.getWorld().rayTraceEntities(p.getEyeLocation(), p.getEyeLocation().getDirection(), 32, 0.5, x -> x != p);
                Entity t = rt == null ? null : rt.getHitEntity();
                if (!(t instanceof LivingEntity)) {
                    s.sendMessage("§7Regardez une créature.");
                    return true;
                }
                s.sendMessage("§6[Cerveau] §f" + t.getName() + " : " + z.cerveaux.etatDe(t) + " — tags " + t.getScoreboardTags());
                return true;
            }
            case "factions":
                z.societe.admin(s, a);
                return true;
            case "prix": {
                Region r;
                synchronized (z.monde) {
                    r = a.length > 1 ? z.monde.graphe.regions.get(a[1]) : p == null ? null : z.monde.graphe.region(p.getLocation().getX(), p.getLocation().getZ());
                }
                if (r != null) z.societe.prix(s, r);
                return true;
            }
            case "base":
            case "survivant":
                z.vivantes.admin(s, a);
                return true;
            case "memoire":
            case "relation":
            case "savoir":
                z.infoJoueurs.admin(s, a);
                return true;
            case "legendes":
                synchronized (z.monde) {
                    for (za.moteur.coeur.Memoire.Legende l : z.monde.memoire.legendes) {
                        s.sendMessage("§6" + l.nom + " §8(J" + l.jour + ")");
                        for (Map.Entry<String, String> v : l.versions.entrySet()) s.sendMessage("§8  " + v.getKey() + " : §7" + v.getValue());
                    }
                    for (String r : z.monde.chronique.resumes(null, 8)) s.sendMessage("§8" + r);
                }
                return true;
            case "omega":
                for (String l : z.omega.etat()) s.sendMessage("§7" + l);
                return true;
            default:
                aide(s);
                return true;
        }
    }

    private static void aide(CommandSender s) {
        s.sendMessage("§6/zaadmin §7directeur [joueur] · region [id|ici] · carte · hordes [creer N|attirer] · norda [joueur] · nemesis");
        s.sendMessage("§7simuler <jours> [fantômes] · chaine <1-8> · evt <type> [grav] [texte] · rapport · systeme <nom> on|off");
        s.sendMessage("§7reactions recharger · chronique [n] · sauver · cerveau · omega");
        s.sendMessage("§7base <joueur> · survivant <id> · factions [cycle|rompre] · prix [région]");
        s.sendMessage("§7memoire <clé> · relation <de> <envers> · savoir <clé> · legendes  §8(clé : pseudo, region:r_3_4, faction:milice, pnj:12)");
    }

    private static String top(Map<String, Double> m, int n) {
        List<Map.Entry<String, Double>> l = new ArrayList<>(m.entrySet());
        l.sort((x, y) -> Double.compare(y.getValue(), x.getValue()));
        StringBuilder b = new StringBuilder();
        for (int k = 0; k < Math.min(n, l.size()); k++) {
            if (l.get(k).getValue() <= 0) break;
            if (b.length() > 0) b.append(", ");
            b.append(l.get(k).getKey()).append(' ').append(Math.round(l.get(k).getValue() * 10) / 10.0);
        }
        return b.length() == 0 ? "-" : b.toString();
    }

    // ================================================================ chaînes de la bible (Partie 5) : déclencheurs de test

    private static void chaine(ZAMoteur z, Player p, int n) {
        double x = p.getLocation().getX(), zz = p.getLocation().getZ();
        String u = p.getUniqueId().toString();
        String type;
        String texte = "";
        int g = 3;
        switch (n) {
            case 1:
                type = "tir";
                g = 2;
                break;
            case 2:
                type = "labo_detruit";
                g = 5;
                texte = "laboratoire NORDA";
                break;
            case 3:
                type = "nemesis_nee";
                g = 4;
                break;
            case 4:
                type = "visite_camp";
                g = 2;
                break;
            case 5:
                type = "courant_retabli";
                break;
            case 6:
                type = "barrage_fissure";
                g = 4;
                break;
            case 7:
                type = "cel_ping";
                g = 2;
                break;
            case 8:
                type = "infecte_bascule";
                g = 4;
                break;
            case 9:
                type = "generatrice_panne";
                g = 2;
                break;
            case 10: {
                // le bûcheron (IA-8) : la réserve de bois tombe, la base décide seule
                za.moteur.coeur.Bases.Base b = z.vivantes.cerveau.base(u);
                b.stocks.put("bois", 0);
                b.derniereSortie = 0;
                z.vivantes.forcer();
                p.sendMessage("§6[Chaîne 10] §7Bois de ta base mis à 0. Le cerveau de la base décide maintenant (/zaadmin base " + p.getName() + ").");
                return;
            }
            case 11:
                type = "inondation_printemps";
                g = 3;
                break;
            case 12:
                z.pont.zaevt("chaine12 " + u);
                p.sendMessage("§6[Chaîne 12] §7Sac lourd, jambe blessée, froid, fatigue : à toi de rentrer. Un tir attirera la horde.");
                return;
            case 13: {
                za.moteur.coeur.Factions f = z.societe.cerveau;
                f.faction("milice").stocks.put("carburant", 0);
                f.faction("milice").territoires = Math.max(1, f.faction("milice").territoires);
                f.faction("marchands").stocks.put("carburant", 60);
                f.relations.put(za.moteur.coeur.Factions.cle("milice", "marchands"), -30);
                z.societe.admin(p, new String[]{"factions", "cycle"});
                p.sendMessage("§6[Chaîne 13] §7La milice n'a plus de carburant ; les marchands tiennent le dépôt. Voir /zaadmin factions.");
                return;
            }
            case 14:
                type = "vol";
                g = 3;
                texte = p.getName() + " a pris les médicaments du coffre commun";
                break;
            default:
                p.sendMessage("§cChaînes 1 à 14.");
                return;
        }
        Evenement e = new Evenement(type).a(x, zz).grav(g).acteur(u).dit(texte);
        e.source = "test";
        if (n == 14) e.temoin("pnj:temoin").imp(30);
        // chaîne 1 : le coup de feu attire une vraie horde
        if (n == 1) {
            synchronized (z.monde) {
                z.monde.bruit(x, zz, 64);
                Horde h = z.monde.attirerHorde(x, zz, 2000);
                if (h == null) {
                    Location l = z.mat.pointHorsVue(p, 300, 400);
                    h = z.monde.creerHorde(z.monde.graphe.region(x, zz), 25);
                    if (h != null && l != null) {
                        h.x = l.getX();
                        h.z = l.getZ();
                    }
                    if (h != null) h.objectif = "suivre_son";
                    if (h != null) {
                        h.cx = x;
                        h.cz = zz;
                    }
                }
            }
        }
        if (n == 7) {
            synchronized (z.monde) {
                z.norda.preuve(u, "cel", 10, x, zz, z.jour(), tours(z, x, zz));
            }
        }
        z.publier(e);
        int attente;
        synchronized (z.monde) {
            attente = z.monde.reactions.enAttente();
        }
        p.sendMessage("§6[Chaîne " + n + "] §7événement « " + type + " » publié ici. Réactions en attente : " + attente
                + ". Suivre : /zaadmin chronique, /zaadmin region ici" + (n == 7 ? ", /zaadmin norda " + p.getName() : "") + ".");
        Graphe.Lieu l;
        synchronized (z.monde) {
            l = z.monde.graphe.lieuProche(x, zz, 400);
        }
        if (l != null) p.sendMessage("§7Lieu le plus proche : " + l.nom + " (" + l.type + ")");
    }

    /** prévisions des scientifiques (19) : où vont les hordes proches, quelle mutation monte dans la région */
    private static void prevoir(ZAMoteur z, String u) {
        Player p = Bukkit.getPlayer(UUID.fromString(u));
        if (p == null) return;
        double x = p.getLocation().getX(), zz = p.getLocation().getZ();
        List<String> l = new ArrayList<>();
        synchronized (z.monde) {
            List<Horde> hs = new ArrayList<>(z.monde.hordes);
            hs.sort((h1, h2) -> Double.compare(Math.hypot(h1.x - x, h1.z - zz), Math.hypot(h2.x - x, h2.z - zz)));
            for (int k = 0; k < Math.min(2, hs.size()); k++) {
                Horde h = hs.get(k);
                double d = Math.hypot(h.x - x, h.z - zz);
                String dir = direction(h.x - x, h.z - zz);
                String va = Math.hypot(h.cx - x, h.cz - zz) < d - 50 ? "elle se rapproche" : "elle s'éloigne ou tourne";
                l.add("Une horde d'environ " + (h.taille / 10 * 10 + 10) + " morts, à " + (int) (d / 100) * 100 + " m au " + dir + " : " + va + ".");
            }
            Region r = z.monde.graphe.region(x, zz);
            if (r != null) {
                String trait = null;
                double best = 0.15;
                for (Map.Entry<String, Double> t : r.traits.entrySet())
                    if (t.getValue() > best) {
                        best = t.getValue();
                        trait = t.getKey();
                    }
                l.add(trait == null ? "Pas de mutation qui se dessine ici pour l'instant." : "La prochaine adaptation du secteur : « " + trait + " » (" + (int) (best * 100) + " %).");
                l.add("Contamination mesurée : " + (int) r.contamination + " %, eau saine : " + (int) r.eau + " %.");
            }
        }
        for (String s : l) z.pont.zaevt("msg " + u + " " + s);
    }

    private static String direction(double dx, double dz) {
        double a = Math.toDegrees(Math.atan2(dz, dx));
        String[] n = {"est", "sud-est", "sud", "sud-ouest", "ouest", "nord-ouest", "nord", "nord-est"};
        int k = (int) Math.round(((a + 360) % 360) / 45.0) % 8;
        return n[k];
    }
}
