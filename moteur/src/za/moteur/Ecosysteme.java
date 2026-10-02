package za.moteur;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.SoundCategory;
import org.bukkit.World;
import org.bukkit.entity.Bat;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Region;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.UUID;

/**
 * L'écosystème comme capteur du monde (bible IA-13, points 23, 105, 113) : oiseaux qui s'envolent avant une horde,
 * silence soudain, corbeaux au-dessus des cadavres et des nids (qui croassent et réveillent les morts), échos lointains
 * d'événements RÉELS dans la bonne direction. Chaque animal est un signal.
 */
public final class Ecosysteme {
    private final ZAMoteur z;
    private final Random rng = new Random();
    private final Map<UUID, Long> corbeaux = new HashMap<>();
    private final Map<UUID, Long> dernierSigne = new HashMap<>();

    Ecosysteme(ZAMoteur z) {
        this.z = z;
    }

    /** des oiseaux s'envolent entre le joueur et la horde qui arrive (105) */
    void avantHorde(Player p, Location horde) {
        long now = System.currentTimeMillis();
        Long d = dernierSigne.get(p.getUniqueId());
        if (d != null && now - d < 60_000) return;
        dernierSigne.put(p.getUniqueId(), now);
        Location m = p.getLocation().clone().add(horde.toVector().subtract(p.getLocation().toVector()).multiply(0.4));
        m.setY(m.getWorld().getHighestBlockYAt(m) + 4);
        envol(p, m);
    }

    private void envol(Player p, Location l) {
        p.spawnParticle(Particle.CLOUD, l, 25, 3, 1, 3, 0.05);
        p.spawnParticle(Particle.FALLING_DUST, l, 0);
        p.playSound(l, Sound.ENTITY_PARROT_FLY, SoundCategory.AMBIENT, 1.5f, 0.8f);
        p.playSound(l, Sound.ENTITY_PHANTOM_FLAP, SoundCategory.AMBIENT, 1f, 1.4f);
        // puis le silence : les sons d'ambiance s'arrêtent (113)
        Bukkit.getScheduler().runTaskLater(z, () -> {
            if (p.isOnline()) p.stopSound(SoundCategory.AMBIENT);
        }, 40L);
        z.pont.set("silence::" + p.getUniqueId(), String.valueOf(System.currentTimeMillis() + 120_000));
    }

    /** signes autour d'un point (mégahorde, réaction) : pour tous les joueurs à portée */
    void signes(double x, double zz, double r) {
        World w = z.mondePrincipal();
        for (Player p : w.getPlayers()) {
            Location l = p.getLocation();
            if (Math.hypot(l.getX() - x, l.getZ() - zz) > r) continue;
            Location m = new Location(w, (l.getX() + x) / 2, 0, (l.getZ() + zz) / 2);
            m.setY(w.getHighestBlockYAt(m) + 4);
            envol(p, m);
            p.playSound(m, Sound.ENTITY_WOLF_HOWL, SoundCategory.AMBIENT, 0.6f, 0.7f);
        }
    }

    /** un signe près du joueur, dans une direction plausible */
    void signesPres(Player p) {
        Location l = p.getLocation().clone().add((rng.nextDouble() - 0.5) * 60, 0, (rng.nextDouble() - 0.5) * 60);
        l.setY(l.getWorld().getHighestBlockYAt(l) + 4);
        int c = rng.nextInt(3);
        if (c == 0) envol(p, l);
        else if (c == 1) p.playSound(l, Sound.ENTITY_WOLF_HOWL, SoundCategory.AMBIENT, 0.5f, 0.6f);
        else p.spawnParticle(Particle.ASH, l, 80, 6, 2, 6, 0);   // un nuage de poussière à l'horizon
    }

    /**
     * un écho lointain (113) : s'il s'est passé quelque chose de réel entre 300 et 800 blocs, on l'entend, étouffé, dans
     * la bonne direction. Sinon, un son plausible.
     */
    void echoLointain(Player p) {
        Location l = p.getLocation();
        Evenement best = null;
        synchronized (z.monde) {
            for (Evenement e : z.monde.chronique.derniers(60)) {
                double d = Math.hypot(e.x - l.getX(), e.z - l.getZ());
                if (d < 300 || d > 800) continue;
                if (System.currentTimeMillis() - e.quand > 10 * 60_000L) continue;
                best = e;
            }
        }
        double ang;
        Sound s;
        if (best != null) {
            ang = Math.atan2(best.z - l.getZ(), best.x - l.getX());
            s = best.type.contains("explosion") || best.type.contains("frappe") ? Sound.ENTITY_GENERIC_EXPLODE
                    : best.type.contains("horde") ? Sound.ENTITY_ZOMBIE_AMBIENT : Sound.ENTITY_FIREWORK_ROCKET_BLAST_FAR;
        } else {
            ang = rng.nextDouble() * Math.PI * 2;
            Sound[] t = {Sound.ENTITY_ZOMBIE_AMBIENT, Sound.ENTITY_WOLF_HOWL, Sound.BLOCK_BELL_RESONATE, Sound.ENTITY_FIREWORK_ROCKET_BLAST_FAR};
            s = t[rng.nextInt(t.length)];
        }
        Location src = l.clone().add(Math.cos(ang) * 40, 8, Math.sin(ang) * 40);
        p.playSound(src, s, SoundCategory.AMBIENT, 0.6f, 0.5f);
    }

    /** toutes les 30 s : corbeaux au-dessus des cadavres et des nids, échantillons de télémétrie */
    void tick30s() {
        long now = System.currentTimeMillis();
        corbeaux.entrySet().removeIf(e -> {
            Entity en = Bukkit.getEntity(e.getKey());
            if (now > e.getValue()) {
                if (en != null) en.remove();
                return true;
            }
            return en == null;
        });
        List<Player> ps = z.mondePrincipal().getPlayers();
        for (Player p : ps) {
            z.telemetrie.echantillon(p);
            Region r;
            synchronized (z.monde) {
                r = z.monde.graphe.region(p.getLocation().getX(), p.getLocation().getZ());
            }
            if (r == null) continue;
            if ((r.cadavres > 25 || r.nids > 0) && corbeaux.size() < 24 && rng.nextDouble() < 0.4) {
                Location l = p.getLocation().clone().add((rng.nextDouble() - 0.5) * 70, 0, (rng.nextDouble() - 0.5) * 70);
                l.setY(l.getWorld().getHighestBlockYAt(l) + 14);
                for (int i = 0; i < 3; i++) {
                    Bat b = l.getWorld().spawn(l, Bat.class, x -> {
                        x.setCustomName("Corbeau");
                        x.setCustomNameVisible(false);
                        x.addScoreboardTag("za_corbeau");
                        x.setRemoveWhenFarAway(true);
                    });
                    corbeaux.put(b.getUniqueId(), now + 120_000);
                }
                p.playSound(l, Sound.ENTITY_PARROT_AMBIENT, SoundCategory.AMBIENT, 1.2f, 0.5f);
            }
        }
        // un corbeau surpris croasse : les morts proches l'entendent (IA-2)
        for (UUID u : corbeaux.keySet()) {
            Entity e = Bukkit.getEntity(u);
            if (e == null) continue;
            for (Player p : ps) {
                if (p.getWorld() != e.getWorld() || p.getLocation().distanceSquared(e.getLocation()) > 64) continue;
                e.getWorld().playSound(e.getLocation(), Sound.ENTITY_PARROT_AMBIENT, 2f, 0.4f);
                synchronized (z.monde) {
                    z.monde.bruit(e.getLocation().getX(), e.getLocation().getZ(), 30);
                }
                break;
            }
        }
    }
}
