# -*- coding: utf-8 -*-
"""souterrains : trois complexes creusés dans la roche, posés par le générateur.

  * NORDA — niveau -2 : couloir blanc, laboratoires, cellules de confinement, salle des générateurs, archives ;
    accès par un kiosque technique à l'est du campus (puits à échelle).
  * Bunker de commandement de la base Bravo : salle de commandement, dortoir, armurerie, infirmerie ;
    accès par un kiosque à l'est de la base.
  * Tunnels de service de Saint-Aurèle : égouts (canal d'eau) sous les ruines, station de pompage au centre,
    6 bouches d'égout (trappes en fer) dans les rues.
Chaque complexe est une Structure remplie de « structure_void » : seuls les blocs réellement construits remplacent
la roche (sites._estamper ignore le vide et ne dégage pas au-dessus). Les salles restent dans le noir.
"""
import math
import random

import numpy as np

import sites as SI
import terrain as T
from za_blocs import S, AIR, Monde

VIDE = 'minecraft:structure_void'


class Chantier:
    def __init__(self, nom, x0, y0, z0, x1, y1, z1, graine):
        self.nom = nom
        self.m = Monde(x0, y0, z0, x1 - x0 + 1, y1 - y0 + 1, z1 - z0 + 1)
        self.m.a[:] = self.m.id(VIDE)
        self.rng = random.Random(graine)
        self.coffres = []
        self.boites = []          # (x0,y0,z0,x1,y1,z1, sol, mur, plafond) : coques puis intérieurs
        self.apparitions = []     # points d'apparition des morts (x, y, z)

    def salle(self, x0, y0, z0, x1, y1, z1, mur, sol=None, plafond=None, spawn=True):
        """Intérieur (x0..x1, y0..y1, z0..z1) : sol à y0-1, plafond à y1+1, murs autour."""
        x0, x1 = sorted((x0, x1)); z0, z1 = sorted((z0, z1))
        self.boites.append((x0, y0, z0, x1, y1, z1, sol or mur, mur, plafond or mur))
        if spawn:
            self.apparitions.append(((x0 + x1) // 2, y0, (z0 + z1) // 2))

    def construire(self):
        m = self.m
        for (x0, y0, z0, x1, y1, z1, sol, mur, pl) in self.boites:
            m.fill(x0 - 1, y0 - 1, z0 - 1, x1 + 1, y1 + 1, z1 + 1, S(mur))
            m.fill(x0, y0 - 1, z0, x1, y0 - 1, z1, S(sol))
            m.fill(x0, y1 + 1, z0, x1, y1 + 1, z1, S(pl))
        for (x0, y0, z0, x1, y1, z1, *_r) in self.boites:
            m.fill(x0, y0, z0, x1, y1, z1, AIR)

    def puits(self, x, z, y_bas, y_haut, mur='stone_bricks'):
        """Puits à échelle de y_bas à y_haut (colonne x,z), échelle accrochée au mur est."""
        m = self.m
        m.fill(x - 1, y_bas, z - 1, x + 1, y_haut, z + 1, S(mur))
        for y in range(y_bas, y_haut + 1):
            m.set(x, y, z, S('ladder', facing='west', waterlogged=False))

    def coffre(self, x, y, z, butin, baril=False):
        if baril:
            self.m.set(x, y, z, S('barrel', facing='up', open=False))
        else:
            self.m.set(x, y, z, S('chest', facing='north', type='single', waterlogged=False))
        self.coffres.append((x, y, z, butin))

    def degats(self, force=0.5):
        """Toiles, sang séché, gravats sur les sols intérieurs."""
        m, r = self.m, self.rng
        air = m.a == 0
        dessous = np.zeros_like(air)
        dessous[1:] = (m.a[:-1] != 0) & (m.a[:-1] != m.id(VIDE))
        H, D, W = m.a.shape
        for (y, z, x) in zip(*np.nonzero(air & dessous)):
            v = r.random()
            if v < 0.03 * force:
                m.a[y, z, x] = m.id(S('cobweb'))
            elif v < 0.06 * force:
                m.a[y, z, x] = m.id(S('red_carpet'))       # sang séché
            elif v < 0.08 * force:
                m.a[y, z, x] = m.id(S('gravel'))
        # toiles aux plafonds
        plaf = np.zeros_like(air)
        plaf[:-1] = (m.a[1:] != 0) & (m.a[1:] != m.id(VIDE))
        for (y, z, x) in zip(*np.nonzero(air & plaf)):
            if r.random() < 0.05 * force:
                m.a[y, z, x] = m.id(S('cobweb'))

    def structure(self):
        st = SI.Structure.depuis_monde(self.nom, self.m, self.coffres)
        st.garder = True        # ne rien dégager au-dessus
        return st


def _sol(plan, x, z):
    c = T.champ(plan, np.array([[float(x)]]), np.array([[float(z)]]))
    return int(c['h'][0, 0])


def _kiosque(ch, x, z, ys, nom, lignes, mur='light_gray_concrete'):
    """Petit bâtiment d'accès 5x5 en surface, porte au sud, trappe du puits au centre."""
    m = ch.m
    m.fill(x - 2, ys, z - 2, x + 2, ys, z + 2, S('smooth_stone'))
    m.fill(x - 2, ys + 1, z - 2, x + 2, ys + 4, z + 2, S(mur))
    m.fill(x - 1, ys + 1, z - 1, x + 1, ys + 3, z + 1, AIR)
    m.fill(x - 2, ys + 5, z - 2, x + 2, ys + 5, z + 2, S('smooth_stone_slab', type='bottom'))
    m.set(x, ys + 1, z + 2, S('iron_door', facing='north', half='lower', hinge='left', open=True, powered=False))
    m.set(x, ys + 2, z + 2, S('iron_door', facing='north', half='upper', hinge='left', open=True, powered=False))
    m.set(x, ys, z, S('iron_trapdoor', facing='north', half='top', open=False, powered=False, waterlogged=False))
    m.fill(x - 3, ys + 1, z + 4, x - 3, ys + 1, z + 4, S('spruce_fence'))
    m.set(x - 3, ys + 2, z + 4, S('spruce_wall_sign', facing='south', waterlogged=False))
    m.sign(x - 3, ys + 2, z + 4, lignes)


# ============================================================================ NORDA — niveau -2
def norda(plan):
    s = next(t for t in plan['sites'] if t['id'] == 'norda')
    ys = T.y_site(s)
    Y = ys - 18                       # sol du niveau -2 (intérieur y .. y+3)
    cx, cz = s['x'], s['z']
    kx = cx + s['larg'] // 2 + 14     # kiosque d'accès à l'est du campus
    ks = _sol(plan, kx, cz)
    ch = Chantier('norda_sous_sol', cx - 50, Y - 4, cz - 30, kx + 4, max(ks, ys) + 8, cz + 30, 4201)
    blanc, gris = 'white_concrete', 'light_gray_concrete'
    # couloir principal est-ouest
    ch.salle(cx - 40, Y, cz - 1, kx, Y + 3, cz + 1, blanc, gris, spawn=False)
    ch.apparitions += [(cx - 30, Y, cz), (cx, Y, cz), (cx + 30, Y, cz)]
    # laboratoires de part et d'autre
    for i, x in enumerate(range(cx - 36, cx + 30, 14)):
        ch.salle(x, Y, cz - 12, x + 10, Y + 3, cz - 3, blanc, gris)
        ch.salle(x + 5, Y, cz - 2, x + 5, Y + 1, cz - 2, blanc, gris, spawn=False)          # porte nord
        ch.salle(x, Y, cz + 3, x + 10, Y + 3, cz + 12, blanc, gris)
        ch.salle(x + 5, Y, cz + 2, x + 5, Y + 1, cz + 2, blanc, gris, spawn=False)          # porte sud
    # cellules de confinement (extrémité ouest)
    ch.salle(cx - 50 + 2, Y, cz - 8, cx - 42, Y + 3, cz + 8, 'polished_deepslate', 'polished_deepslate')
    # puits d'accès
    ch.construire()
    m = ch.m
    ch.puits(kx, cz, Y, ks, 'white_concrete')
    m.fill(kx, Y, cz - 1, kx, Y + 1, cz + 1, AIR)
    m.set(kx, Y, cz, S('ladder', facing='west', waterlogged=False))
    m.set(kx, Y + 1, cz, S('ladder', facing='west', waterlogged=False))
    _kiosque(ch, kx, cz, ks, 'norda', ['NORDA Biotech', 'ACCÈS TECHNIQUE', 'Niveau -2', 'Personnel autorisé'])
    # équipement des labos
    r = ch.rng
    for i, x in enumerate(range(cx - 36, cx + 30, 14)):
        for zz, face in ((cz - 12, 'south'), (cz + 12, 'north')):
            m.fill(x, Y, zz, x + 10, Y, zz, S('smooth_quartz'))
            m.set(x + 2, Y + 1, zz, S('brewing_stand', has_bottle_0=r.random() < 0.5, has_bottle_1=False, has_bottle_2=r.random() < 0.3))
            m.set(x + 8, Y + 1, zz, S('glass'))
            ch.coffre(x + 5, Y, zz + (1 if face == 'south' else -1), SI.LOOT_LABO, baril=True)
        m.set(x + 1, Y + 3, cz - 8, S('redstone_lamp', lit=False))
        m.set(x + 1, Y + 3, cz + 8, S('redstone_lamp', lit=False))
    # cellules : barreaux, une porte arrachée
    for z in range(cz - 8, cz + 9, 4):
        m.fill(cx - 44, Y, z, cx - 42, Y + 3, z, S('iron_bars'))
    m.fill(cx - 42, Y, cz - 7, cx - 42, Y + 3, cz + 7, S('iron_bars'))
    m.fill(cx - 42, Y, cz - 1, cx - 42, Y + 1, cz + 1, AIR)
    ch.coffre(cx - 47, Y, cz, SI.LOOT_LABO)
    # panneaux du couloir
    for (x, lignes) in ((cx - 38, ['CONFINEMENT', 'Sujets Z', 'NE PAS OUVRIR', '']),
                        (cx - 5, ['PROJET ARÈS', 'Laboratoires', 'B1 à B5', '']),
                        (kx - 3, ['Niveau -2', '→ Sortie', 'Puits technique', ''])):
        m.set(x, Y + 2, cz - 1, S('oak_wall_sign', facing='south', waterlogged=False))
        m.sign(x, Y + 2, cz - 1, lignes, 'red' if 'CONF' in lignes[0] else 'black')
    ch.degats(0.8)
    return ch, 'sous_norda', 'NORDA — niveau -2', (cx - 5, Y, cz), (50, 16)


# ============================================================================ Bunker de commandement Bravo
def bunker(plan):
    s = next(t for t in plan['sites'] if t['id'] == 'base_bravo')
    ys = T.y_site(s)
    Y = ys - 14
    cx, cz = s['x'], s['z']
    kx = cx + s['larg'] // 2 + 14
    ks = _sol(plan, kx, cz)
    ch = Chantier('bunker_bravo', cx - 30, Y - 4, cz - 20, kx + 4, max(ks, ys) + 8, cz + 20, 4202)
    mur, sol = 'stone_bricks', 'polished_andesite'
    ch.salle(cx - 10, Y, cz - 1, kx, Y + 2, cz + 1, mur, sol, spawn=False)                     # couloir
    ch.salle(cx - 28, Y, cz - 8, cx - 12, Y + 4, cz + 8, mur, sol)                             # commandement
    ch.salle(cx - 11, Y, cz - 1, cx - 11, Y + 1, cz + 1, mur, sol, spawn=False)
    ch.salle(cx + 2, Y, cz - 14, cx + 16, Y + 2, cz - 3, mur, sol)                              # dortoir
    ch.salle(cx + 8, Y, cz - 2, cx + 8, Y + 1, cz - 2, mur, sol, spawn=False)
    ch.salle(cx + 2, Y, cz + 3, cx + 10, Y + 2, cz + 12, mur, sol)                              # armurerie
    ch.salle(cx + 6, Y, cz + 2, cx + 6, Y + 1, cz + 2, mur, sol, spawn=False)
    ch.salle(cx + 14, Y, cz + 3, cx + 22, Y + 2, cz + 10, mur, 'white_concrete')                # infirmerie
    ch.salle(cx + 18, Y, cz + 2, cx + 18, Y + 1, cz + 2, mur, sol, spawn=False)
    ch.construire()
    m = ch.m
    ch.puits(kx, cz, Y, ks, mur)
    m.fill(kx, Y, cz - 1, kx, Y + 1, cz + 1, AIR)
    m.set(kx, Y, cz, S('ladder', facing='west', waterlogged=False))
    m.set(kx, Y + 1, cz, S('ladder', facing='west', waterlogged=False))
    _kiosque(ch, kx, cz, ks, 'bravo', ['FORCES ARMÉES', 'Bunker Bravo', 'Accès restreint', ''], 'green_terracotta')
    # commandement : table des cartes, radios
    m.fill(cx - 22, Y, cz - 2, cx - 18, Y, cz + 2, S('green_terracotta'))
    m.set(cx - 20, Y + 1, cz, S('lectern', facing='east', has_book=False, powered=False))
    for z in range(cz - 6, cz + 7, 3):
        m.set(cx - 27, Y, z, S('note_block', instrument='harp', note=0, powered=False))
    m.set(cx - 12, Y + 2, cz + 7, S('oak_wall_sign', facing='west', waterlogged=False))
    m.sign(cx - 12, Y + 2, cz + 7, ['JOUR 8, 04 h 10', 'Ordre reçu :', 'ne plus ouvrir.', '— Cpl Dumas'], 'red')
    # dortoir : lits ; armurerie : caisses ; infirmerie : lits blancs
    for x in range(cx + 3, cx + 16, 3):
        m.set(x, Y, cz - 13, S('green_bed', facing='south', part='head', occupied=False))
        m.set(x, Y, cz - 12, S('green_bed', facing='south', part='foot', occupied=False))
    for x in range(cx + 3, cx + 10, 2):
        ch.coffre(x, Y, cz + 11, SI.LOOT_MILITAIRE, baril=True)
    ch.coffre(cx + 9, Y, cz + 4, SI.LOOT_MILITAIRE)
    for x in range(cx + 15, cx + 22, 3):
        m.set(x, Y, cz + 9, S('white_bed', facing='south', part='head', occupied=False))
        m.set(x, Y, cz + 10, S('white_bed', facing='south', part='foot', occupied=False))
    ch.coffre(cx + 21, Y, cz + 4, SI.LOOT_LABO, baril=True)
    ch.degats(0.6)
    return ch, 'sous_bunker', 'Bunker de commandement Bravo', (cx, Y, cz), (32, 16)


# ============================================================================ tunnels de Saint-Aurèle
def tunnels(plan):
    s = next(t for t in plan['sites'] if t['type'] == 'ruines')
    ru = SI.structure_de(s, plan)
    bx, by, bz = SI.base_de(s, ru)
    rue = 63                                       # surface des rues (coordonnées de la structure)
    yl = rue - ru.oy
    H, D, W = ru.a.shape
    gris = np.array([p.startswith('minecraft:gray_concrete') for p in ru.pal])
    ouvert = np.array([p == 'minecraft:air' for p in ru.pal])
    ok = gris[ru.a[yl]] & ouvert[ru.a[yl + 1]] & ouvert[ru.a[yl + 2]] & ouvert[ru.a[yl + 3]]
    # centre (station de pompage) et 6 bouches réparties sur un anneau
    wc = (bx + ru.ox + W // 2, bz + ru.oz + D // 2)
    Y = by + rue - 23                              # sol des tunnels, ~22 blocs sous la rue
    ysurf = by + rue
    bouches = []
    zz, xx = np.nonzero(ok)
    wx, wz = xx + bx + ru.ox, zz + bz + ru.oz
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        tx, tz = wc[0] + math.cos(a) * 80, wc[1] + math.sin(a) * 80
        i = int(np.argmin((wx - tx) ** 2 + (wz - tz) ** 2))
        bouches.append((int(wx[i]), int(wz[i])))
    ch = Chantier('tunnels_sa', wc[0] - 140, Y - 4, wc[1] - 140, wc[0] + 140, ysurf + 1, wc[1] + 140, 4203)
    mur, sol = 'stone_bricks', 'cracked_stone_bricks'
    # station de pompage
    ch.salle(wc[0] - 8, Y, wc[1] - 6, wc[0] + 8, Y + 5, wc[1] + 6, mur, 'polished_andesite')
    for (mx, mz) in bouches:
        # tunnel en L : d'abord le long de x depuis la station, puis de z jusqu'à la bouche
        ch.salle(min(wc[0], mx), Y, wc[1] - 1, max(wc[0], mx), Y + 3, wc[1] + 1, mur, sol, spawn=False)
        ch.salle(mx - 1, Y, min(wc[1], mz), mx + 1, Y + 3, max(wc[1], mz), mur, sol, spawn=False)
        ch.apparitions.append(((wc[0] + mx) // 2, Y, wc[1]))
        ch.apparitions.append((mx, Y, (wc[1] + mz) // 2))
    ch.construire()
    m = ch.m
    # canal d'eau au milieu des tunnels (sources : l'eau ne s'écoule pas)
    for (mx, mz) in bouches:
        for x in range(min(wc[0], mx) + 1, max(wc[0], mx)):
            if abs(x - mx) > 2:
                m.set(x, Y - 1, wc[1], S('water', level=0))
        for z in range(min(wc[1], mz) + 1, max(wc[1], mz)):
            if abs(z - mz) > 2 and abs(z - wc[1]) > 2:
                m.set(mx, Y - 1, z, S('water', level=0))
        # puits jusqu'à la rue + trappe en fer dans la chaussée
        ch.puits(mx, mz, Y, ysurf - 1, mur)
        m.set(mx, ysurf, mz, S('iron_trapdoor', facing='north', half='top', open=False, powered=False, waterlogged=False))
    # station : pompes, tableau électrique, coffre de l'employé
    for x in range(wc[0] - 6, wc[0] + 7, 4):
        m.fill(x, Y, wc[1] - 5, x, Y + 2, wc[1] - 5, S('iron_block'))
        m.set(x, Y + 3, wc[1] - 5, S('lightning_rod', facing='up', powered=False, waterlogged=False))
    ch.coffre(wc[0] + 7, Y, wc[1] + 5, SI.LOOT_VILLE)
    m.set(wc[0], Y + 2, wc[1] + 6 - 0, S('oak_wall_sign', facing='north', waterlogged=False))
    m.sign(wc[0], Y + 2, wc[1] + 6, ['Ville de', 'Saint-Aurèle', 'Station de', 'pompage n° 2'])
    ch.degats(0.7)
    return ch, 'sous_egouts', 'Tunnels de service de Saint-Aurèle', (wc[0], Y, wc[1]), (140, 140)


CONSTRUCTEURS = (norda, bunker, tunnels)
_CACHE = {}


def tous(plan):
    """-> liste de (Structure, type, nom, (x,y,z) centre, (demi-l, demi-p), apparitions)."""
    if 'tous' not in _CACHE:
        out = []
        for f in CONSTRUCTEURS:
            ch, genre, nom, centre, demi, = f(plan)
            out.append((ch.structure(), genre, nom, centre, demi, list(ch.apparitions)))
        _CACHE['tous'] = out
    return _CACHE['tous']


def poser(reg):
    for (st, *_r) in tous(reg.plan):
        SI._estamper(reg, st, 0, 0, 0)
