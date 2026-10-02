package za.moteur;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeInstance;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mob;
import org.bukkit.entity.Monster;
import org.bukkit.entity.Player;
import org.bukkit.entity.Zombie;
import org.bukkit.inventory.EntityEquipment;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import za.moteur.coeur.Evenement;
import za.moteur.coeur.Graphe;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.UUID;

/**
 * Individualité, vétérans et NÉMÉSIS (bible IA-4, point 84, chaîne 3).
 * Le zombie qui tue un joueur devient un vétéran nommé, prend son casque et son arme, se souvient de lui, et revient
 * plus tard, ailleurs (le Directeur organise la revanche). Blessé et en fuite, il revient avec une cicatrice et une
 * résistance à l'arme qui l'a blessé. Il a une faiblesse cachée. Le tuer rend l'équipement et donne sa tête.
 */
public final class Nemesis {
    public static final class Fiche {
        public String id;
        public UUID victime;
        public String nomVictime = "";
        public String nom;
        public String base = "Zombie";
        public int rang = 1;          // 1 Vétéran, 2 Ancien, 3 Légende locale
        public int tues = 1;
        public String resistance = "";
        public String faiblesse = "";
        public boolean faiblesseConnue;
        public boolean cicatrice;
        public ItemStack casque, arme;
        public UUID entite;
        public int jourNe;
        public String lieu = "";
    }

    private final ZAMoteur z;
    private final Map<String, Fiche> fiches = new HashMap<>();
    private final Random rng = new Random();
    public int maxServeur = 10;
    private static final String[] EPITHETES = {"l'Éventreur", "le Faucheur", "la Mâchoire", "le Silencieux", "la Veuve", "le Chasseur",
            "le Tisonnier", "l'Affamé", "le Pendu", "la Griffe", "le Patient", "le Muet"};
    private static final String[] CLASSES = {"melee", "fleche", "balle", "feu", "explosion"};

    Nemesis(ZAMoteur z) {
        this.z = z;
    }

    public boolean aUneNemesis(UUID joueur) {
        for (Fiche f : fiches.values()) if (joueur.equals(f.victime)) return true;
        return false;
    }

    public Fiche de(Entity e) {
        for (String t : e.getScoreboardTags()) if (t.startsWith("za_nem_")) return fiches.get(t.substring(7));
        return null;
    }

    public List<Fiche> toutes() {
        return new ArrayList<>(fiches.values());
    }

    // ---------------------------------------------------------------- naissance

    /** un zombie vient de tuer un joueur (appelé avant que les objets tombent) */
    public void tueur(Player victime, LivingEntity tueur, List<ItemStack> drops) {
        if (!z.actif("nemesis") || !(tueur instanceof Mob) || !(tueur instanceof Monster)) return;
        Fiche f = de(tueur);
        if (f != null) {
            // il tue encore : il monte en grade, son nom grandit
            f.tues++;
            f.rang = Math.min(3, f.rang + 1);
            renommer(tueur, f);
            z.publier(new Evenement("nemesis_tue_encore").a(tueur.getLocation().getX(), tueur.getLocation().getZ()).grav(4)
                    .acteur(victime.getUniqueId().toString()).dit(f.nom));
            return;
        }
        if (aUneNemesis(victime.getUniqueId()) || fiches.size() >= maxServeur) return;
        f = new Fiche();
        f.id = Long.toString(System.currentTimeMillis() % 1_000_000_000L, 36);
        f.victime = victime.getUniqueId();
        f.nomVictime = victime.getName();
        String base = tueur.getCustomName() == null ? "Zombie" : tueur.getCustomName().replaceAll("§.", "");
        int k = base.indexOf(" «");
        f.base = k > 0 ? base.substring(0, k) : base;
        Location l = tueur.getLocation();
        Graphe.Lieu lieu;
        synchronized (z.monde) {
            lieu = z.monde.graphe.lieuProche(l.getX(), l.getZ(), 400);
        }
        f.lieu = lieu == null ? "la 117" : lieu.nom;
        f.nom = EPITHETES[rng.nextInt(EPITHETES.length)] + " de " + f.lieu;
        f.faiblesse = CLASSES[rng.nextInt(CLASSES.length)];
        f.jourNe = z.jour();
        f.entite = tueur.getUniqueId();
        // il prend le casque et l'arme de sa victime
        ItemStack casque = victime.getInventory().getHelmet();
        ItemStack arme = victime.getInventory().getItemInMainHand();
        if (casque != null && casque.getType() != Material.AIR) {
            f.casque = casque.clone();
            drops.remove(casque);
        }
        if (arme != null && arme.getType() != Material.AIR) {
            f.arme = arme.clone();
            drops.remove(arme);
        }
        fiches.put(f.id, f);
        equiper(tueur, f);
        renommer(tueur, f);
        tueur.addScoreboardTag("za_nemesis");
        tueur.addScoreboardTag("za_nem_" + f.id);
        tueur.addScoreboardTag("za_veteran");
        tueur.addScoreboardTag("za_cerveau_libre");
        tueur.setRemoveWhenFarAway(false);
        renforcer(tueur, 2.0);
        z.publier(new Evenement("nemesis_nee").a(l.getX(), l.getZ()).grav(4).acteur(f.victime.toString()).dit(f.nom));
        z.pont.zaevt("nemesis_nee " + f.victime + " " + f.nom);
    }

    private void equiper(LivingEntity e, Fiche f) {
        EntityEquipment eq = e.getEquipment();
        if (eq == null) return;
        if (f.casque != null) {
            eq.setHelmet(f.casque.clone());
            eq.setHelmetDropChance(1f);
        }
        if (f.arme != null) {
            eq.setItemInMainHand(f.arme.clone());
            eq.setItemInMainHandDropChance(1f);
        }
    }

    private void renommer(LivingEntity e, Fiche f) {
        String rang = f.rang == 1 ? "" : f.rang == 2 ? " l'Ancien" : ", Légende locale";
        e.setCustomName(f.base + " « " + f.nom + rang + (f.cicatrice ? " le Balafré" : "") + " »");
        e.setCustomNameVisible(true);
    }

    private static void renforcer(LivingEntity e, double k) {
        AttributeInstance a = e.getAttribute(Attribute.GENERIC_MAX_HEALTH);
        if (a == null) return;
        a.setBaseValue(Math.min(400, a.getBaseValue() * k));
        e.setHealth(a.getBaseValue());
    }

    // ---------------------------------------------------------------- combat

    public static String classe(org.bukkit.event.entity.EntityDamageEvent ev) {
        switch (ev.getCause()) {
            case FIRE:
            case FIRE_TICK:
            case LAVA:
                return "feu";
            case BLOCK_EXPLOSION:
            case ENTITY_EXPLOSION:
                return "explosion";
            case PROJECTILE: {
                if (ev instanceof org.bukkit.event.entity.EntityDamageByEntityEvent) {
                    String n = ((org.bukkit.event.entity.EntityDamageByEntityEvent) ev).getDamager().getType().name();
                    return n.contains("ARROW") || n.contains("TRIDENT") ? "fleche" : "balle";
                }
                return "balle";
            }
            default:
                return "melee";
        }
    }

    /** dégâts reçus par une Némésis : résistance, faiblesse, fuite à 30 %% de vie */
    public double degats(LivingEntity e, double d, String classe) {
        Fiche f = de(e);
        if (f == null) return d;
        if (classe.equals(f.resistance)) d *= 0.5;
        if (classe.equals(f.faiblesse)) d *= 1.5;
        AttributeInstance a = e.getAttribute(Attribute.GENERIC_MAX_HEALTH);
        double max = a == null ? 20 : a.getValue();
        if (!f.cicatrice && e.getHealth() - d < max * 0.3 && e.getHealth() - d > 0) {
            // blessé, il s'enfuit : il reviendra avec une cicatrice et une résistance à cette arme
            f.cicatrice = true;
            f.resistance = classe;
            z.cerveaux.panique(e.getLocation().clone().add(e.getLocation().getDirection().multiply(2)), 2);
            Bukkit.getScheduler().runTaskLater(z, () -> {
                if (!e.isDead()) {
                    f.entite = null;
                    e.remove();
                }
            }, 20L * 15);
            z.publier(new Evenement("nemesis_fuit").a(e.getLocation().getX(), e.getLocation().getZ()).grav(3).dit(f.nom));
        }
        return d;
    }

    /** la Némésis tombe */
    public void mort(LivingEntity e, Player tueur) {
        Fiche f = de(e);
        if (f == null) return;
        fiches.remove(f.id);
        Location l = e.getLocation();
        ItemStack tete = new ItemStack(Material.ZOMBIE_HEAD);
        ItemMeta m = tete.getItemMeta();
        if (m != null) {
            m.setDisplayName("§6Tête de " + f.nom);
            m.setLore(Collections.singletonList("§7Némésis de " + f.nomVictime + ", tombée au jour " + z.jour()));
            tete.setItemMeta(m);
        }
        l.getWorld().dropItemNaturally(l, tete);
        String t = tueur == null ? "-" : tueur.getUniqueId().toString();
        z.publier(new Evenement("nemesis_vaincue").a(l.getX(), l.getZ()).grav(4).acteur(t).acteur(f.victime.toString()).dit(f.nom));
        z.pont.zaevt("nemesis_tue " + t + " " + f.victime + " " + f.nom);
    }

    // ---------------------------------------------------------------- revanche (le Directeur la décide)

    public boolean revanche(Player p) {
        for (Fiche f : fiches.values()) {
            if (!p.getUniqueId().equals(f.victime)) continue;
            if (f.entite != null && Bukkit.getEntity(f.entite) != null) return false;
            if (z.jour() < f.jourNe + 1) return false;
            Location l = z.mat.pointHorsVue(p, 30, 50);
            if (l == null) return false;
            Zombie zb = l.getWorld().spawn(l, Zombie.class, x -> {
                x.setAdult();
                x.setRemoveWhenFarAway(false);
                x.addScoreboardTag("za_nemesis");
                x.addScoreboardTag("za_nem_" + f.id);
                x.addScoreboardTag("za_veteran");
                x.addScoreboardTag("za_cerveau_libre");
            });
            equiper(zb, f);
            renommer(zb, f);
            renforcer(zb, 2.0 + f.rang * 0.5);
            zb.setTarget(p);
            f.entite = zb.getUniqueId();
            z.pont.zaevt("nemesis_revient " + p.getUniqueId() + " " + f.nom);
            return true;
        }
        return false;
    }

    // ---------------------------------------------------------------- vétérans (84) : survivre plusieurs jours, c'est grandir

    void tick1s() {
        if (rng.nextInt(60) != 0) return;
        int n = 0;
        for (Player p : z.mondePrincipal().getPlayers()) {
            for (Entity e : p.getNearbyEntities(48, 16, 48)) {
                if (!(e instanceof Monster) || n++ > 60) continue;
                int t = e.getTicksLived();
                LivingEntity le = (LivingEntity) e;
                if (e.getScoreboardTags().contains("za_nemesis")) continue;
                String nom = le.getCustomName() == null ? "Zombie" : le.getCustomName().replaceAll("§.", "");
                if (t > 144_000 && !e.getScoreboardTags().contains("za_legende")) {
                    e.addScoreboardTag("za_legende");
                    Graphe.Lieu lieu;
                    synchronized (z.monde) {
                        lieu = z.monde.graphe.lieuProche(e.getLocation().getX(), e.getLocation().getZ(), 500);
                    }
                    String titre = EPITHETES[rng.nextInt(EPITHETES.length)] + " de " + (lieu == null ? "la région" : lieu.nom);
                    le.setCustomName(base(nom) + " « " + titre + ", Légende locale »");
                    le.setCustomNameVisible(true);
                    renforcer(le, 1.5);
                    z.publier(new Evenement("legende_locale").a(e.getLocation().getX(), e.getLocation().getZ()).grav(3).dit(titre));
                    z.pont.zaevt("bestiaire_avis " + titre);
                } else if (t > 72_000 && !e.getScoreboardTags().contains("za_ancien")) {
                    e.addScoreboardTag("za_ancien");
                    le.setCustomName(base(nom) + " « l'Ancien »");
                    renforcer(le, 1.3);
                } else if (t > 24_000 && !e.getScoreboardTags().contains("za_veteran")) {
                    e.addScoreboardTag("za_veteran");
                    le.setCustomName(base(nom) + " « Vétéran »");
                    renforcer(le, 1.5);
                    le.setRemoveWhenFarAway(false);
                }
            }
        }
        // la Némésis réelle a disparu (tronçon déchargé) : elle redevient virtuelle
        for (Fiche f : fiches.values()) if (f.entite != null && Bukkit.getEntity(f.entite) == null) f.entite = null;
    }

    private static String base(String nom) {
        int k = nom.indexOf(" «");
        return k > 0 ? nom.substring(0, k) : nom;
    }

    void jour() {
    }

    public String faiblesse(String id) {
        Fiche f = fiches.get(id);
        if (f == null) return "";
        f.faiblesseConnue = true;
        return f.faiblesse;
    }

    void sauver(ConfigurationSection s) {
        for (Fiche f : fiches.values()) {
            ConfigurationSection c = s.createSection(f.id);
            c.set("victime", f.victime.toString());
            c.set("nom_victime", f.nomVictime);
            c.set("nom", f.nom);
            c.set("base", f.base);
            c.set("rang", f.rang);
            c.set("tues", f.tues);
            c.set("resistance", f.resistance);
            c.set("faiblesse", f.faiblesse);
            c.set("faiblesse_connue", f.faiblesseConnue);
            c.set("cicatrice", f.cicatrice);
            c.set("casque", f.casque);
            c.set("arme", f.arme);
            c.set("jour", f.jourNe);
            c.set("lieu", f.lieu);
        }
    }

    void charger(ConfigurationSection s) {
        if (s == null) return;
        for (String k : s.getKeys(false)) {
            ConfigurationSection c = s.getConfigurationSection(k);
            if (c == null) continue;
            Fiche f = new Fiche();
            f.id = k;
            try {
                f.victime = UUID.fromString(c.getString("victime", ""));
            } catch (IllegalArgumentException e) {
                continue;
            }
            f.nomVictime = c.getString("nom_victime", "");
            f.nom = c.getString("nom", "la Némésis");
            f.base = c.getString("base", "Zombie");
            f.rang = c.getInt("rang", 1);
            f.tues = c.getInt("tues", 1);
            f.resistance = c.getString("resistance", "");
            f.faiblesse = c.getString("faiblesse", "melee");
            f.faiblesseConnue = c.getBoolean("faiblesse_connue");
            f.cicatrice = c.getBoolean("cicatrice");
            f.casque = c.getItemStack("casque");
            f.arme = c.getItemStack("arme");
            f.jourNe = c.getInt("jour");
            f.lieu = c.getString("lieu", "");
            fiches.put(k, f);
        }
    }
}
