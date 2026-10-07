package za.moteur;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.block.data.Openable;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mob;
import org.bukkit.entity.Monster;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.util.Vector;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.UUID;

/**
 * Les sens et le cerveau des zombies (bible IA-2, IA-3) et leur tactique de groupe (IA-5).
 * Chaque zombie proche d'un joueur perçoit (vue en cône selon la lumière, ouïe, odorat, vibrations) et suit une
 * machine à états : errance, alerte, investigation, poursuite, recherche, panique. MythicMobs et l'IA de Minecraft
 * font le déplacement ; le cerveau choisit l'état et la destination (leurres invisibles, comme la migration p33).
 * Un zombie ne vise JAMAIS un joueur qu'il n'a pas perçu (règle 6).
 */
public final class Cerveaux {
    public static final class Cerveau {
        public String etat = "errance";
        public long depuis = System.currentTimeMillis();
        public Location derniere;          // dernière position connue de la proie
        public UUID proie;
        public int pas;                    // étape de la recherche en spirale
        public LivingEntity leurre;
        public final List<String> traits = new ArrayList<>();
        public int groupe = -1;
        public String role = "";
    }

    private final ZAMoteur z;
    private final Map<UUID, Cerveau> cerveaux = new HashMap<>();
    /** carte d'odeurs : cases de 4 x 4 blocs, clé "x;z" -> force */
    private final Map<Long, Double> odeurs = new HashMap<>();
    private final Random rng = new Random();
    public int budget = 80;
    private final Map<Integer, double[]> groupes = new HashMap<>();   // id -> {taille de départ, pertes}
    private int prochainGroupe = 1;

    Cerveaux(ZAMoteur z) {
        this.z = z;
    }

    private static long cle(double x, double zz) {
        return (((long) Math.floor(x / 4)) << 32) ^ (((long) Math.floor(zz / 4)) & 0xffffffffL);
    }

    public Cerveau cerveau(Entity e) {
        return cerveaux.computeIfAbsent(e.getUniqueId(), k -> {
            Cerveau c = new Cerveau();
            // individualité (IA-4) : des traits tirés à l'apparition
            String[] t = {"boiteux", "aveugle", "sourd", "affame", "obstine", "craintif"};
            if (rng.nextDouble() < 0.35) c.traits.add(t[rng.nextInt(t.length)]);
            for (String s : c.traits) e.addScoreboardTag("za_trait_" + s);
            if (c.traits.contains("boiteux") && e instanceof LivingEntity)
                ((LivingEntity) e).addPotionEffect(new PotionEffect(PotionEffectType.SLOW, 20 * 60 * 60, 0, true, false));
            return c;
        });
    }

    // ---------------------------------------------------------------- sens

    /** portée de la vue selon la lumière, la nuit, la torche en main, l'accroupissement, la pluie */
    double porteeVue(Player p) {
        double r = z.estNuit() ? 8 : 24;
        int lum = p.getLocation().getBlock().getLightLevel();
        if (z.estNuit() && lum >= 10) r = 16;
        if (tientLumiere(p)) r = 32;
        if (p.isSneaking()) r /= 2;
        if (p.getWorld().hasStorm()) r *= 0.75;
        return r;
    }

    private static boolean tientLumiere(Player p) {
        ItemStack i = p.getInventory().getItemInMainHand(), o = p.getInventory().getItemInOffHand();
        return lumiere(i) || lumiere(o);
    }

    private static boolean lumiere(ItemStack i) {
        if (i == null) return false;
        String n = i.getType().name();
        return n.contains("TORCH") || n.contains("LANTERN") || n.contains("GLOWSTONE") || n.contains("FLASHLIGHT") || n.contains("LAMP");
    }

    /** le zombie perçoit-il ce joueur ? (vue, vibrations, odorat de près) */
    public boolean percoit(Mob m, Player p) {
        Cerveau c = cerveau(m);
        Location ml = m.getEyeLocation(), pl = p.getEyeLocation();
        if (ml.getWorld() != pl.getWorld()) return false;
        double d = ml.distance(pl);
        if (d < 2.5) return true;                       // au contact, on sent tout
        if (p.getScoreboardTags().contains("za_fumee")) return false;
        if (p.getScoreboardTags().contains("za_odeur_morte") && d > 6) return false;   // infecté au stade 3 (39) : il sent comme eux   // fumigène (104) : plus rien ne se voit ni ne se sent
        boolean aveugle = c.traits.contains("aveugle");
        if (!aveugle && d <= porteeVue(p)) {
            Vector regard = ml.getDirection().normalize();
            Vector vers = pl.toVector().subtract(ml.toVector()).normalize();
            if (regard.dot(vers) > Math.cos(Math.toRadians(55)) && m.hasLineOfSight(p)) return true;
        }
        // vibrations : course, sauts (surtout les aveugles)
        if (p.isSprinting() && d < (aveugle ? 14 : 8)) return true;
        // odorat : piste fraîche ou sang
        double od = odeur(m.getLocation());
        double seuil = c.traits.contains("affame") ? 1.5 : 3;
        if (od > seuil && d < 12) return true;
        return false;
    }

    double odeur(Location l) {
        Double v = odeurs.get(cle(l.getX(), l.getZ()));
        return v == null ? 0 : v;
    }

    /** la piste des joueurs ; le sang (vie basse) laisse une piste forte (point 26) ; l'eau coupe la piste */
    private void deposerOdeurs() {
        for (Player p : z.mondePrincipal().getPlayers()) {
            Location l = p.getLocation();
            if (l.getBlock().isLiquid()) continue;
            double f = 1;
            if (p.getHealth() < 10) f = 4;
            if (p.getScoreboardTags().contains("za_camouflage")) f = 0;   // sang de zombie (IA-2)
            odeurs.merge(cle(l.getX(), l.getZ()), f, (a, b) -> Math.min(20, a + b));
        }
        boolean pluie = z.mondePrincipal().hasStorm();
        Iterator<Map.Entry<Long, Double>> it = odeurs.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<Long, Double> e = it.next();
            double v = e.getValue() * (pluie ? 0.9 : 0.97);
            if (v < 0.2) it.remove();
            else e.setValue(v);
        }
        if (odeurs.size() > 20000) odeurs.clear();
    }

    // ---------------------------------------------------------------- chaque seconde

    void tick1s() {
        deposerOdeurs();
        List<Player> ps = z.mondePrincipal().getPlayers();
        if (ps.isEmpty()) return;
        int n = 0;
        List<Mob> vus = new ArrayList<>();
        for (Player p : ps) {
            for (Entity e : p.getNearbyEntities(48, 20, 48)) {
                if (!(e instanceof Monster) || !(e instanceof Mob)) continue;
                if (e.getScoreboardTags().contains("za_cerveau_libre")) continue;   // boss, PNJ hostiles scriptés
                if (n++ >= budget) break;
                vus.add((Mob) e);
            }
        }
        for (Mob m : vus) penser(m, ps);
        // ménage
        cerveaux.keySet().removeIf(u -> Bukkit.getEntity(u) == null);
        tactique();
    }

    private void penser(Mob m, List<Player> ps) {
        Cerveau c = cerveau(m);
        long now = System.currentTimeMillis();
        long dans = now - c.depuis;
        // perception de la proie la plus proche
        Player vue = null;
        double bd = 1e9;
        for (Player p : ps) {
            if (p.getGameMode().name().equals("SPECTATOR") || p.getGameMode().name().equals("CREATIVE")) continue;
            double d = p.getLocation().distanceSquared(m.getLocation());
            if (d < bd && percoit(m, p)) {
                bd = d;
                vue = p;
            }
        }
        if (vue != null && !c.etat.equals("panique")) {
            if (!c.etat.equals("poursuite")) {
                if (c.etat.equals("errance") && dans > 500) {
                    alerte(m, c, vue.getLocation());
                    return;
                }
                passer(c, "poursuite");
                alerterVoisins(m, vue);
            }
            c.proie = vue.getUniqueId();
            c.derniere = vue.getLocation();
            if (m.getTarget() != vue) m.setTarget(vue);
            metier(m, vue);
            return;
        }
        switch (c.etat) {
            case "alerte":
                if (dans > 2000 + rng.nextInt(2000)) {
                    if (c.derniere != null) {
                        passer(c, "investigation");
                        viser(m, c, c.derniere, 30);
                    } else passer(c, "errance");
                }
                break;
            case "poursuite":
                // il a perdu sa proie : il fouille sa dernière position (point 104)
                passer(c, "recherche");
                c.pas = 0;
                break;
            case "investigation":
                if (c.derniere == null || m.getLocation().distanceSquared(c.derniere) < 9 || dans > 30_000) {
                    passer(c, "recherche");
                    c.pas = 0;
                }
                break;
            case "recherche": {
                long duree = c.traits.contains("obstine") ? 60_000 : 20_000 + rng.nextInt(20_000);
                if (dans > duree || c.derniere == null) {
                    abandonner(m, c);
                    break;
                }
                if (dans / 4000 > c.pas) {
                    c.pas++;
                    double a = c.pas * 1.7, r = 3 + c.pas * 1.5;
                    viser(m, c, c.derniere.clone().add(Math.cos(a) * r, 0, Math.sin(a) * r), 6);
                }
                break;
            }
            case "panique":
                if (dans > (c.traits.contains("craintif") ? 25_000 : 10_000 + rng.nextInt(10_000))) abandonner(m, c);
                break;
            default: {
                // errance : il entend un bruit (point 3) ou suit une odeur
                if (!c.traits.contains("sourd")) {
                    double[] t;
                    synchronized (z.monde) {
                        t = z.monde.plusFortBruit(m.getLocation().getX(), m.getLocation().getZ(), 64);
                    }
                    if (t != null && rng.nextDouble() < 0.5) {
                        alerte(m, c, new Location(m.getWorld(), t[0], m.getLocation().getY(), t[1]));
                        break;
                    }
                }
                // empêche la visée « magique » d'un joueur non perçu
                if (m.getTarget() instanceof Player && !percoit(m, (Player) m.getTarget())) m.setTarget(null);
            }
        }
    }

    private void passer(Cerveau c, String e) {
        c.etat = e;
        c.depuis = System.currentTimeMillis();
    }

    private void alerte(Mob m, Cerveau c, Location source) {
        passer(c, "alerte");
        c.derniere = source;
        m.setTarget(null);
        m.addPotionEffect(new PotionEffect(PotionEffectType.SLOW, 50, 3, true, false));
        // il tourne la tête et renifle : on l'entend, on apprend à le lire
        Location l = m.getLocation();
        Vector v = source.toVector().subtract(l.toVector());
        l.setDirection(v);
        m.setRotation(l.getYaw(), l.getPitch());
        m.getWorld().playSound(l, Sound.ENTITY_FOX_SNIFF, 0.8f, 0.5f);
    }

    private void viser(Mob m, Cerveau c, Location l, int secondes) {
        if (l == null) return;
        Location sol = l.clone();
        sol.setY(m.getWorld().getHighestBlockYAt(sol) + 1);
        LivingEntity v = z.mat.leurre(sol, secondes);
        if (v != null) {
            c.leurre = v;
            m.setTarget(v);
        }
    }

    private void abandonner(Mob m, Cerveau c) {
        passer(c, "errance");
        c.derniere = null;
        c.proie = null;
        if (m.getTarget() != null && !(m.getTarget() instanceof Player)) m.setTarget(null);
        else if (m.getTarget() instanceof Player && !percoit(m, (Player) m.getTarget())) m.setTarget(null);
    }

    /** alerte partagée : 8 blocs ; le Screamer porte à 48 (p56) */
    private void alerterVoisins(Mob m, Player p) {
        String nom = m.getCustomName() == null ? "" : m.getCustomName();
        double r = nom.contains("Screamer") ? 48 : 8;
        for (Entity e : m.getNearbyEntities(r, 6, r)) {
            if (!(e instanceof Mob) || !(e instanceof Monster)) continue;
            Cerveau c = cerveau(e);
            if (c.etat.equals("errance") || c.etat.equals("recherche")) {
                c.derniere = p.getLocation();
                passer(c, "investigation");
                viser((Mob) e, c, c.derniere, 20);
            }
        }
    }

    /** panique (point 68) : explosion, feu, fusée : fuir 10 à 20 s ; les Alphas et vétérans résistent */
    public void panique(Location source, double rayon) {
        for (Entity e : source.getWorld().getNearbyEntities(source, rayon, 10, rayon)) {
            if (!(e instanceof Mob) || !(e instanceof Monster)) continue;
            String nom = e.getCustomName() == null ? "" : e.getCustomName();
            if (nom.contains("Alpha") || e.getScoreboardTags().contains("za_veteran") || nom.contains("Pompier")) continue;
            Cerveau c = cerveau(e);
            passer(c, "panique");
            Vector fuite = e.getLocation().toVector().subtract(source.toVector()).setY(0);
            if (fuite.lengthSquared() < 0.01) fuite = new Vector(1, 0, 0);
            fuite.normalize().multiply(20);
            viser((Mob) e, c, e.getLocation().clone().add(fuite), 20);
        }
    }

    /** traits de l'ancien métier (IA-4) : le policier essaie les poignées, le prisonnier traîne ses chaînes */
    private void metier(Mob m, Player p) {
        String nom = m.getCustomName() == null ? "" : m.getCustomName();
        if (nom.contains("Policier") && rng.nextDouble() < 0.3) {
            Location l = m.getLocation();
            for (int dx = -1; dx <= 1; dx++)
                for (int dz = -1; dz <= 1; dz++)
                    for (int dy = 0; dy <= 1; dy++) {
                        Block b = l.clone().add(dx, dy, dz).getBlock();
                        if (b.getType().name().endsWith("_DOOR") && b.getType() != Material.IRON_DOOR && b.getBlockData() instanceof Openable) {
                            Openable o = (Openable) b.getBlockData();
                            if (!o.isOpen()) {
                                o.setOpen(true);
                                b.setBlockData(o);
                                b.getWorld().playSound(b.getLocation(), Sound.BLOCK_WOODEN_DOOR_OPEN, 1f, 0.8f);
                                return;
                            }
                        }
                    }
        }
        if (nom.contains("Prisonnier") && rng.nextDouble() < 0.2) m.getWorld().playSound(m.getLocation(), Sound.BLOCK_CHAIN_STEP, 1f, 0.7f);
    }

    // ---------------------------------------------------------------- tactique de groupe (IA-5)

    private void tactique() {
        // groupes : les morts en poursuite d'une même proie
        Map<UUID, List<Mob>> parProie = new HashMap<>();
        for (Map.Entry<UUID, Cerveau> e : cerveaux.entrySet()) {
            Cerveau c = e.getValue();
            if (!c.etat.equals("poursuite") || c.proie == null) continue;
            Entity en = Bukkit.getEntity(e.getKey());
            if (en instanceof Mob) parProie.computeIfAbsent(c.proie, k -> new ArrayList<>()).add((Mob) en);
        }
        for (Map.Entry<UUID, List<Mob>> e : parProie.entrySet()) {
            List<Mob> g = e.getValue();
            Player p = Bukkit.getPlayer(e.getKey());
            if (p == null || g.size() < 4) continue;
            // un groupe : son identifiant, sa taille de départ
            int gid = -1;
            for (Mob m : g) if (cerveau(m).groupe >= 0) gid = cerveau(m).groupe;
            if (gid < 0) {
                gid = prochainGroupe++;
                groupes.put(gid, new double[]{g.size(), 0});
            }
            for (Mob m : g) cerveau(m).groupe = gid;
            double[] st = groupes.get(gid);
            if (st == null) continue;
            // moral de la horde : à 30 %, elle recule, se regroupe, revient plus tard
            if (st[1] / Math.max(1, st[0]) >= 0.7) {
                for (Mob m : g) {
                    Cerveau c = cerveau(m);
                    passer(c, "panique");
                    Vector v = m.getLocation().toVector().subtract(p.getLocation().toVector()).setY(0);
                    if (v.lengthSquared() < 0.01) v = new Vector(1, 0, 0);
                    viser(m, c, m.getLocation().clone().add(v.normalize().multiply(25)), 20);
                }
                groupes.remove(gid);
                continue;
            }
            // encerclement : un tiers prend un second chemin pour couper la retraite
            Location centre = new Location(p.getWorld(), 0, 0, 0);
            for (Mob m : g) centre.add(m.getLocation());
            centre.multiply(1.0 / g.size());
            Vector derriere = p.getLocation().toVector().subtract(centre.toVector()).setY(0);
            if (derriere.lengthSquared() > 0.01) {
                derriere.normalize().multiply(10);
                int k = 0;
                for (Mob m : g) {
                    Cerveau c = cerveau(m);
                    String nom = m.getCustomName() == null ? "" : m.getCustomName();
                    if (c.role.isEmpty()) {
                        if (nom.contains("Brute")) c.role = "devant";
                        else if (nom.contains("Crawler")) c.role = "achever";
                        else if (k++ % 3 == 0) c.role = "contourner";
                        else c.role = "poursuivre";
                    }
                    if (c.role.equals("contourner") && rng.nextDouble() < 0.3) viser(m, c, p.getLocation().clone().add(derriere), 6);
                    if (c.role.equals("devant")) m.addPotionEffect(new PotionEffect(PotionEffectType.SPEED, 40, 0, true, false));
                }
            }
        }
    }

    /** un mort d'un groupe tombe : le moral du groupe baisse */
    void mort(Entity e) {
        Cerveau c = cerveaux.remove(e.getUniqueId());
        if (c != null && c.groupe >= 0) {
            double[] st = groupes.get(c.groupe);
            if (st != null) st[1]++;
        }
    }

    public String etatDe(Entity e) {
        Cerveau c = cerveaux.get(e.getUniqueId());
        return c == null ? "?" : c.etat + (c.traits.isEmpty() ? "" : " " + c.traits) + (c.role.isEmpty() ? "" : " rôle " + c.role);
    }
}
