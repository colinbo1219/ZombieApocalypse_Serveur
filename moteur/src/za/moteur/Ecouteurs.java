package za.moteur;

import org.bukkit.Location;
import org.bukkit.entity.Animals;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Monster;
import org.bukkit.Sound;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;
import org.bukkit.entity.Projectile;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.entity.CreatureSpawnEvent;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.entity.EntityDeathEvent;
import org.bukkit.event.entity.EntityExplodeEvent;
import org.bukkit.event.entity.EntitySpawnEvent;
import org.bukkit.event.entity.EntityTargetLivingEntityEvent;
import org.bukkit.event.entity.PlayerDeathEvent;
import org.bukkit.event.entity.ProjectileLaunchEvent;
import org.bukkit.event.player.PlayerFishEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Region;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Ce que le moteur entend du monde réel (bruit, morts, dégâts, explosions, tirs, animaux, pêche). */
public final class Ecouteurs implements Listener {
    private final ZAMoteur z;
    private final Map<UUID, Long> dernierTir = new HashMap<>();
    private final Map<UUID, Long> dernierBloc = new HashMap<>();

    Ecouteurs(ZAMoteur z) {
        this.z = z;
    }

    private static boolean survie(Entity e) {
        return !e.getWorld().getName().equals("za_prologue");
    }

    /** type MythicMobs probable d'après le nom affiché (« Shambler « Vétéran » » -> ZA_Shambler) */
    static String typeDe(Entity e) {
        String n = e.getCustomName() == null ? "" : e.getCustomName().replaceAll("§.", "");
        int k = n.indexOf(" «");
        if (k > 0) n = n.substring(0, k);
        for (String t : Region.TYPES) {
            String court = t.substring(3).replace('_', ' ');
            if (n.equalsIgnoreCase(court) || n.startsWith(court)) return t;
        }
        if (n.contains("Citoyen")) return "ZA_Citoyen_Infecte";
        return "ZA_Shambler";
    }

    private void bruit(Location l, double force) {
        synchronized (z.monde) {
            z.monde.bruit(l.getX(), l.getZ(), force);
        }
    }

    // ---------------------------------------------------------------- morts

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void mort(EntityDeathEvent ev) {
        LivingEntity e = ev.getEntity();
        if (!survie(e) || e instanceof Player) return;
        if (e.getScoreboardTags().contains("za_drone")) {
            z.nordaReel.droneAbattu(e, e.getKiller());
            return;
        }
        if (!(e instanceof Monster)) return;
        Location l = e.getLocation();
        String type = typeDe(e);
        // charge de cadavres (1), pertes du génome (IA-6)
        synchronized (z.monde) {
            Region r = z.monde.graphe.region(l.getX(), l.getZ());
            if (r != null) {
                r.cadavres += 1;
                r.pertes.merge(type, 1.0, Double::sum);
            }
        }
        z.mat.mortReel(e);
        z.cerveaux.mort(e);
        Player k = e.getKiller();
        if (e.getScoreboardTags().contains("za_nemesis")) z.nemesis.mort(e, k);
        if (k != null) {
            z.directeur.kill(k);
            EntityDamageEvent d = e.getLastDamageCause();
            String arme = d == null ? "melee" : Nemesis.classe(d);
            z.telemetrie.kill(arme, type, l);
            synchronized (z.monde) {
                Region r = z.monde.graphe.region(l.getX(), l.getZ());
                if (r != null) {
                    if (arme.equals("balle")) r.habitudes.merge("armes_feu", 0.3, Double::sum);
                    else if (arme.equals("melee")) r.habitudes.merge("melee", 0.3, Double::sum);
                    else if (arme.equals("feu")) r.habitudes.merge("feu", 0.3, Double::sum);
                }
            }
            if (e.getScoreboardTags().contains("za_legende"))
                z.publier(new Evenement("legende_tombee").a(l.getX(), l.getZ()).grav(4).acteur(k.getUniqueId().toString())
                        .dit(e.getCustomName() == null ? "" : e.getCustomName().replaceAll("§.", "")));
        }
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void mortJoueur(PlayerDeathEvent ev) {
        Player p = ev.getEntity();
        if (!survie(p)) return;
        Location l = p.getLocation();
        z.directeur.mort(p);
        EntityDamageEvent d = p.getLastDamageCause();
        String cause = d == null ? "inconnue" : d.getCause().name().toLowerCase();
        Entity tueur = null;
        if (d instanceof EntityDamageByEntityEvent) {
            tueur = ((EntityDamageByEntityEvent) d).getDamager();
            if (tueur instanceof Projectile && ((Projectile) tueur).getShooter() instanceof Entity)
                tueur = (Entity) ((Projectile) tueur).getShooter();
        }
        Region r;
        synchronized (z.monde) {
            r = z.monde.graphe.region(l.getX(), l.getZ());
        }
        z.telemetrie.mortJoueur(tueur instanceof Monster ? "zombie:" + typeDe(tueur) : cause, r == null ? "?" : r.id);
        if (tueur instanceof Monster && tueur instanceof LivingEntity) {
            synchronized (z.monde) {
                if (r != null) r.succes.merge(typeDe(tueur), 5.0, Double::sum);
            }
            z.nemesis.tueur(p, (LivingEntity) tueur, ev.getDrops());
        }
        z.publier(new Evenement("mort_joueur").a(l.getX(), l.getZ()).grav(3).acteur(p.getUniqueId().toString()).dit(p.getName()));
    }

    // ---------------------------------------------------------------- dégâts

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void degats(EntityDamageByEntityEvent ev) {
        Entity cible = ev.getEntity();
        if (!survie(cible)) return;
        Entity src = ev.getDamager();
        if (src instanceof Projectile && ((Projectile) src).getShooter() instanceof Entity) src = (Entity) ((Projectile) src).getShooter();
        if (cible instanceof Player) {
            Player p = (Player) cible;
            if (src instanceof Monster) {
                z.directeur.degats(p, ev.getFinalDamage());
                synchronized (z.monde) {
                    Region r = z.monde.graphe.region(p.getLocation().getX(), p.getLocation().getZ());
                    if (r != null) r.succes.merge(typeDe(src), ev.getFinalDamage(), Double::sum);
                }
            }
            // capture par NORDA au palier 5 (100) : ses agents capturent au lieu de tuer
            if ((src.getScoreboardTags().contains("za_norda") || (src.getCustomName() != null && src.getCustomName().contains("NORDA")))
                    && z.nordaReel.capturables.contains(p.getUniqueId())
                    && p.getHealth() - ev.getFinalDamage() <= 1) {
                ev.setCancelled(true);
                p.setHealth(Math.max(1, p.getHealth()));
                z.nordaReel.capturables.remove(p.getUniqueId());
                z.pont.zaevt("capture " + p.getUniqueId());
                z.publier(new Evenement("norda_capture").a(p.getLocation().getX(), p.getLocation().getZ()).grav(5).acteur(p.getUniqueId().toString()));
            }
            return;
        }
        if (cible instanceof LivingEntity && cible.getScoreboardTags().contains("za_nemesis")) {
            ev.setDamage(z.nemesis.degats((LivingEntity) cible, ev.getDamage(), Nemesis.classe(ev)));
        }
    }

    // ---------------------------------------------------------------- bruit (3) : explosions, tirs, blocs

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void explosion(EntityExplodeEvent ev) {
        Location l = ev.getLocation();
        if (!survie(ev.getEntity())) return;
        z.publier(new Evenement("explosion").a(l.getX(), l.getZ()).grav(2));
        z.cerveaux.panique(l, 14);
    }

    /** les balles de TaCZ sont des entités moddées : leur apparition est un coup de feu */
    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void tirModde(EntitySpawnEvent ev) {
        Entity e = ev.getEntity();
        String t = e.getType().name();
        if (t.startsWith("CREATEBIGCANNONS") && survie(e)) {
            canon(e.getLocation());
            return;
        }
        if (!t.contains("BULLET") || !survie(e)) return;
        Entity tireur = e instanceof Projectile && ((Projectile) e).getShooter() instanceof Entity ? (Entity) ((Projectile) e).getShooter() : null;
        // S-2 : fiabilité selon l'état du tireur (tags posés par za_p129 : blessé, épuisé, affamé, stressé...)
        if (tireur instanceof Player && fiabilite((Player) tireur, e, ev)) return;
        UUID u = tireur == null ? new UUID(0, 0) : tireur.getUniqueId();
        long now = System.currentTimeMillis();
        Long d = dernierTir.get(u);
        if (d != null && now - d < 1000) return;
        dernierTir.put(u, now);
        Location l = e.getLocation();
        double force = 64;
        if (l.getBlock().getLightFromSky() < 8) force *= 0.5;   // à l'intérieur
        if (l.getWorld().isThundering()) force *= 0.5;
        else if (l.getWorld().hasStorm()) force *= 0.8;
        if (z.estNuit()) force *= 1.2;
        bruit(l, force);
        synchronized (z.monde) {
            Region r = z.monde.graphe.region(l.getX(), l.getZ());
            if (r != null) r.habitudes.merge("armes_feu", 0.5, Double::sum);
        }
    }

    private final java.util.Random alea = new java.util.Random();

    /** Main qui tremble : la balle part de travers (dispersion selon l'état) ; à bout de forces, l'arme s'enraye
     *  parfois (la balle ne sort pas). Renvoie vrai si le tir est annulé. */
    private boolean fiabilite(Player p, Entity balle, EntitySpawnEvent ev) {
        java.util.Set<String> tags = p.getScoreboardTags();
        double dispersion = tags.contains("za_tremble2") ? 0.09 : tags.contains("za_tremble") ? 0.04 : 0;
        if (dispersion == 0) return false;
        if (tags.contains("za_tremble2") && alea.nextDouble() < 0.07) {
            ev.setCancelled(true);
            p.playSound(p.getLocation(), Sound.BLOCK_DISPENSER_FAIL, 1f, 1.6f);
            p.sendMessage("§c✖ Enrayé ! §7Tes mains tremblent trop.");
            return true;
        }
        Vector v = balle.getVelocity();
        double n = v.length();
        if (n < 1e-6) return false;
        Vector d = v.clone().normalize().add(new Vector(alea.nextGaussian(), alea.nextGaussian(), alea.nextGaussian())
                .multiply(dispersion)).normalize().multiply(n);
        balle.setVelocity(d);
        return false;
    }

    /** canons de Create Big Cannons (43) : un énorme bruit (300 blocs), et NORDA s'intéresse au tireur le plus proche */
    private long dernierCanon;

    private void canon(Location l) {
        long now = System.currentTimeMillis();
        if (now - dernierCanon < 2000) return;
        dernierCanon = now;
        bruit(l, 300);
        z.publier(new Evenement("tir_canon").a(l.getX(), l.getZ()).grav(3));
        Player proche = null;
        double best = 48 * 48;
        for (Player p : l.getWorld().getPlayers()) {
            double d = p.getLocation().distanceSquared(l);
            if (d < best) {
                best = d;
                proche = p;
            }
        }
        if (proche != null) {
            synchronized (z.monde) {
                z.norda.preuve(proche.getUniqueId().toString(), "canon", 8, l.getX(), l.getZ(), z.jour(), 0);
            }
        }
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void tirArc(ProjectileLaunchEvent ev) {
        if (!(ev.getEntity().getShooter() instanceof Player) || !survie(ev.getEntity())) return;
        bruit(ev.getEntity().getLocation(), 10);
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void bloc(BlockBreakEvent ev) {
        if (!survie(ev.getPlayer())) return;
        long now = System.currentTimeMillis();
        Long d = dernierBloc.get(ev.getPlayer().getUniqueId());
        if (d != null && now - d < 3000) return;
        dernierBloc.put(ev.getPlayer().getUniqueId(), now);
        double f = ev.getPlayer().getLocation().getBlock().getLightFromSky() < 8 ? 5 : 10;
        bruit(ev.getBlock().getLocation(), f);
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void pose(BlockPlaceEvent ev) {
        if (!survie(ev.getPlayer())) return;
        z.directeur.construit(ev.getPlayer());
        String t = ev.getBlock().getType().name();
        if (t.contains("FENCE") || t.contains("PLANKS") || t.contains("BARS") || t.contains("WALL")) {
            synchronized (z.monde) {
                Region r = z.monde.graphe.region(ev.getBlock().getX(), ev.getBlock().getZ());
                if (r != null) r.habitudes.merge("barricades", 0.1, Double::sum);
            }
        }
    }

    // ---------------------------------------------------------------- l'IA ne triche pas (règle 6)

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void cible(EntityTargetLivingEntityEvent ev) {
        if (!z.actif("cerveaux")) return;
        if (!(ev.getEntity() instanceof Monster) || !(ev.getTarget() instanceof Player)) return;
        Entity e = ev.getEntity();
        if (e.getScoreboardTags().contains("za_cerveau_libre") || !survie(e)) return;
        if (ev.getReason() == EntityTargetLivingEntityEvent.TargetReason.TARGET_ATTACKED_ENTITY
                || ev.getReason() == EntityTargetLivingEntityEvent.TargetReason.TARGET_ATTACKED_NEARBY_ENTITY
                || ev.getReason() == EntityTargetLivingEntityEvent.TargetReason.CUSTOM) return;
        if (e instanceof org.bukkit.entity.Mob && !z.cerveaux.percoit((org.bukkit.entity.Mob) e, (Player) ev.getTarget())) ev.setCancelled(true);
    }

    // ---------------------------------------------------------------- écosystème (IA-13, 85)

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void animaux(CreatureSpawnEvent ev) {
        if (!(ev.getEntity() instanceof Animals) || ev.getSpawnReason() != CreatureSpawnEvent.SpawnReason.NATURAL) return;
        Location l = ev.getLocation();
        synchronized (z.monde) {
            Region r = z.monde.graphe.region(l.getX(), l.getZ());
            if (r != null && (r.contamination > 60 || r.nids > 0)) ev.setCancelled(true);   // ils désertent
        }
    }

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void peche(PlayerFishEvent ev) {
        if (ev.getState() != PlayerFishEvent.State.CAUGHT_FISH || ev.getCaught() == null) return;
        Location l = ev.getCaught().getLocation();
        synchronized (z.monde) {
            Region r = z.monde.graphe.region(l.getX(), l.getZ());
            if (r == null || r.eau >= 40) return;
        }
        ev.getCaught().remove();
        ev.getPlayer().sendMessage("§7L'hameçon remonte vide. Dans cette eau-là, même les poissons sont partis.");
    }

    @EventHandler
    public void entree(PlayerJoinEvent ev) {
        z.directeur.join(ev.getPlayer());
        z.rapportAbsence(ev.getPlayer());
    }
}
