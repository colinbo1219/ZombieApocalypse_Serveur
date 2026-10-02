package za.moteur;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.Sign;
import org.bukkit.entity.Allay;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Norda;
import za.moteur.coeur.Region;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.UUID;

/**
 * NORDA dans le monde réel (bible IA-11, points 79, 82, 96, 99, 100, 101, 109) : drones qui tournent là où NORDA CROIT
 * que tu es (jamais là où tu es vraiment, s'il se trompe), barrages sur tes routes habituelles, patrouilles, capture.
 */
public final class NordaReel {
    private final ZAMoteur z;
    private final Random rng = new Random();

    private static final class Drone {
        UUID entite;
        String cible;
        double cx, cz;
        long fin;
        double angle;
    }

    private static final class Barrage {
        final List<Location> blocs = new ArrayList<>();
        Location centre;
        String cible;
        int jour;
        boolean pose;
        String region;
    }

    private final List<Drone> drones = new ArrayList<>();
    private final List<Barrage> barrages = new ArrayList<>();
    private final Map<UUID, Long> controles = new HashMap<>();
    /** joueurs au palier 5 : une embuscade NORDA les capture au lieu de les tuer (100) */
    public final java.util.Set<UUID> capturables = new java.util.HashSet<>();

    NordaReel(ZAMoteur z) {
        this.z = z;
    }

    /** le plan du jour de NORDA, exécuté sur le fil principal */
    void executer(List<Norda.Ordre> ordres) {
        capturables.clear();
        // les barrages d'hier tombent
        for (Barrage b : barrages) retirer(b);
        barrages.clear();
        for (Norda.Ordre o : ordres) {
            Norda.Dossier d;
            synchronized (z.monde) {
                d = z.norda.dossiers.get(o.cible);
            }
            if (d == null) continue;
            switch (o.type) {
                case "sms":
                    if (o.texte.equals("1"))
                        z.pont.sms(o.cible, "Numéro masqué", "Activité inhabituelle signalée dans votre secteur. Restez disponible pour un contrôle de routine.");
                    else
                        z.pont.sms(o.cible, "NORDA Biotech", "Nous savons qui vous êtes, " + nom(o.cible) + ". Coopérez, et tout ira bien.");
                    break;
                case "drone":
                    lancerDrone(o.cible, d);
                    break;
                case "barrage":
                    poserBarrage(o.cible, o.region);
                    break;
                case "patrouille": {
                    Region r;
                    synchronized (z.monde) {
                        r = o.region == null ? null : z.monde.graphe.regions.get(o.region);
                    }
                    if (r != null && !r.routes.isEmpty()) {
                        double[] p = r.routes.get(rng.nextInt(r.routes.size()));
                        z.pont.zaevt("norda_patrouille " + o.cible + " " + (int) p[0] + " " + (int) p[1]);
                    }
                    break;
                }
                case "capture":
                    try {
                        capturables.add(UUID.fromString(o.cible));
                    } catch (IllegalArgumentException ignored) {
                        // faction : pas de capture
                    }
                    z.pont.zaevt("norda_chasse " + o.cible);
                    break;
                case "radio":
                    z.pont.radio("norda", "Avis à la population : " + nom(o.cible) + " est recherché pour atteinte à la sécurité sanitaire. Signalez-le. Récompense garantie.");
                    break;
                case "marche":
                    z.pont.zaevt("norda_marche " + o.cible);
                    break;
                default:
                    break;
            }
            z.publier(new Evenement("norda_" + o.type).a(d.posX, d.posZ).grav(2).acteur(o.cible).dit(o.texte).faux());
        }
    }

    private String nom(String cle) {
        try {
            Player p = Bukkit.getPlayer(UUID.fromString(cle));
            if (p != null) return p.getName();
        } catch (IllegalArgumentException ignored) {
            // faction
        }
        Norda.Dossier d = z.norda.dossiers.get(cle);
        return d != null && !d.nom.isEmpty() ? d.nom : "le sujet";
    }

    // ---------------------------------------------------------------- drones (99)

    private void lancerDrone(String cible, Norda.Dossier d) {
        Drone dr = new Drone();
        dr.cible = cible;
        dr.cx = d.posX;
        dr.cz = d.posZ;
        dr.fin = System.currentTimeMillis() + 6 * 60_000L;
        drones.add(dr);
    }

    void tick1s() {
        long now = System.currentTimeMillis();
        World w = z.mondePrincipal();
        Iterator<Drone> it = drones.iterator();
        while (it.hasNext()) {
            Drone d = it.next();
            Entity e = d.entite == null ? null : Bukkit.getEntity(d.entite);
            if (now > d.fin) {
                if (e != null) e.remove();
                it.remove();
                continue;
            }
            if (e == null) {
                // il n'apparaît que si quelqu'un est près de l'endroit que NORDA croit être le bon
                if (!w.isChunkLoaded(((int) d.cx) >> 4, ((int) d.cz) >> 4)) continue;
                boolean proche = false;
                for (Player p : w.getPlayers()) if (Math.hypot(p.getLocation().getX() - d.cx, p.getLocation().getZ() - d.cz) < 120) proche = true;
                if (!proche) continue;
                Location l = new Location(w, d.cx, w.getHighestBlockYAt((int) d.cx, (int) d.cz) + 30, d.cz);
                Allay a = w.spawn(l, Allay.class, x -> {
                    x.setAI(false);
                    x.setGravity(false);
                    x.setSilent(true);
                    x.setCustomName("Drone NORDA");
                    x.setCustomNameVisible(false);
                    x.addScoreboardTag("za_drone");
                    x.setGlowing(true);
                    x.setRemoveWhenFarAway(false);
                });
                d.entite = a.getUniqueId();
                e = a;
            }
            // il tourne, il bourdonne, il regarde
            d.angle += 0.08;
            double r = 18;
            Location c = new Location(w, d.cx + Math.cos(d.angle) * r, 0, d.cz + Math.sin(d.angle) * r);
            c.setY(w.getHighestBlockYAt(c) + 30);
            e.teleport(c);
            if (rng.nextInt(4) == 0) w.playSound(c, org.bukkit.Sound.BLOCK_BEEHIVE_WORK, 2f, 0.5f);
            for (Player p : w.getPlayers()) {
                Location pl = p.getLocation();
                if (Math.hypot(pl.getX() - c.getX(), pl.getZ() - c.getZ()) > 40) continue;
                if (pl.getBlock().getLightFromSky() < 8) continue;   // sous un toit, il ne voit rien
                synchronized (z.monde) {
                    z.norda.preuve(p.getUniqueId().toString(), "drone", 3, pl.getX(), pl.getZ(), z.jour(), 0);
                }
                // il suit ce qu'il voit
                d.cx = pl.getX();
                d.cz = pl.getZ();
            }
        }
        // les barrages : posés quand le tronçon est chargé, contrôle à 6 blocs
        for (Barrage b : barrages) {
            if (!b.pose && b.centre != null && w.isChunkLoaded(b.centre.getBlockX() >> 4, b.centre.getBlockZ() >> 4)) poser(b);
            if (!b.pose) continue;
            for (Player p : w.getPlayers()) {
                if (p.getLocation().distanceSquared(b.centre) > 36) continue;
                Long t = controles.get(p.getUniqueId());
                if (t != null && now - t < 10 * 60_000L) continue;
                controles.put(p.getUniqueId(), now);
                z.pont.zaevt("norda_controle " + p.getUniqueId());
            }
        }
    }

    public void droneAbattu(Entity e, Player tueur) {
        drones.removeIf(d -> e.getUniqueId().equals(d.entite));
        Location l = e.getLocation();
        z.publier(new Evenement("drone_abattu").a(l.getX(), l.getZ()).grav(3).acteur(tueur == null ? "" : tueur.getUniqueId().toString()));
        if (tueur != null) {
            synchronized (z.monde) {
                z.norda.preuve(tueur.getUniqueId().toString(), "drone", 8, l.getX(), l.getZ(), z.jour(), 0);
                z.monde.graphe.region(l.getX(), l.getZ()).attentionN += 20;
            }
            z.pont.zaevt("drone_abattu " + tueur.getUniqueId());
        }
    }

    // ---------------------------------------------------------------- barrages (109) sur les routes habituelles

    private void poserBarrage(String cible, String region) {
        if (region == null) return;
        Region r;
        synchronized (z.monde) {
            r = z.monde.graphe.regions.get(region);
        }
        if (r == null || r.routes.isEmpty()) return;
        double[] p = r.routes.get(rng.nextInt(r.routes.size()));
        Barrage b = new Barrage();
        b.cible = cible;
        b.region = region;
        b.jour = z.jour();
        b.centre = new Location(z.mondePrincipal(), p[0], 0, p[1]);
        barrages.add(b);
    }

    private void poser(Barrage b) {
        World w = b.centre.getWorld();
        int y = w.getHighestBlockYAt(b.centre) + 1;
        b.centre.setY(y);
        if (z.mat.presBase(b.centre, 64)) {
            b.pose = true;
            return;
        }
        for (int dx = -3; dx <= 3; dx++) {
            Block bl = w.getBlockAt(b.centre.getBlockX() + dx, y, b.centre.getBlockZ());
            if (bl.getType() == Material.AIR) {
                bl.setType(dx == 0 ? Material.OAK_SIGN : Material.IRON_BARS);
                b.blocs.add(bl.getLocation());
                if (dx == 0 && bl.getState() instanceof Sign) {
                    Sign s = (Sign) bl.getState();
                    s.setLine(0, "NORDA");
                    s.setLine(1, "POINT DE");
                    s.setLine(2, "CONTRÔLE");
                    s.setLine(3, "Halte !");
                    s.update();
                }
            }
        }
        b.pose = true;
        z.pont.zaevt("norda_barrage " + b.centre.getBlockX() + " " + b.centre.getBlockZ());
    }

    private void retirer(Barrage b) {
        for (Location l : b.blocs) {
            Block bl = l.getBlock();
            if (bl.getType() == Material.IRON_BARS || bl.getType() == Material.OAK_SIGN) bl.setType(Material.AIR);
        }
    }

    public List<String> etat() {
        List<String> r = new ArrayList<>();
        r.add("Drones actifs : " + drones.size() + " — barrages : " + barrages.size() + " — capturables : " + capturables.size());
        for (Barrage b : barrages) r.add("  barrage " + b.region + " (" + b.centre.getBlockX() + ", " + b.centre.getBlockZ() + ")" + (b.pose ? " posé" : " en attente"));
        return r;
    }
}
