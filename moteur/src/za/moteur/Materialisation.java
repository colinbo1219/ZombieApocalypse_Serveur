package za.moteur;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mob;
import org.bukkit.entity.Player;
import org.bukkit.entity.Villager;
import org.bukkit.util.Vector;
import za.moteur.coeur.Horde;
import za.moteur.coeur.Region;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Virtuel <-> réel (bible F4) : les hordes vivent comme des données ; elles apparaissent pour vrai à 96-128 blocs d'un
 * joueur, HORS DE SON CHAMP DE VISION (règle 6), et redeviennent virtuelles quand plus personne n'est à moins de 160 blocs
 * depuis 60 s. Renforts en continu : une horde de 200 envoie ~30 morts réels à la fois, les autres arrivent par l'arrière.
 * Aussi : les leurres invisibles (le moyen de déplacement de toute l'IA, comme la migration p33).
 */
public final class Materialisation {
    private final ZAMoteur z;
    private final Random rng = new Random();

    /** demande d'apparition : horde, type MythicMobs, joueur ciblé */
    private static final class Demande {
        final int horde;
        final String type;
        final UUID joueur;

        Demande(int horde, String type, UUID joueur) {
            this.horde = horde;
            this.type = type;
            this.joueur = joueur;
        }
    }

    private final Deque<Demande> demandes = new ArrayDeque<>();
    private final Map<Integer, Set<UUID>> reels = new HashMap<>();
    private final Map<Integer, Long> derniereProximite = new HashMap<>();
    /** position d'un joueur, relevée sur le fil principal */
    public static final class Pos {
        public final double x, z, y, yaw;
        public final UUID u;

        Pos(double x, double z, double y, double yaw, UUID u) {
            this.x = x;
            this.z = z;
            this.y = y;
            this.yaw = yaw;
            this.u = u;
        }
    }

    private final List<Pos> joueurs = new CopyOnWriteArrayList<>();
    private final List<Object[]> aMarquer = new ArrayList<>();   // {Location, hordeId, échéance tick}
    private final Map<UUID, Long> leurres = new HashMap<>();     // leurre -> expiration (ms)
    private long tick;
    public int front = 30;   // morts réels par horde au contact

    Materialisation(ZAMoteur z) {
        this.z = z;
    }

    public List<Pos> positionsJoueurs() {
        return joueurs;
    }

    public int totalReels() {
        int n = 0;
        for (Set<UUID> s : reels.values()) n += s.size();
        return n;
    }

    /** HORS du fil principal : quelles hordes doivent apparaître ou disparaître ? */
    void planifier(List<Pos> js) {
        if (!z.actif("materialisation")) return;
        long now = System.currentTimeMillis();
        List<Demande> nouvelles = new ArrayList<>();
        synchronized (z.monde) {
            for (Horde h : z.monde.hordes) {
                double best = 1e9;
                Pos cible = null;
                for (Pos p : js) {
                    double d = Math.hypot(p.x - h.x, p.z - h.z);
                    if (d < best) {
                        best = d;
                        cible = p;
                    }
                }
                if (best < 160) derniereProximite.put(h.id, now);
                if (cible != null && best < 140) {
                    // la règle 2 : jamais d'invasion automatique d'une base, sauf siège avec un joueur présent (p8)
                    if (z.directeur.relacheActive(cible.u)) continue;
                    int voulu = Math.min(h.taille, front) - h.reels;
                    Region r = z.monde.graphe.regions.get(h.region);
                    for (int i = 0; i < Math.min(voulu, 8); i++) {
                        String t = r != null ? saisonnier(r, r.tirerType(z.monde.rng)) : "ZA_Shambler";
                        if (h.alpha && h.reels == 0 && i == 0) t = "ZA_Alpha";
                        nouvelles.add(new Demande(h.id, t, cible.u));
                    }
                    // la nuit, une meute de chiens infectés suit parfois la horde (23) : tuer le dominant la disperse
                    if (z.monde.nuit && voulu > 0 && z.monde.rng.nextDouble() < 0.05) {
                        nouvelles.add(new Demande(h.id, "ZA_Chien_Dominant", cible.u));
                        for (int i = 0; i < 2 + z.monde.rng.nextInt(3); i++) nouvelles.add(new Demande(h.id, "ZA_Chien_Infecte", cible.u));
                    }
                }
            }
        }
        synchronized (demandes) {
            if (demandes.size() < 200) demandes.addAll(nouvelles);
        }
    }

    /** fil principal, chaque tick */
    void tickPrincipal() {
        tick++;
        if (tick % 20 == 0) instantane();
        // apparitions avec budget
        int budget = z.budgetSpawnsTick;
        while (budget-- > 0) {
            Demande d;
            synchronized (demandes) {
                d = demandes.poll();
            }
            if (d == null) break;
            apparaitre(d);
        }
        // marquer les morts apparus (la commande MythicMobs ne rend pas l'entité)
        if (!aMarquer.isEmpty()) {
            Iterator<Object[]> it = aMarquer.iterator();
            while (it.hasNext()) {
                Object[] m = it.next();
                Location l = (Location) m[0];
                int hid = (Integer) m[1];
                if (tick < (Long) m[2]) continue;
                it.remove();
                for (Entity e : l.getWorld().getNearbyEntities(l, 4, 6, 4)) {
                    if (!(e instanceof Mob) || e.getTicksLived() > 60 || e.getScoreboardTags().contains("za_horde")) continue;
                    e.addScoreboardTag("za_horde");
                    e.addScoreboardTag("za_h_" + hid);
                    reels.computeIfAbsent(hid, k -> new HashSet<>()).add(e.getUniqueId());
                    synchronized (z.monde) {
                        for (Horde h : z.monde.hordes) if (h.id == hid) h.reels++;
                    }
                    break;
                }
            }
        }
        if (tick % 40 == 0) guider();
        if (tick % 200 == 0) dematerialiser();
        if (tick % 100 == 0) nettoyerLeurres();
    }

    /** positions des joueurs du monde de survie */
    private void instantane() {
        List<Pos> l = new ArrayList<>();
        World w = z.mondePrincipal();
        for (Player p : w.getPlayers()) {
            Location o = p.getLocation();
            l.add(new Pos(o.getX(), o.getZ(), o.getY(), o.getYaw(), p.getUniqueId()));
        }
        joueurs.clear();
        joueurs.addAll(l);
    }

    /** un point à 96-128 blocs, hors du champ de vision du joueur */
    public Location pointHorsVue(Player p, double dmin, double dmax) {
        Location o = p.getLocation();
        Vector regard = o.getDirection().setY(0);
        if (regard.lengthSquared() < 1e-6) regard = new Vector(0, 0, 1);
        regard.normalize();
        for (int essai = 0; essai < 12; essai++) {
            // derrière lui, à ±70° de son dos
            double base = Math.atan2(-regard.getZ(), -regard.getX());
            double a = base + (rng.nextDouble() - 0.5) * Math.toRadians(140);
            double d = dmin + rng.nextDouble() * (dmax - dmin);
            double x = o.getX() + Math.cos(a) * d, zz = o.getZ() + Math.sin(a) * d;
            World w = o.getWorld();
            if (!w.isChunkLoaded(((int) Math.floor(x)) >> 4, ((int) Math.floor(zz)) >> 4)) continue;
            int y = w.getHighestBlockYAt((int) Math.floor(x), (int) Math.floor(zz)) + 1;
            Location l = new Location(w, x, y, zz);
            Vector vers = l.toVector().subtract(o.toVector()).setY(0);
            if (vers.lengthSquared() < 1) continue;
            if (vers.normalize().dot(regard) > Math.cos(Math.toRadians(70))) continue;   // dans son champ de vision
            if (presBase(l, 48)) continue;
            if (w.getBlockAt(l.clone().add(0, -1, 0)).isLiquid()) continue;
            return l;
        }
        return null;
    }

    public boolean presBase(Location l, double r) {
        for (Location b : z.bases.values()) {
            if (b.getWorld() == l.getWorld() && b.distanceSquared(l) < r * r) return true;
        }
        return false;
    }

    private void apparaitre(Demande d) {
        Player p = Bukkit.getPlayer(d.joueur);
        if (p == null || p.getWorld().getName().equals("za_prologue")) return;
        if (totalReels() >= z.plafondReelsServeur) return;
        int pres = 0;
        for (Entity e : p.getNearbyEntities(64, 32, 64)) if (e.getScoreboardTags().contains("za_horde")) pres++;
        if (pres >= z.plafondReelsJoueur) return;
        Location l = pointHorsVue(p, 96, 128);
        if (l == null) return;
        Region r;
        synchronized (z.monde) {
            r = z.monde.graphe.region(l.getX(), l.getZ());
        }
        if (r != null && r.interdictionFarm >= z.monde.jour && r.habitudes.getOrDefault("farm", 0.0) > 20) return;
        String cmd = "mm mobs spawn " + d.type + " 1 " + l.getWorld().getName() + "," + l.getBlockX() + "," + l.getBlockY() + "," + l.getBlockZ();
        Bukkit.dispatchCommand(Bukkit.getConsoleSender(), cmd);
        aMarquer.add(new Object[]{l, d.horde, tick + 2});
        z.ecosysteme.avantHorde(p, l);
    }

    /** les morts d'une horde réelle marchent vers son objectif (ou vers le joueur qu'elle a entendu) */
    private void guider() {
        Map<Integer, Horde> parId = new HashMap<>();
        synchronized (z.monde) {
            for (Horde h : z.monde.hordes) parId.put(h.id, h);
        }
        for (Map.Entry<Integer, Set<UUID>> e : reels.entrySet()) {
            Horde h = parId.get(e.getKey());
            if (h == null) continue;
            Location but = null;
            for (UUID u : e.getValue()) {
                Entity en = Bukkit.getEntity(u);
                if (!(en instanceof Mob)) continue;
                Mob m = (Mob) en;
                if (m.getTarget() instanceof Player) continue;
                if (but == null) {
                    World w = m.getWorld();
                    int y = w.getHighestBlockYAt((int) h.cx, (int) h.cz) + 1;
                    but = new Location(w, h.cx, y, h.cz);
                    if (but.distanceSquared(m.getLocation()) > 200 * 200) but = null;
                }
                if (but != null) {
                    LivingEntity lv = leurre(but, 40);
                    if (lv != null) m.setTarget(lv);
                }
            }
        }
    }

    /** une horde dont plus personne n'est proche depuis 60 s redevient virtuelle (elle garde son état) */
    private void dematerialiser() {
        long now = System.currentTimeMillis();
        Iterator<Map.Entry<Integer, Set<UUID>>> it = reels.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<Integer, Set<UUID>> e = it.next();
            int hid = e.getKey();
            e.getValue().removeIf(u -> Bukkit.getEntity(u) == null || Bukkit.getEntity(u).isDead());
            long dp = derniereProximite.getOrDefault(hid, 0L);
            int vivants = e.getValue().size();
            synchronized (z.monde) {
                for (Horde h : z.monde.hordes) if (h.id == hid) h.reels = vivants;
            }
            if (now - dp > 60_000) {
                for (UUID u : e.getValue()) {
                    Entity en = Bukkit.getEntity(u);
                    if (en != null) en.remove();
                }
                synchronized (z.monde) {
                    for (Horde h : z.monde.hordes) if (h.id == hid) h.reels = 0;
                }
                it.remove();
            }
        }
    }

    /** un mort d'une horde est tombé : la horde le perd, son moral baisse (IA-5) */
    void mortReel(Entity e) {
        for (String t : e.getScoreboardTags()) {
            if (!t.startsWith("za_h_")) continue;
            int hid;
            try {
                hid = Integer.parseInt(t.substring(5));
            } catch (NumberFormatException x) {
                return;
            }
            Set<UUID> s = reels.get(hid);
            if (s != null) s.remove(e.getUniqueId());
            synchronized (z.monde) {
                for (Horde h : z.monde.hordes) {
                    if (h.id != hid) continue;
                    h.taille = Math.max(0, h.taille - 1);
                    h.reels = Math.max(0, h.reels - 1);
                    h.moral = Math.max(0, h.moral - (e.getScoreboardTags().contains("za_alpha") ? 40 : 2));
                }
            }
        }
    }

    public void toutDematerialiser() {
        for (Set<UUID> s : reels.values())
            for (UUID u : s) {
                Entity e = Bukkit.getEntity(u);
                if (e != null) e.remove();
            }
        reels.clear();
        for (UUID u : leurres.keySet()) {
            Entity e = Bukkit.getEntity(u);
            if (e != null) e.remove();
        }
        leurres.clear();
    }

    // ================================================================ leurres invisibles (moyen de déplacement de l'IA)

    /** un leurre invisible : les morts le prennent pour une proie et marchent vers lui */
    public LivingEntity leurre(Location l, int secondes) {
        if (l == null || l.getWorld() == null) return null;
        if (!l.getWorld().isChunkLoaded(l.getBlockX() >> 4, l.getBlockZ() >> 4)) return null;
        for (Entity e : l.getWorld().getNearbyEntities(l, 3, 3, 3)) {
            if (e.getScoreboardTags().contains("za_leurre_moteur") && e instanceof LivingEntity) {
                leurres.put(e.getUniqueId(), System.currentTimeMillis() + secondes * 1000L);
                return (LivingEntity) e;
            }
        }
        if (leurres.size() > 60) return null;
        Villager v = l.getWorld().spawn(l, Villager.class, x -> {
            x.setInvisible(true);
            x.setAI(false);
            x.setInvulnerable(true);
            x.setSilent(true);
            x.setCollidable(false);
            x.setGravity(false);
            x.setPersistent(false);
            x.addScoreboardTag("za_leurre_moteur");
        });
        leurres.put(v.getUniqueId(), System.currentTimeMillis() + secondes * 1000L);
        return v;
    }

    public void deplacerLeurre(LivingEntity v, Location l) {
        if (v != null && l != null) v.teleport(l);
    }

    private void nettoyerLeurres() {
        long now = System.currentTimeMillis();
        Iterator<Map.Entry<UUID, Long>> it = leurres.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<UUID, Long> e = it.next();
            if (e.getValue() < now) {
                Entity en = Bukkit.getEntity(e.getKey());
                if (en != null) en.remove();
                it.remove();
            }
        }
    }

    /** zombies de saison (13) : une part des morts change avec la saison ; les noyés, seulement près de la rivière */
    private String saisonnier(Region r, String t) {
        if (z.monde.rng.nextDouble() > 0.12) return t;
        switch (z.monde.saison) {
            case "printemps":
                return r.riviere ? "ZA_Noye" : t;
            case "ete":
                return "ZA_Saison_Brule";
            case "automne":
                return "ZA_Moisi";
            case "hiver":
                return "ZA_Givre";
            default:
                return t;
        }
    }
}
