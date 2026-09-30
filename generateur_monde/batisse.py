# -*- coding: utf-8 -*-
"""batisse : construction des sites de la région (hors Saint-Aurèle et autobus, qui viennent de ZAMonde).

Chaque fonction <type>(site, plan) renvoie une sites.Structure, sol de marche à y=64 (comme la ville), centrée sur
(0, 0). Les états de blocs passent par za_blocs.S() (validés : vanilla 1.20.1 + mods décoratifs installés).
Après construction : connexions (vitres, clôtures), formes d'escaliers, habillage moddé, puis passe « apocalypse ».
"""
import math
import random
import zlib

import numpy as np

import sites as SI
from za_blocs import S, AIR, Monde, OPP, CW, CCW, parse, MODERNE
import za_meubles as ZM
from za_meubles import Ctx, Repere
import za_rue as RU
import za_moderne

VEC = {'north': (0, -1), 'south': (0, 1), 'west': (-1, 0), 'east': (1, 0)}
MURS = ['white_terracotta', 'light_gray_concrete', 'yellow_terracotta', 'light_blue_terracotta', 'bricks', 'spruce_planks',
        'birch_planks', 'cyan_terracotta', 'white_concrete', 'stone_bricks', 'mud_bricks', 'orange_terracotta']
TOITS = ['spruce', 'dark_oak', 'stone_brick', 'deepslate_tile', 'red_nether_brick']
COULEURS_AUTO = ['red', 'blue', 'white', 'black', 'gray', 'light_gray', 'green', 'brown', 'cyan', 'yellow']


# ============================================================================ cadre commun
class Chantier:
    def __init__(self, site, W, D, H=48, sol='grass'):
        self.site = site
        self.rng = random.Random(site.get('graine', zlib.crc32(site['id'].encode()) & 0xFFFF))  # crc32 : stable d'un processus à l'autre
        self.m = Monde(-(W // 2), 58, -(D // 2), W, H, D)
        self.ctx = Ctx(self.m, site.get('graine', 1250))
        self.coffres = []
        self.lieux = []            # sous-lieux (type, nom, x, z, demi-largeur, demi-profondeur) en coordonnées locales
        m = self.m
        x0, z0, x1, z1 = m.x0, m.z0, m.x0 + W - 1, m.z0 + D - 1
        m.fill(x0, 58, z0, x1, 62, z1, S('dirt'))
        m.fill(x0, 63, z0, x1, 63, z1, S('grass_block', snowy=False) if sol == 'grass' else S(sol))
        self.R0 = Repere(self.ctx, 0, 0)
        self.x0, self.z0, self.x1, self.z1 = x0, z0, x1, z1

    def rep(self, ox, oz, front):
        """Repère d'un bâtiment dont la façade (b croissant) regarde vers `front`."""
        v = VEC[front]
        u = {'south': (1, 0), 'north': (-1, 0), 'east': (0, -1), 'west': (0, 1)}[front]
        return Repere(self.ctx, ox, oz, u, v)

    def lieu(self, R, L, P, genre, nom):
        (xa, za), (xb, zb) = R.xz(0, 0), R.xz(L - 1, P - 1)
        self.lieux.append((genre, nom, (xa + xb) // 2, (za + zb) // 2, abs(xb - xa) // 2 + 3, abs(zb - za) // 2 + 3))

    def coffre(self, R, a, y, b, regard, butin=SI.LOOT_MAISON, baril=False):
        if baril:
            R.set(a, y, b, R.S('barrel', facing=regard, open=False))
        else:
            R.set(a, y, b, R.S('chest', facing=regard, type='single', waterlogged=False))
        x, z = R.xz(a, b)
        self.coffres.append((x, y, z, butin))

    def panneau(self, x, y, z, lignes, rotation=0, couleur='black', mur=None):
        if mur:
            self.m.set(x, y, z, S('oak_wall_sign', facing=mur, waterlogged=False))
        else:
            self.m.set(x, y, z, S('oak_sign', rotation=rotation, waterlogged=False))
        self.m.sign(x, y, z, lignes, couleur)

    def route(self, x1, z1, x2, z2, st=None, ligne=True):
        m = self.m
        m.fill(x1, 63, z1, x2, 63, z2, st or S('gray_concrete'))
        m.vide(x1, 64, z1, x2, 70, z2)
        if ligne:
            if abs(x2 - x1) >= abs(z2 - z1):
                zc = (z1 + z2) // 2
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    if x % 6 < 3:
                        m.set(x, 63, zc, S('yellow_concrete'))
            else:
                xc = (x1 + x2) // 2
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    if z % 6 < 3:
                        m.set(xc, 63, z, S('yellow_concrete'))

    def voitures(self, x1, z1, x2, z2, n, direction):
        for _ in range(n):
            x = self.rng.randint(min(x1, x2), max(x1, x2))
            z = self.rng.randint(min(z1, z2), max(z1, z2))
            kind = self.rng.choice(['auto', 'auto', 'auto', 'brulee', 'taxi'])
            try:
                RU.voiture(self.R0, x, z, direction if self.rng.random() < 0.7 else CW[direction],
                           self.rng.choice(COULEURS_AUTO), 64, kind, portes=self.rng.random() < 0.4)
            except Exception:
                pass

    def terminer(self, degats=0.5):
        m = self.m
        # lampes : éteintes (plus de courant depuis le Jour 8)
        for l in self.ctx.lampes:
            m.set(l['x'], l['y'], l['z'], l['off'])
        m.passe_connexions()
        m.passe_escaliers()
        za_moderne.habiller(self.ctx)
        degrader(m, self.rng, degats)
        err = [e for e in m.verifier() if 'porte' in e or 'lit' in e or 'inconnu' in e]
        if err:
            print('  [%s] %d avertissements (%s)' % (self.site['id'], len(err), err[0]))
        st = SI.Structure.depuis_monde(self.site['id'], m, self.coffres)
        st.lieux = list(self.lieux)
        return st


# ============================================================================ passe « apocalypse »
def degrader(m, rng, force=0.5):
    if force <= 0:
        return
    H, D, W = m.a.shape
    pal = m.pal
    rs = np.random.default_rng(rng.randint(0, 1 << 30))
    alea = rs.random(m.a.shape)
    verre = np.array(['glass_pane' in p or p == 'minecraft:glass' for p in pal])
    toile = m.id(S('cobweb'))
    est_verre = verre[m.a]
    m.a[est_verre & (alea < 0.45 * force)] = 0
    m.a[est_verre & (alea > 1 - 0.05 * force)] = toile
    # lierre sur les murs extérieurs
    solide = np.array([p != AIR and not any(k in p for k in ('glass', 'pane', 'door', 'sign', 'leaves', 'grass', 'flower', 'fence',
                                                            'wall', 'stairs', 'slab', 'carpet', 'rail', 'torch', 'lantern', 'bed',
                                                            'water', 'lava', 'button', 'plate', 'trapdoor', 'vine', 'bars', 'banner'))
                       and p.split('[')[0] not in ('minecraft:air',) for p in pal])
    # ids du lierre créés d'abord : la table « solide » couvre toute la palette
    lierres = {}
    for face in ('east', 'west', 'south', 'north'):
        props = {k: 'false' for k in ('east', 'north', 'south', 'up', 'west')}
        props[face] = 'true'
        lierres[face] = m.id(S('vine', **props))
    herbe = m.id(S('grass'))
    solide = np.concatenate([solide, np.zeros(len(m.pal) - len(solide), bool)])
    src = solide[m.a]
    air = m.a == 0
    for (dx, dz, face) in ((1, 0, 'east'), (-1, 0, 'west'), (0, 1, 'south'), (0, -1, 'north')):
        voisin = np.zeros(m.a.shape, bool)
        if dx:
            if dx > 0:
                voisin[:, :, :-1] = src[:, :, 1:]
            else:
                voisin[:, :, 1:] = src[:, :, :-1]
        else:
            if dz > 0:
                voisin[:, :-1, :] = src[:, 1:, :]
            else:
                voisin[:, 1:, :] = src[:, :-1, :]
        lierre = lierres[face]
        cible = air & voisin & (alea < 0.035 * force)
        cible[:8] = False
        m.a[cible] = lierre
        air = m.a == 0
    # herbes folles sur le gazon
    gazon = np.array([p.startswith('minecraft:grass_block') for p in m.pal])
    dessus = np.zeros(m.a.shape, bool)
    dessus[1:] = gazon[m.a[:-1]]
    m.a[(m.a == 0) & dessus & (alea < 0.35 * force + 0.1)] = herbe


# ============================================================================ bâtiments
def maison(ch, R, L, P, etages=1, mur=None, toit=None, bois='spruce', butin=SI.LOOT_MAISON):
    rng = ch.rng
    mur = S(mur or rng.choice(MURS))
    toit = toit or rng.choice(TOITS)
    hm = 4 * etages
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 63 + hm, P - 1, mur)
    R.vide(1, 64, 1, L - 2, 63 + hm, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('oak_planks'))
    for e in range(1, etages):
        R.fill(1, 63 + 4 * e, 1, L - 2, 63 + 4 * e, P - 2, S('oak_planks'))
    R.fill(0, 64 + hm, 0, L - 1, 64 + hm, P - 1, S('spruce_planks'))
    # fenêtres
    for e in range(etages):
        y = 65 + 4 * e
        for a in range(2, L - 2, 3):
            for b in (0, P - 1):
                R.set(a, y, b, S('glass_pane'))
                R.set(a, y + 1, b, S('glass_pane'))
        for b in range(2, P - 2, 3):
            for a in (0, L - 1):
                R.set(a, y, b, S('glass_pane'))
                R.set(a, y + 1, b, S('glass_pane'))
    # porte + perron
    pa = L // 2
    R.vide(pa, 64, P - 1, pa, 65, P - 1)
    ZM.porte(R, pa, 64, P - 1, 'north', 'oak' if rng.random() < 0.5 else 'spruce', 'left', rng.random() < 0.25)
    R.fill(pa - 1, 63, P, pa + 1, 63, P + 1, S('spruce_planks'))
    # toit à deux versants (faîte le long de a)
    yr = 65 + hm
    n = (P + 1) // 2
    for k in range(n + 1):
        y = yr + k
        if k - 1 <= P - k:
            R.fill(-1, y, k - 1, L, y, k - 1, R.S(toit + '_stairs', facing='south', half='bottom'))
            R.fill(-1, y, P - k, L, y, P - k, R.S(toit + '_stairs', facing='north', half='bottom'))
        if k <= P - 1 - k:
            R.fill(0, y, k, 0, y, P - 1 - k, mur)
            R.fill(L - 1, y, k, L - 1, y, P - 1 - k, mur)
            R.vide(1, y, k, L - 2, y, P - 1 - k)
    # intérieur (rez-de-chaussée)
    if L >= 8 and P >= 8:
        ZM.comptoir_cuisine(R, 1, 64, 1, 'south', min(4, L - 4), bois, evier_i=1, cuis_i=2, haut=True)
        ZM.table(R, L // 2, 64, P // 2, bois)
        ZM.chaise(R, L // 2 - 1, 64, P // 2, 'east', bois)
        ZM.chaise(R, L // 2 + 1, 64, P // 2, 'west', bois)
        ZM.canape(R, 1, 64, P - 3, 'east', 2, 'dark_oak', 'dark_oak')
        ZM.lit(R, L - 2, 64, 3, 'north', rng.choice(['white', 'blue', 'red', 'green', 'light_gray']))
        ch.coffre(R, L - 2, 64, P - 2, 'west', butin)
        if L >= 10:
            ZM.bibliotheque(R, L - 2, 64, P // 2, 2)
    if etages > 1:
        ZM.lit(R, 2, 68, 2, 'north', 'white')
        ch.coffre(R, L - 2, 68, 1, 'south', butin)


def eglise(ch, R, L=13, P=21):
    pierre = S('stone_bricks')
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 71, P - 1, pierre)
    R.vide(1, 64, 1, L - 2, 71, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('polished_andesite'))
    for b in range(3, P - 3, 3):
        for a in (0, L - 1):
            R.fill(a, 66, b, a, 69, b, S('light_blue_stained_glass_pane'))
    # bancs
    for b in range(5, P - 4, 2):
        for a in (2, L - 5):
            if MODERNE:
                for i in range(3):
                    R.set(a + i, 64, b, R.S('handcrafted:spruce_bench', facing='north', shape='single', color='red'))
            else:
                ZM.canape(R, a, 64, b, 'north', 3, 'spruce', 'spruce')
    R.fill(L // 2 - 1, 64, 2, L // 2 + 1, 64, 2, S('quartz_block'))
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'dark_oak')
    # clocher
    R.fill(L // 2 - 2, 64, P - 4, L // 2 + 2, 84, P, pierre)
    R.vide(L // 2 - 1, 72, P - 3, L // 2 + 1, 83, P - 1)
    R.set(L // 2, 80, P - 2, S('bell', attachment='ceiling', facing='north', powered=False))
    R.fill(L // 2, 85, P - 2, L // 2, 88, P - 2, S('stone_brick_wall'))
    R.fill(L // 2 - 1, 87, P - 2, L // 2 + 1, 87, P - 2, S('stone_brick_wall'))
    # toit
    for k in range(L // 2 + 2):
        R.fill(k - 1, 72 + k, 0, k - 1, 72 + k, P - 5, R.S('deepslate_tile_stairs', facing='east', half='bottom'))
        R.fill(L - k, 72 + k, 0, L - k, 72 + k, P - 5, R.S('deepslate_tile_stairs', facing='west', half='bottom'))
    ch.coffre(R, 1, 64, 1, 'south', SI.LOOT_MAISON)


def commerce(ch, R, L, P, nom, genre='depanneur'):
    mur = S(ch.rng.choice(['bricks', 'light_gray_concrete', 'white_concrete']))
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 68, P - 1, mur)
    R.vide(1, 64, 1, L - 2, 67, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('smooth_stone'))
    R.fill(0, 69, 0, L - 1, 69, P - 1, S('smooth_stone_slab', type='bottom'))
    # vitrine
    R.fill(1, 65, P - 1, L - 2, 66, P - 1, S('glass_pane'))
    ZM.porte(R, 2, 64, P - 1, 'north', 'iron' if not MODERNE else 'oak')
    # rayonnages et comptoir
    for b in range(2, P - 3, 2):
        R.fill(3, 64, b, L - 3, 65, b, R.S('barrel', facing='up', open=False))
    for b in range(2, P - 3, 4):
        ch.coffre(R, 3, 64, b, 'up', SI.LOOT_VILLE, baril=True)
    R.fill(L - 3, 64, P - 3, L - 2, 64, P - 3, S('smooth_quartz'))
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 67, z, ['', nom.upper()[:15], '', ''], mur=R.d('south'))


def garage(ch, R, L=12, P=12, nom='GARAGE'):
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 69, P - 1, S('light_gray_concrete'))
    R.vide(1, 64, 1, L - 2, 68, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('gray_concrete'))
    R.vide(2, 64, P - 1, L - 3, 67, P - 1)
    R.fill(2, 67, P - 1, L - 3, 67, P - 1, S('iron_trapdoor', facing='north', half='top', open=False, powered=False, waterlogged=False))
    x, z = R.xz(L // 2, P // 2)
    try:
        RU.voiture(ch.R0, x, z, R.d('south'), ch.rng.choice(COULEURS_AUTO), 64, 'auto', portes=True)
    except Exception:
        pass
    ch.coffre(R, 1, 64, 1, 'south', SI.LOOT_VILLE)
    R.fill(1, 64, 2, 1, 65, 5, S('smithing_table'))
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 68, z, ['', nom, 'Mécanique générale', ''], mur=R.d('south'))


def ecole(ch, R, L=15, P=13, village=''):
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 69, P - 1, S('bricks'))
    R.vide(1, 64, 1, L - 2, 68, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('white_terracotta'))
    R.fill(0, 70, 0, L - 1, 70, P - 1, S('smooth_stone_slab', type='bottom'))
    for a in range(2, L - 2, 2):
        for b in (0, P - 1):
            R.fill(a, 65, b, a, 67, b, S('glass_pane'))
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'oak')
    # classe : pupitres en rangées face au tableau noir
    R.fill(2, 65, 1, L - 3, 67, 1, S('black_concrete'))
    for b in range(4, P - 3, 2):
        for a in range(2, L - 2, 3):
            ZM.table(R, a, 64, b, 'birch')
            ZM.chaise(R, a, 64, b + 1, 'north', 'birch')
    ch.coffre(R, L - 2, 64, 1, 'south', SI.LOOT_MAISON)
    ch.coffre(R, 1, 64, 1, 'south', SI.LOOT_MAISON, baril=True)
    # mât de drapeau (bleu et blanc) devant l'entrée
    x, z = R.xz(1, P + 2)
    ch.m.fill(x, 64, z, x, 72, z, S('iron_bars'))
    ch.m.set(x, 71, z, S('white_wool')); ch.m.set(x, 72, z, S('blue_wool'))
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 69, z, ['ÉCOLE', 'PRIMAIRE', village[:15], ''], mur=R.d('south'))
    ch.lieu(R, L, P, 'ecole', 'École primaire de ' + village if village else 'École primaire')


def clinique(ch, R, L=13, P=13, village=''):
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 68, P - 1, S('white_concrete'))
    R.vide(1, 64, 1, L - 2, 67, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('light_gray_concrete'))
    R.fill(0, 69, 0, L - 1, 69, P - 1, S('smooth_stone_slab', type='bottom'))
    # croix rouge sur la façade
    c = L // 2
    for (a, y) in ((c, 68), (c, 67), (c, 66), (c - 1, 67), (c + 1, 67)):
        R.set(a, y, P - 1, S('red_concrete'))
    R.fill(2, 65, P - 1, c - 2, 66, P - 1, S('glass_pane'))
    ZM.porte(R, c + 2, 64, P - 1, 'north', 'iron' if not MODERNE else 'oak')
    # salle d'attente, lits, pharmacie
    for a in range(1, L - 1, 3):
        ZM.lit(R, a, 64, 2, 'north', 'white')
    R.fill(1, 64, P - 4, 3, 64, P - 4, S('smooth_quartz'))
    for b in range(5, P - 5, 2):
        ch.coffre(R, L - 2, 64, b, 'west', SI.LOOT_VILLE, baril=True)
    ch.coffre(R, L - 2, 64, P - 3, 'west', SI.LOOT_LABO)
    x, z = R.xz(c, P)
    ch.panneau(x, 69, z, ['CLINIQUE', 'MÉDICALE', village[:15], ''], mur=R.d('south'))
    ch.lieu(R, L, P, 'clinique', 'Clinique médicale de ' + village if village else 'Clinique médicale')


def caserne(ch, R, L=15, P=13, village=''):
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 70, P - 1, S('red_nether_bricks' if ch.rng.random() < 0.5 else 'bricks'))
    R.vide(1, 64, 1, L - 2, 69, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('gray_concrete'))
    R.fill(0, 71, 0, L - 1, 71, P - 1, S('smooth_stone_slab', type='bottom'))
    # grande porte de garage (à moitié levée) et camion rouge
    R.vide(2, 64, P - 1, 8, 68, P - 1)
    R.fill(2, 68, P - 1, 8, 68, P - 1, S('iron_trapdoor', facing='north', half='top', open=False, powered=False, waterlogged=False))
    x, z = R.xz(5, P // 2)
    try:
        RU.voiture(ch.R0, x, z, R.d('south'), 'red', 64, 'auto', portes=True)
    except Exception:
        pass
    ZM.porte(R, L - 3, 64, P - 1, 'north', 'spruce')
    # vestiaires : barils (équipement), tour de séchage des boyaux
    for b in range(1, P - 2, 2):
        ch.coffre(R, L - 2, 64, b, 'west', SI.LOOT_VILLE, baril=True)
    R.fill(L - 4, 64, 0, L - 2, 78, 2, S('bricks'))
    R.vide(L - 3, 72, 1, L - 3, 77, 1)
    x, z = R.xz(5, P)
    ch.panneau(x, 70, z, ['CASERNE', 'DE POMPIERS', village[:15], ''], mur=R.d('south'))
    ch.lieu(R, L, P, 'caserne', 'Caserne de pompiers de ' + village if village else 'Caserne de pompiers')


# ============================================================================ sites
def village(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D)
    m, rng = ch.m, ch.rng
    hw, hd = W // 2, D // 2
    # rues en croix + trottoirs
    ch.route(ch.x0, -4, ch.x1, 4)
    ch.route(-4, ch.z0, 4, ch.z1)
    m.fill(ch.x0, 63, -6, ch.x1, 63, -5, S('smooth_stone'))
    m.fill(ch.x0, 63, 5, ch.x1, 63, 6, S('smooth_stone'))
    m.fill(-6, 63, ch.z0, -5, 63, ch.z1, S('smooth_stone'))
    m.fill(5, 63, ch.z0, 6, 63, ch.z1, S('smooth_stone'))
    speciaux = ['eglise', 'depanneur', 'garage', 'casse_croute', 'ecole', 'clinique', 'caserne']
    rng.shuffle(speciaux)
    lots = []
    for x in range(-hw + 12, hw - 12, 17):
        if abs(x) < 16:
            continue
        lots.append(('rue_ew_n', x))
        lots.append(('rue_ew_s', x))
    for z in range(-hd + 12, hd - 12, 17):
        if abs(z) < 16:
            continue
        lots.append(('rue_ns_o', z))
        lots.append(('rue_ns_e', z))
    rng.shuffle(lots)
    for i, (cote, c) in enumerate(lots):
        spec = speciaux[i] if i < len(speciaux) else None
        L, P = {'eglise': (13, 21), 'ecole': (15, 13), 'clinique': (13, 13), 'caserne': (15, 13)}.get(
            spec, (rng.choice((9, 10, 11)), rng.choice((9, 10, 11))))
        if cote == 'rue_ew_n':
            R = ch.rep(c - L // 2, -8 - (P - 1), 'south')
        elif cote == 'rue_ew_s':
            R = ch.rep(c + L // 2, 8 + (P - 1), 'north')
        elif cote == 'rue_ns_o':
            R = ch.rep(-8 - (P - 1), c + L // 2, 'east')
        else:
            R = ch.rep(8 + (P - 1), c - L // 2, 'west')
        # le lot doit tenir dans le site
        coins = [R.xz(0, 0), R.xz(L - 1, P - 1)]
        if any(not (ch.x0 + 2 <= x <= ch.x1 - 2 and ch.z0 + 2 <= z <= ch.z1 - 2) for x, z in coins):
            continue
        vn = site['nom']
        if spec == 'eglise':
            eglise(ch, R, L, P)
            ch.lieu(R, L, P, 'eglise', 'Église de ' + vn)
        elif spec == 'depanneur':
            commerce(ch, R, L + 2, P + 2, 'Dépanneur')
            ch.lieu(R, L + 2, P + 2, 'depanneur', 'Dépanneur de ' + vn)
        elif spec == 'casse_croute':
            commerce(ch, R, L + 2, P, 'Casse-croûte')
            ch.lieu(R, L + 2, P, 'depanneur', 'Casse-croûte de ' + vn)
        elif spec == 'garage':
            garage(ch, R)
            ch.lieu(R, 12, 12, 'garage', 'Garage de ' + vn)
        elif spec == 'ecole':
            ecole(ch, R, L, P, vn)
        elif spec == 'clinique':
            clinique(ch, R, L, P, vn)
        elif spec == 'caserne':
            caserne(ch, R, L, P, vn)
        else:
            maison(ch, R, L, P, etages=2 if rng.random() < 0.3 else 1)
            # cour : clôture à piquets et arbre
            for a in range(-1, L + 1):
                R.set(a, 64, -2, S('spruce_fence'))
            try:
                x, z = R.xz(L // 2, -4)
                if ch.x0 + 3 < x < ch.x1 - 3 and ch.z0 + 3 < z < ch.z1 - 3:
                    RU.arbre_rue(ch.R0, x, z, rng)
            except Exception:
                pass
    # lampadaires, voitures abandonnées, panneaux d'entrée
    for x in range(ch.x0 + 8, ch.x1 - 8, 24):
        if abs(x) > 8:
            RU.lampadaire(ch.R0, x, -6, 'south')
    for z in range(ch.z0 + 8, ch.z1 - 8, 24):
        if abs(z) > 8:
            RU.lampadaire(ch.R0, 6, z, 'west')
    ch.voitures(ch.x0 + 10, -3, ch.x1 - 10, 3, 6, 'east')
    ch.voitures(-3, ch.z0 + 10, 3, ch.z1 - 10, 4, 'south')
    for (x, z, rot) in ((ch.x0 + 3, 7, 4), (ch.x1 - 3, -7, 12), (7, ch.z0 + 3, 8), (-7, ch.z1 - 3, 0)):
        ch.panneau(x, 64, z, ['Bienvenue à', site['nom'][:15], site['nom'][15:30], ''], rotation=rot)
    return ch.terminer(0.6)


def ferme(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D)
    m, rng = ch.m, ch.rng
    R = ch.rep(-W // 2 + 6, -D // 2 + 6, 'south')
    maison(ch, R, 11, 10, etages=2, mur=rng.choice(['white_terracotta', 'birch_planks', 'bricks']), toit='dark_oak')
    # grange rouge
    G = ch.rep(4, -D // 2 + 4, 'south')
    G.fill(0, 59, 0, 15, 63, 19, S('stone'))
    G.fill(0, 64, 0, 15, 70, 19, S('red_terracotta'))
    G.vide(1, 64, 1, 14, 70, 18)
    G.fill(1, 63, 1, 14, 63, 18, S('spruce_planks'))
    G.vide(5, 64, 19, 10, 68, 19)
    for k in range(9):
        G.fill(k - 1, 71 + k // 2, 0, k - 1, 71 + k // 2, 19, G.S('dark_oak_stairs', facing='east', half='bottom'))
        G.fill(16 - k, 71 + k // 2, 0, 16 - k, 71 + k // 2, 19, G.S('dark_oak_stairs', facing='west', half='bottom'))
    G.fill(7, 75, 0, 8, 75, 19, S('dark_oak_planks'))
    for i in range(12):
        G.set(rng.randint(2, 13), 64, rng.randint(2, 16), S('hay_block', axis='y'))
    ch.coffre(G, 2, 64, 2, 'south', SI.LOOT_MAISON)
    # silo
    cx, cz = 25, -D // 2 + 8
    for y in range(64, 80):
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if 6 <= dx * dx + dz * dz <= 10:
                    m.set(cx + dx, y, cz + dz, S('light_gray_terracotta') if y < 78 else S('iron_block'))
    # champs
    cultures = [('wheat', 7), ('carrots', 7), ('potatoes', 7), ('beetroots', 3)]
    for i, (x1, z1) in enumerate(((-W // 2 + 4, 4), (-W // 2 + 4 + (W - 12) // 2 + 2, 4))):
        cult, amax = cultures[(i + site.get('graine', 0)) % len(cultures)]
        for x in range(x1, x1 + (W - 12) // 2):
            for z in range(z1, D // 2 - 4):
                if (z - z1) % 5 == 2:
                    m.set(x, 63, z, S('water'))
                else:
                    m.set(x, 63, z, S('farmland', moisture=7))
                    if rng.random() < 0.8:
                        m.set(x, 64, z, S(cult, age=rng.randint(0, amax)))
    for x in range(-W // 2 + 2, W // 2 - 1):
        m.set(x, 64, 2, S('oak_fence'))
        m.set(x, 64, D // 2 - 2, S('oak_fence'))
    # tracteur (blocs)
    m.fill(-2, 64, -4, 0, 65, -2, S('green_concrete'))
    m.set(-1, 66, -3, S('black_stained_glass'))
    for (x, z) in ((-3, -4), (1, -4), (-3, -2), (1, -2)):
        m.set(x, 64, z, S('black_concrete'))
    ch.panneau(-W // 2 + 2, 64, -D // 2 + 18, [site['nom'][:15], 'Œufs frais', 'Blé d\'Inde', ''], rotation=4)
    return ch.terminer(0.45)


def militaire(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D)
    m, rng = ch.m, ch.rng
    m.fill(ch.x0 + 2, 63, ch.z0 + 2, ch.x1 - 2, 63, ch.z1 - 2, S('coarse_dirt'))
    # clôture double (grillage + barbelés)
    for x in range(ch.x0 + 2, ch.x1 - 1):
        for z in (ch.z0 + 2, ch.z1 - 2):
            m.fill(x, 64, z, x, 66, z, S('iron_bars'))
            m.set(x, 67, z, S('cobweb') if rng.random() < 0.3 else S('iron_bars'))
    for z in range(ch.z0 + 2, ch.z1 - 1):
        for x in (ch.x0 + 2, ch.x1 - 2):
            m.fill(x, 64, z, x, 66, z, S('iron_bars'))
    # entrée (sud) : barrière + guérite
    m.vide(-4, 64, ch.z1 - 2, 4, 67, ch.z1 - 2)
    ch.route(-4, 0, 4, ch.z1, S('gray_concrete'), False)
    m.fill(-5, 64, ch.z1 - 5, -5, 64, ch.z1 - 5, S('spruce_fence'))
    m.fill(-4, 65, ch.z1 - 5, 4, 65, ch.z1 - 5, S('red_concrete'))
    gu = ch.rep(6, ch.z1 - 9, 'south')
    gu.fill(0, 64, 0, 4, 67, 4, S('green_terracotta'))
    gu.vide(1, 64, 1, 3, 66, 3)
    gu.fill(1, 66, 4, 3, 66, 4, S('glass_pane'))
    ZM.porte(gu, 2, 64, 0, 'south', 'iron')
    ch.panneau(-6, 65, ch.z1 - 1, ['ZONE MILITAIRE', 'ACCÈS INTERDIT', 'Forces armées', 'canadiennes'], rotation=0, couleur='red')
    # casernes
    for i, z in enumerate(range(ch.z0 + 10, ch.z0 + 10 + 3 * 22, 22)):
        C = ch.rep(ch.x0 + 10, z, 'south')
        C.fill(0, 59, 0, 29, 63, 13, S('stone'))
        C.fill(0, 64, 0, 29, 67, 13, S('green_terracotta'))
        C.vide(1, 64, 1, 28, 67, 12)
        C.fill(1, 63, 1, 28, 63, 12, S('spruce_planks'))
        C.fill(0, 68, 0, 29, 68, 13, S('gray_concrete'))
        for a in range(3, 28, 4):
            C.set(a, 65, 0, S('glass_pane'))
            C.set(a, 65, 13, S('glass_pane'))
            ZM.lit(C, a, 64, 2, 'north', 'green')
            ZM.lit(C, a, 64, 11, 'south', 'green')
            ch.coffre(C, a + 1, 64, 1, 'south', SI.LOOT_MILITAIRE)
        ZM.porte(C, 14, 64, 13, 'north', 'iron')
        px, pz = C.xz(12, 15)
        ch.panneau(px, 64, pz, ['', 'CASERNE %d' % (i + 1), 'Bravo-%d' % (i + 1), ''])
    # poste de commandement
    Q = ch.rep(ch.x1 - 40, ch.z0 + 12, 'south')
    maison(ch, Q, 20, 14, etages=2, mur='stone_bricks', toit='deepslate_tile', butin=SI.LOOT_MILITAIRE)
    # hélisurface
    hx, hz = ch.x1 - 30, ch.z1 - 30
    m.fill(hx - 8, 63, hz - 8, hx + 8, 63, hz + 8, S('gray_concrete'))
    for dz in range(-4, 5):
        m.set(hx - 3, 63, hz + dz, S('yellow_concrete'))
        m.set(hx + 3, 63, hz + dz, S('yellow_concrete'))
    for dx in range(-3, 4):
        m.set(hx + dx, 63, hz, S('yellow_concrete'))
    # tours de guet
    for (x, z) in ((ch.x0 + 4, ch.z0 + 4), (ch.x1 - 4, ch.z0 + 4), (ch.x0 + 4, ch.z1 - 4), (ch.x1 - 4, ch.z1 - 4)):
        for (dx, dz) in ((0, 0), (2, 0), (0, 2), (2, 2)):
            m.fill(x + dx - 1, 64, z + dz - 1, x + dx - 1, 72, z + dz - 1, S('spruce_log', axis='y'))
        m.fill(x - 2, 73, z - 2, x + 2, 73, z + 2, S('spruce_planks'))
        for dx in range(-2, 3):
            for dz in (-2, 2):
                m.set(x + dx, 74, z + dz, S('spruce_fence'))
                m.set(x + dz, 74, z + dx, S('spruce_fence'))
    # sacs de sable, tentes, camions, caisses de munitions
    for _ in range(14):
        x, z = rng.randint(ch.x0 + 8, ch.x1 - 8), rng.randint(ch.z0 + 80, ch.z1 - 10)
        horiz = rng.random() < 0.5
        for k in range(5):
            m.set(x + (k if horiz else 0), 64, z + (0 if horiz else k), S('sandstone_wall'))
    for _ in range(6):
        x, z = rng.randint(ch.x0 + 10, ch.x1 - 16), rng.randint(ch.z0 + 80, ch.z1 - 16)
        T = ch.rep(x, z, 'south')
        for k in range(4):
            T.fill(k, 64 + k, 0, k, 64 + k, 6, S('green_wool'))
            T.fill(7 - k, 64 + k, 0, 7 - k, 64 + k, 6, S('green_wool'))
        ch.coffre(T, 3, 64, 3, 'south', SI.LOOT_MILITAIRE)
    ch.voitures(ch.x0 + 20, ch.z1 - 50, ch.x1 - 50, ch.z1 - 20, 5, 'east')
    return ch.terminer(0.5)


def norda(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D)
    m, rng = ch.m, ch.rng
    # stationnement
    m.fill(ch.x0 + 4, 63, 30, ch.x1 - 4, 63, ch.z1 - 4, S('gray_concrete'))
    for x in range(ch.x0 + 6, ch.x1 - 6, 4):
        m.fill(x, 63, 34, x, 63, 40, S('white_concrete'))
    ch.voitures(ch.x0 + 8, 36, ch.x1 - 8, ch.z1 - 8, 10, 'north')
    # bâtiment principal (3 étages) : murs blancs, mur-rideau
    L, P = 70, 34
    R = ch.rep(-L // 2, -P - 4, 'south')
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    for e in range(3):
        y0 = 64 + 5 * e
        R.fill(0, y0, 0, L - 1, y0 + 4, P - 1, S('white_concrete'))
        R.vide(1, y0, 1, L - 2, y0 + 3, P - 2)
        R.fill(1, y0 - 1, 1, L - 2, y0 - 1, P - 2, S('smooth_quartz'))
        for a in range(2, L - 2):
            if a % 5:
                R.fill(a, y0 + 1, P - 1, a, y0 + 3, P - 1, S('light_blue_stained_glass_pane'))
                R.fill(a, y0 + 1, 0, a, y0 + 3, 0, S('light_blue_stained_glass_pane'))
        # laboratoires : paillasses, alambics, chaudrons
        for a in range(4, L - 6, 8):
            R.fill(a, y0, 5, a + 4, y0, 5, S('smooth_quartz'))
            R.set(a + 1, y0 + 1, 5, S('brewing_stand', has_bottle_0=False, has_bottle_1=False, has_bottle_2=False))
            R.set(a + 3, y0, 7, S('cauldron'))
            ch.coffre(R, a + 4, y0, 7, 'north', SI.LOOT_LABO)
        # escalier
        for k in range(5):
            R.set(L - 4, y0 + k, 10 + k, R.S('quartz_stairs', facing='south', half='bottom'))
            R.vide(L - 4, y0 + 4, 10 + k, L - 4, y0 + 4, 10 + k)
    R.fill(0, 79, 0, L - 1, 79, P - 1, S('smooth_stone_slab', type='bottom'))
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'iron')
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 68, z, ['NORDA', 'BIOTECH', 'Recherche', 'et innovation'], mur=R.d('south'), couleur='blue')
    # chambre froide (sous-sol) avec le logo Z-01
    R.fill(20, 55, 8, 40, 58, 20, S('iron_block'))
    R.vide(21, 55, 9, 39, 57, 19)
    R.set(22, 63, 12, S('ladder', facing=R.d('south'), waterlogged=False))
    for y in range(55, 63):
        R.set(22, y, 12, S('ladder', facing=R.d('south'), waterlogged=False))
        R.vide(22, y, 13, 22, y, 13)
    for a in range(24, 38, 3):
        R.set(a, 55, 18, S('blue_ice'))
        ch.coffre(R, a, 55, 10, 'south', SI.LOOT_LABO)
    # clôture
    for x in range(ch.x0 + 1, ch.x1):
        for z in (ch.z0 + 1, ch.z1 - 1):
            m.fill(x, 64, z, x, 66, z, S('iron_bars'))
    for z in range(ch.z0 + 1, ch.z1):
        for x in (ch.x0 + 1, ch.x1 - 1):
            m.fill(x, 64, z, x, 66, z, S('iron_bars'))
    m.vide(-3, 64, ch.z1 - 1, 3, 66, ch.z1 - 1)
    ch.panneau(-5, 65, ch.z1, ['NORDA BIOTECH', 'Propriété privée', 'Risque biologique', 'NE PAS ENTRER'], rotation=0, couleur='red')
    return ch.terminer(0.45)


def barrage(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, H=48, sol='air')
    m = ch.m
    m.vide(ch.x0, 58, ch.z0, ch.x1, 62, ch.z1)         # le terrain naturel (rivière) reste en dessous
    m.fill(ch.x0, 63, ch.z0, ch.x1, 63, ch.z1, AIR)
    # mur du barrage : perpendiculaire à la rivière (qui coule d'ouest en est), de rive à rive
    m.fill(-4, 50, ch.z0 + 5, 4, 72, ch.z1 - 5, S('light_gray_concrete'))
    m.fill(-3, 73, ch.z0 + 5, 3, 73, ch.z1 - 5, S('gray_concrete'))
    for z in range(ch.z0 + 5, ch.z1 - 4):
        m.set(-4, 74, z, S('iron_bars'))
        m.set(4, 74, z, S('iron_bars'))
    # vannes (déversoir)
    for z in range(-12, 13, 6):
        m.fill(5, 58, z, 7, 70, z + 2, S('iron_block'))
    # centrale : bâtiment des turbines en aval (côté est), sur la rive nord
    C = ch.rep(10, ch.z0 + 6, 'south')
    C.fill(0, 59, 0, 29, 63, 17, S('stone'))
    C.fill(0, 64, 0, 29, 73, 17, S('light_gray_concrete'))
    C.vide(1, 64, 1, 28, 72, 16)
    C.fill(1, 63, 1, 28, 63, 16, S('polished_andesite'))
    for a in range(4, 27, 7):
        C.fill(a, 64, 6, a + 3, 67, 9, S('iron_block'))
        C.set(a + 1, 68, 7, S('lightning_rod', facing='up', powered=False, waterlogged=False))
    for a in range(2, 28, 3):
        C.fill(a, 69, 0, a, 71, 0, S('glass_pane'))
    ZM.porte(C, 14, 64, 17, 'north', 'iron')
    x, z = C.xz(14, 18)
    ch.panneau(x, 67, z, ['HYDRO', 'Centrale de la', 'Rivière-Blanche', 'DANGER 25 kV'], mur=C.d('south'), couleur='red')
    ch.coffre(C, 2, 64, 2, 'south', SI.LOOT_VILLE)
    return ch.terminer(0.3)


def industriel(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, sol='gray_concrete')
    m, rng = ch.m, ch.rng
    for i, x in enumerate(range(ch.x0 + 8, ch.x1 - 40, 52)):
        E = ch.rep(x, ch.z0 + 8, 'south')
        E.fill(0, 59, 0, 39, 63, 49, S('stone'))
        E.fill(0, 64, 0, 39, 75, 49, S('iron_block') if i % 2 else S('light_gray_concrete'))
        E.vide(1, 64, 1, 38, 75, 48)
        E.fill(0, 76, 0, 39, 76, 49, S('smooth_stone_slab', type='bottom'))
        for a in range(4, 36, 8):
            E.vide(a, 64, 49, a + 4, 68, 49)
        for k in range(20):
            E.set(rng.randint(2, 37), 64, rng.randint(2, 45), E.S('barrel', facing='up', open=False))
        for k in range(4):
            ch.coffre(E, rng.randint(2, 37), 64, rng.randint(2, 40), 'south', SI.LOOT_VILLE)
    # conteneurs
    for _ in range(18):
        x, z = rng.randint(ch.x0 + 6, ch.x1 - 12), rng.randint(ch.z1 - 50, ch.z1 - 8)
        col = rng.choice(['red', 'blue', 'green', 'orange', 'gray', 'white'])
        m.fill(x, 64, z, x + 6, 66, z + 2, S(col + '_concrete'))
    ch.voitures(ch.x0 + 10, ch.z1 - 30, ch.x1 - 10, ch.z1 - 6, 6, 'east')
    ch.panneau(0, 64, ch.z1 - 1, [site['nom'][:15], site['nom'][15:30], '', ''], rotation=0)
    return ch.terminer(0.4)


def station(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, sol='gray_concrete')
    m = ch.m
    # marquise sur piliers
    for (x, z) in ((-12, -6), (8, -6), (-12, 4), (8, 4)):
        m.fill(x, 64, z, x, 68, z, S('white_concrete'))
    m.fill(-14, 69, -8, 10, 69, 6, S('white_concrete'))
    m.fill(-14, 70, -8, 10, 70, -8, S('red_concrete'))
    for x in (-6, 2):
        for z in (-3, 1):
            m.set(x, 64, z, S('iron_block'))
            m.set(x, 65, z, S('stone_button', face='floor', facing='north', powered=False))
    ch.voitures(-10, -2, 6, 2, 2, 'east')
    R = ch.rep(-14, ch.z0 + 2, 'south')
    commerce(ch, R, 16, 10, 'Dépanneur')
    ch.panneau(12, 64, 8, ['ESSENCE', 'ORDINAIRE', '---- $/L', 'FERMÉ'], rotation=8, couleur='red')
    return ch.terminer(0.5)


def motel(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, sol='gray_concrete')
    R = ch.rep(-W // 2 + 2, -D // 2 + 2, 'south')
    L = W - 4
    R.fill(0, 59, 0, L - 1, 63, 11, S('stone'))
    R.fill(0, 64, 0, L - 1, 68, 11, S('orange_terracotta'))
    R.vide(1, 64, 1, L - 2, 67, 10)
    R.fill(1, 63, 1, L - 2, 63, 10, S('spruce_planks'))
    for i, a in enumerate(range(1, L - 8, 8)):
        R.fill(a + 7, 64, 1, a + 7, 67, 10, S('orange_terracotta'))
        ZM.porte(R, a + 2, 64, 11, 'north', 'spruce', 'left', i % 3 == 0)
        R.set(a + 5, 65, 11, S('glass_pane'))
        ZM.lit(R, a + 4, 64, 3, 'north', 'red')
        ch.coffre(R, a + 1, 64, 1, 'south', SI.LOOT_MAISON)
    R.fill(0, 69, 0, L - 1, 69, 11, S('smooth_stone_slab', type='bottom'))
    ch.voitures(-W // 2 + 6, 6, W // 2 - 6, D // 2 - 4, 4, 'north')
    ch.panneau(W // 2 - 3, 64, D // 2 - 2, ['MOTEL', 'DU VOYAGEUR', 'Chambres', 'libres'], rotation=0, couleur='red')
    return ch.terminer(0.55)


def checkpoint(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, sol='gray_concrete')
    m, rng = ch.m, ch.rng
    for k in range(-12, 13):
        if k % 5:
            m.set(k, 64, -2, S('sandstone_wall'))
    m.fill(-10, 64, 3, 10, 64, 3, S('iron_bars'))
    ch.voitures(-12, 6, 12, 12, 5, 'north')
    T = ch.rep(8, -12, 'south')
    for k in range(4):
        T.fill(k, 64 + k, 0, k, 64 + k, 5, S('green_wool'))
        T.fill(7 - k, 64 + k, 0, 7 - k, 64 + k, 5, S('green_wool'))
    ch.coffre(T, 3, 64, 2, 'south', SI.LOOT_MILITAIRE)
    ch.panneau(-6, 64, 6, ['ARRÊT', 'CONTRÔLE', 'MILITAIRE', 'Escouade Bravo-3'], rotation=0, couleur='red')
    return ch.terminer(0.4)


def emetteur(site, plan):
    ch = Chantier(site, site['larg'], site['prof'], H=90)
    m = ch.m
    for y in range(64, 136):
        e = max(1, 4 - (y - 64) // 18)
        for (dx, dz) in ((-e, -e), (e, -e), (-e, e), (e, e)):
            m.set(dx, y, dz, S('iron_bars'))
        if y % 6 == 0:
            for d in range(-e, e + 1):
                m.set(d, y, -e, S('iron_bars'))
                m.set(d, y, e, S('iron_bars'))
                m.set(-e, y, d, S('iron_bars'))
                m.set(e, y, d, S('iron_bars'))
    m.fill(0, 136, 0, 0, 140, 0, S('lightning_rod', facing='up', powered=False, waterlogged=False))
    for y in (100, 120, 135):
        m.set(0, y, 0, S('redstone_lamp', lit=False))
    R = ch.rep(8, -6, 'south')
    maison(ch, R, 9, 8, mur='light_gray_concrete', toit='deepslate_tile', butin=SI.LOOT_VILLE)
    x, z = R.xz(4, 9)
    ch.panneau(x + 2, 64, z, ['CKZA 98,5', 'Émetteur du', 'mont Gagnon', 'Défense d\'entrer'], rotation=0, couleur='blue')
    return ch.terminer(0.4)


def carriere(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, H=60, sol='stone')
    m, rng = ch.m, ch.rng
    ch.m = m
    # fosse en gradins (creusée sous le niveau du sol : la structure commence à y=58)
    for k in range(6):
        r = W // 2 - 8 - k * 7
        m.vide(-r, 63 - k, -r * D // W, r, 63, r * D // W)
    m.fill(-6, 58, -6, 6, 58, 6, S('gravel'))
    R = ch.rep(ch.x1 - 16, ch.z0 + 2, 'south')
    maison(ch, R, 12, 8, mur='white_concrete', toit='stone_brick', butin=SI.LOOT_VILLE)
    for _ in range(8):
        x, z = rng.randint(ch.x0 + 4, ch.x1 - 4), rng.randint(ch.z0 + 4, ch.z1 - 4)
        m.fill(x, 64, z, x + 1, 64 + rng.randint(0, 2), z + 1, S('cobblestone'))
    return ch.terminer(0.3)


def chalet(site, plan):
    ch = Chantier(site, site['larg'], site['prof'])
    R = ch.rep(-6, -5, 'south')
    maison(ch, R, 11, 9, mur='spruce_log', toit='dark_oak', bois='spruce')
    ch.m.set(-8, 64, 6, S('campfire', facing='north', lit=False, signal_fire=False, waterlogged=False))
    ch.panneau(-9, 64, 7, ['Chalet', site.get('lac', '')[:15], '« Fermé pour', 'l\'hiver »'], rotation=0)
    return ch.terminer(0.5)


def camp_chasse(site, plan):
    ch = Chantier(site, site['larg'], site['prof'])
    R = ch.rep(-4, -4, 'south')
    maison(ch, R, 7, 6, mur='spruce_planks', toit='spruce', bois='spruce')
    ch.m.set(5, 64, 5, S('campfire', facing='north', lit=False, signal_fire=False, waterlogged=False))
    ch.coffre(R, 5, 64, 1, 'south', SI.LOOT_MAISON)
    return ch.terminer(0.6)
