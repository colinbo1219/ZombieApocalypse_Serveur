# -*- coding: utf-8 -*-
"""grands_lieux : les lieux de la bible (Partie 3, points 28 à 31, 36) — aéroport et avion écrasé, centre d'achat,
aréna de hockey, prison, gares, université, port, hôtel. Même cadre que batisse.py (Chantier, sol de marche à y=64,
centrés sur (0, 0)) ; importé à la fin de batisse.py pour que sites.structure_de les trouve par leur type.
Chaque sous-lieu (terminal, tour de contrôle, cinéma, bloc cellulaire...) est déclaré avec ch.lieu() : za_p73 donne
son nom à l'entrée et ses zombies (generer.ZOMBIES).
"""
import batisse as BA
import sites as SI
import za_meubles as ZM
from za_blocs import S

Chantier = BA.Chantier


def _boite(R, L, P, H, mur, sol='smooth_stone', toit='smooth_stone_slab'):
    """Un volume fermé : fondations, murs, sol, plafond plat."""
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 63 + H, P - 1, S(mur))
    R.vide(1, 64, 1, L - 2, 63 + H, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S(sol))
    R.fill(0, 64 + H, 0, L - 1, 64 + H, P - 1, S(toit, type='bottom') if toit.endswith('slab') else S(toit))


def _vitres(R, L, P, y1, y2, pas=3):
    for a in range(2, L - 2, pas):
        for b in (0, P - 1):
            R.fill(a, y1, b, a, y2, b, S('glass_pane'))
    for b in range(2, P - 2, pas):
        for a in (0, L - 1):
            R.fill(a, y1, b, a, y2, b, S('glass_pane'))


def _plancher(R, L, P, y, trou=None):
    R.fill(1, y, 1, L - 2, y, P - 2, S('smooth_stone'))
    if trou:
        a1, b1, a2, b2 = trou
        R.vide(a1, y, b1, a2, y, b2)


def _escalier(R, a, b, y0, n, facing):
    """Un escalier droit de n marches (b croissant)."""
    for k in range(n):
        R.set(a, y0 + k, b + k, R.S('stone_brick_stairs', facing=facing, half='bottom'))
        R.set(a + 1, y0 + k, b + k, R.S('stone_brick_stairs', facing=facing, half='bottom'))
        R.vide(a, y0 + k + 1, b + k, a + 1, y0 + k + 3, b + k)


def _barricade(ch, R, a, b, n=3):
    for k in range(n):
        R.set(a + k, 64, b, S(ch.rng.choice(['oak_planks', 'stripped_oak_log', 'cobblestone', 'oak_planks'])))


# ============================================================================ 28 — aéroport et avion écrasé
def aeroport(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, H=60, sol='grass')
    m, rng = ch.m, ch.rng
    x0, x1 = ch.x0 + 6, ch.x1 - 6
    # piste (est-ouest) : béton, bords blancs, numéros, axe pointillé
    zp1, zp2 = 20, 44
    m.fill(x0, 63, zp1, x1, 63, zp2, S('gray_concrete'))
    for x in range(x0, x1 + 1):
        m.set(x, 63, zp1, S('white_concrete'))
        m.set(x, 63, zp2, S('white_concrete'))
        if x % 10 < 5:
            m.set(x, 63, (zp1 + zp2) // 2, S('white_concrete'))
    for x in range(x0 + 4, x0 + 12):
        for z in range(zp1 + 3, zp2 - 2, 3):
            m.set(x, 63, z, S('white_concrete'))
    # le terminal (où des survivants ont tenu : journaux, barricades, lits de camp)
    T = ch.rep(-60, -D // 2 + 6, 'south')
    _boite(T, 56, 22, 9, 'white_concrete', 'polished_andesite')
    _vitres(T, 56, 22, 65, 71, 2)
    _plancher(T, 56, 22, 68, (20, 6, 35, 15))
    BA.ZM.porte_double(T, 26, 64, 21, 'north', 'oak')
    for b in range(4, 18, 4):
        T.fill(4, 64, b, 16, 64, b, T.S('stone_brick_stairs', facing='north', half='bottom'))     # rangées de sièges
    for a in range(38, 52, 3):
        ZM.lit(T, a, 64, 3, 'north', rng.choice(['white', 'light_gray', 'blue']))                 # le camp qui a tenu
    _barricade(ch, T, 24, 19, 6)
    ch.coffre(T, 52, 64, 2, 'south', SI.LOOT_VILLE)
    ch.coffre(T, 2, 64, 2, 'south', SI.LOOT_MAISON, baril=True)
    ch.coffre(T, 40, 69, 4, 'south', SI.LOOT_MAISON)
    x, z = T.xz(28, 22)
    ch.panneau(x, 72, z, ['AÉROPORT', 'RÉGIONAL', 'DES LAURENTIDES', ''], mur=T.d('south'))
    ch.lieu(T, 56, 22, 'terminal', "Terminal de l'aéroport")
    # tour de contrôle : la radio longue portée (106)
    C = ch.rep(4, -D // 2 + 8, 'south')
    C.fill(0, 59, 0, 6, 63, 6, S('stone'))
    C.fill(0, 64, 0, 6, 84, 6, S('light_gray_concrete'))
    C.vide(1, 64, 1, 5, 84, 5)
    C.fill(1, 64, 1, 1, 84, 1, S('scaffolding', bottom=False, distance=0, waterlogged=False))
    C.fill(-1, 85, -1, 7, 85, 7, S('smooth_stone'))
    C.fill(-1, 86, -1, 7, 89, 7, S('light_blue_stained_glass'))
    C.vide(0, 86, 0, 6, 89, 6)
    C.fill(-1, 90, -1, 7, 90, 7, S('smooth_stone_slab', type='bottom'))
    C.set(3, 86, 3, S('lectern', facing='south', has_book=False, powered=False))
    C.set(4, 86, 3, S('note_block', instrument='bit', note=0, powered=False))
    ch.coffre(C, 1, 86, 5, 'east', SI.LOOT_MILITAIRE)
    C.fill(3, 91, 3, 3, 95, 3, S('lightning_rod', facing='up', powered=False, waterlogged=False))
    ch.lieu(C, 7, 7, 'tour_controle', 'Tour de contrôle (radio longue portée)')
    # hangar : pièces de drones (99)
    H = ch.rep(30, -D // 2 + 4, 'south')
    _boite(H, 34, 24, 12, 'light_gray_concrete', 'gray_concrete', 'smooth_stone')
    H.vide(6, 64, 23, 27, 72, 23)
    for a in range(4, 30, 6):
        ch.coffre(H, a, 64, 2, 'south', SI.LOOT_MILITAIRE)
        H.set(a + 1, 64, 2, S('anvil', facing='north'))
    ch.lieu(H, 34, 24, 'hangar', 'Hangar (pièces de drones)')
    # dépôt de carburant : trois citernes (il peut exploser, 32)
    for k, cx in enumerate((-W // 2 + 14, -W // 2 + 24, -W // 2 + 34)):
        cz = D // 2 - 16
        for y in range(64, 71):
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    if 6 <= dx * dx + dz * dz <= 10:
                        m.set(cx + dx, y, cz + dz, S('iron_block' if (y + k) % 3 else 'white_concrete'))
        m.fill(cx - 2, 71, cz - 2, cx + 2, 71, cz + 2, S('smooth_stone_slab', type='bottom'))
    x, z = -W // 2 + 24, D // 2 - 8
    ch.panneau(x, 64, z, ['DANGER', 'CARBURANT', 'AVIATION', 'Ne pas fumer'], rotation=8, couleur='red')
    ch.lieux.append(('depot_carburant', 'Dépôt de carburant', -W // 2 + 24, D // 2 - 16, 18, 8))
    # l'avion écrasé : une traînée de débris jusqu'au fuselage brisé, à l'est de la piste
    fx = x1 - 30
    for x in range(x0 + 120, fx):
        if rng.random() < 0.18:
            z = rng.randint(zp1 - 10, zp2 + 10)
            m.set(x, 64, z, S(rng.choice(['iron_bars', 'white_concrete', 'gray_concrete', 'coal_block', 'iron_trapdoor'])) if rng.random() < 0.8 else S('fire', age=0, east=False, north=False, south=False, up=False, west=False))
            m.set(x, 63, z, S(rng.choice(['coarse_dirt', 'soul_soil', 'gravel'])))
    for x in range(fx - 6, fx + 22):
        for dy in range(0, 5):
            for dz in range(-2, 3):
                if dy in (0, 4) or abs(dz) == 2:
                    if rng.random() < 0.85:
                        m.set(x, 64 + dy, 32 + dz, S('white_concrete' if dy < 3 else 'light_gray_concrete'))
    m.vide(fx + 6, 64, 30, fx + 9, 69, 34)                                          # brisé en deux
    for k in range(10):
        m.set(fx - 4 + k * 2, 64, 26, S('white_concrete'))                       # une aile arrachée
    ch.coffre(ch.R0, fx + 2, 65, 32, 'north', SI.LOOT_MILITAIRE)
    ch.lieux.append(('avion', 'Avion écrasé', fx + 8, 32, 16, 8))
    ch.lieux.append(('piste', "Piste (zone d'extraction)", (x0 + x1) // 2, (zp1 + zp2) // 2, (x1 - x0) // 2, 12))
    return ch.terminer(0.55)


# ============================================================================ 29 — centre d'achat
def centre_achat(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, H=40, sol='gray_concrete')
    rng = ch.rng
    L, P = W - 16, D - 22
    R = ch.rep(-L // 2, -D // 2 + 4, 'south')
    _boite(R, L, P, 11, 'light_gray_concrete', 'polished_diorite')
    _vitres(R, L, P, 65, 67, 4)
    _plancher(R, L, P, 69, (L // 2 - 8, 10, L // 2 + 8, P - 12))                  # atrium sur deux étages
    BA.ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'oak')
    _escalier(R, L // 2 - 12, 12, 64, 5, 'south')                                 # l'escalier mécanique arrêté
    R.fill(L // 2 - 12, 63, 11, L // 2 - 11, 63, 17, S('black_concrete'))
    # boutiques du rez-de-chaussée (le long des murs)
    noms = ['Pharmacie', 'Épicerie', 'Quincaillerie', 'Sport Expert', 'Librairie', 'Bijouterie', 'Électronique']
    for i, a in enumerate(range(2, L - 14, 13)):
        R.fill(a, 64, 1, a, 68, 9, S('white_concrete'))
        R.fill(a + 1, 64, 9, a + 11, 66, 9, S('glass_pane'))
        R.vide(a + 5, 64, 9, a + 6, 65, 9)
        nom = noms[i % len(noms)]
        butin = SI.LOOT_LABO if nom == 'Pharmacie' else SI.LOOT_VILLE
        for b in range(2, 8, 2):
            ch.coffre(R, a + 3 + (b % 4), 64, b, 'south', butin, baril=True)
        x, z = R.xz(a + 6, 10)
        ch.panneau(x, 67, z, ['', nom.upper()[:15], '', ''], mur=R.d('south'))
        if nom == 'Pharmacie':
            (xa, za), (xb, zb) = R.xz(a, 1), R.xz(a + 11, 9)
            ch.lieux.append(('pharmacie', 'Pharmacie du centre', (xa + xb) // 2, (za + zb) // 2, abs(xb - xa) // 2 + 2, abs(zb - za) // 2 + 2))
    # aire de restauration (au fond de l'atrium)
    for a in range(L // 2 - 7, L // 2 + 8, 4):
        ZM.table(R, a, 64, P - 10, 'birch')
        ZM.chaise(R, a - 1, 64, P - 10, 'east', 'birch')
        ZM.chaise(R, a + 1, 64, P - 10, 'west', 'birch')
    ch.coffre(R, L // 2, 64, P - 5, 'north', SI.LOOT_MAISON, baril=True)
    # cinéma à l'étage : une salle noire pleine de morts endormis (état Dormant, IA-3)
    R.fill(2, 70, 2, 24, 74, P - 3, S('black_concrete'))
    R.vide(3, 70, 3, 23, 74, P - 4)
    R.fill(3, 69, 3, 23, 69, P - 4, S('red_carpet'))
    for b in range(6, P - 6, 2):
        R.fill(5, 70, b, 21, 70, b, R.S('red_nether_brick_stairs', facing='north', half='bottom'))
    R.fill(3, 71, 3, 23, 74, 3, S('white_concrete'))                                # l'écran
    R.vide(24, 70, P // 2, 24, 71, P // 2)
    ch.lieu(R, 26, P, 'cinema', "Cinéma du centre (il y a du monde dans le noir)")
    # poste de sécurité (caméras) et le camp perdu, à l'étage
    R.fill(L - 16, 70, 2, L - 2, 70, 10, S('smooth_stone'))
    R.fill(L - 16, 70, 10, L - 2, 72, 10, S('iron_bars'))
    for a in range(L - 15, L - 3, 2):
        R.set(a, 70, 3, S('black_concrete'))
        R.set(a, 71, 3, S('light_blue_stained_glass_pane'))
    ch.coffre(R, L - 3, 70, 3, 'south', SI.LOOT_MILITAIRE)
    for a in range(L - 30, L - 18, 3):
        ZM.lit(R, a, 70, P - 8, 'north', rng.choice(['brown', 'gray', 'green']))
    _barricade(ch, R, L - 30, P - 12, 10)
    ch.coffre(R, L - 20, 70, P - 6, 'north', SI.LOOT_MAISON)
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 73, z, ['CARREFOUR', 'LAURENTIDES', 'Centre', "d'achat"], mur=R.d('south'))
    ch.lieu(R, L, P, 'centre_achat', "Carrefour Laurentides (centre d'achat)")
    # stationnement : voitures abandonnées
    ch.voitures(ch.x0 + 4, D // 2 - 12, ch.x1 - 4, D // 2 - 3, 10, 'north')
    return ch.terminer(0.5)


# ============================================================================ 30 — aréna de hockey
def arena(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, H=40, sol='gray_concrete')
    m, rng = ch.m, ch.rng
    a, b = W // 2 - 4, D // 2 - 4
    # enceinte ovale, toit voûté
    for x in range(-a, a + 1):
        for z in range(-b, b + 1):
            e = (x / a) ** 2 + (z / b) ** 2
            if e <= 1:
                m.set(x, 63, z, S('polished_andesite'))
                if e > 0.86:
                    m.fill(x, 64, z, x, 76, z, S('light_gray_concrete' if (x + z) % 7 else 'blue_concrete'))
                    if 0.86 < e < 0.93:
                        m.fill(x, 66, z, x, 67, z, S('glass_pane'))
                h = 77 + int(5 * (1 - e))
                m.set(x, h, z, S('smooth_stone_slab', type='bottom'))
    # la patinoire : glace, avec des silhouettes figées dessous (27)
    pa, pb = a - 14, b - 12
    m.fill(-pa, 62, -pb, pa, 62, pb, S('packed_ice'))
    m.fill(-pa, 63, -pb, pa, 63, pb, S('ice'))
    for _ in range(8):
        x, z = rng.randint(-pa + 2, pa - 2), rng.randint(-pb + 2, pb - 2)
        m.set(x, 62, z, S('soul_soil'))
    m.fill(-pa - 1, 64, -pb - 1, pa + 1, 64, -pb - 1, S('white_concrete'))          # bandes
    m.fill(-pa - 1, 64, pb + 1, pa + 1, 64, pb + 1, S('white_concrete'))
    m.fill(-pa - 1, 64, -pb - 1, -pa - 1, 64, pb + 1, S('white_concrete'))
    m.fill(pa + 1, 64, -pb - 1, pa + 1, 64, pb + 1, S('white_concrete'))
    m.fill(-pa - 1, 65, -pb - 1, pa + 1, 65, -pb - 1, S('glass_pane'))
    m.fill(-pa - 1, 65, pb + 1, pa + 1, 65, pb + 1, S('glass_pane'))
    for x in (-pa + 1, pa - 1):
        m.fill(x, 64, -2, x, 65, 2, S('red_concrete'))                              # les buts
    # gradins (marché ou lieu de rassemblement, p44)
    for k in range(5):
        m.fill(-pa + 2, 65 + k, -pb - 3 - k, pa - 2, 65 + k, -pb - 3 - k, S('blue_concrete' if k % 2 else 'white_concrete'))
        m.fill(-pa + 2, 65 + k, pb + 3 + k, pa - 2, 65 + k, pb + 3 + k, S('blue_concrete' if k % 2 else 'white_concrete'))
    m.vide(-2, 64, b - 1, 2, 67, b + 1)                                               # entrée sud
    ch.coffre(ch.R0, a - 10, 64, 0, 'west', SI.LOOT_VILLE, baril=True)
    ch.coffre(ch.R0, -a + 10, 64, 0, 'east', SI.LOOT_MAISON)
    ch.panneau(0, 64, b + 3, ['ARÉNA', 'GILLES-TREMBLAY', 'Hockey mineur', 'ce samedi'], rotation=0, couleur='blue')
    ch.lieux.append(('arena', 'Aréna Gilles-Tremblay', 0, 0, a, b))
    ch.lieux.append(('patinoire', 'La patinoire (il y a des formes sous la glace)', 0, 0, pa, pb))
    return ch.terminer(0.4)


# ============================================================================ 31 — prison
def prison(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, H=40, sol='gravel')
    m, rng = ch.m, ch.rng
    x0, z0, x1, z1 = ch.x0 + 3, ch.z0 + 3, ch.x1 - 3, ch.z1 - 3
    # mur d'enceinte, barbelés (barreaux), miradors
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            m.fill(x, 64, z, x, 70, z, S('stone_bricks'))
            m.set(x, 71, z, S('iron_bars'))
    for z in range(z0, z1 + 1):
        for x in (x0, x1):
            m.fill(x, 64, z, x, 70, z, S('stone_bricks'))
            m.set(x, 71, z, S('iron_bars'))
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        m.fill(x - 2, 64, z - 2, x + 2, 76, z + 2, S('stone_bricks'))
        m.vide(x - 1, 72, z - 1, x + 1, 75, z + 1)
        m.fill(x - 2, 77, z - 2, x + 2, 77, z + 2, S('stone_brick_slab', type='bottom', waterlogged=False))
    m.vide(-3, 64, z1, 3, 69, z1)                                                     # portail (forcé)
    m.fill(-3, 64, z1 + 1, 3, 64, z1 + 1, S('iron_bars'))
    m.vide(-1, 64, z1 + 1, 1, 64, z1 + 1)
    # deux blocs cellulaires
    for k, bx in enumerate((x0 + 10, 12)):
        B = ch.rep(bx, z0 + 12, 'south')
        L, P = 40, 24
        _boite(B, L, P, 9, 'light_gray_concrete', 'gray_concrete')
        _plancher(B, L, P, 68, (1, 10, L - 2, 13))                                     # coursive
        for etage in (64, 69):
            for a in range(1, L - 1, 4):
                for (bb, face) in ((1, 'south'), (P - 7, 'north')):
                    B.fill(a, etage, bb, a, etage + 3, bb + 5, S('light_gray_concrete'))
                    B.fill(a + 1, etage, bb + (5 if face == 'south' else 0), a + 3, etage + 2, bb + (5 if face == 'south' else 0), S('iron_bars'))
                    ZM.lit(B, a + 2, etage, bb + (1 if face == 'south' else 4), 'north' if face == 'south' else 'south', 'orange')
        BA.ZM.porte(B, L // 2, 64, P - 1, 'north', 'iron' if not BA.MODERNE else 'oak')
        ch.lieu(B, L, P, 'cellules', 'Bloc cellulaire %s' % ('A' if k == 0 else 'B'))
    # armurerie et salle de contrôle (le levier qui ouvre toutes les cellules : un événement d'évasion)
    A = ch.rep(-10, z1 - 24, 'south')
    _boite(A, 20, 14, 6, 'stone_bricks', 'polished_andesite')
    for a in range(2, 18, 3):
        ch.coffre(A, a, 64, 2, 'south', SI.LOOT_MILITAIRE)
    A.set(10, 64, 8, S('lever', face='floor', facing='north', powered=False))
    A.fill(6, 64, 6, 14, 64, 6, S('polished_blackstone'))
    BA.ZM.porte(A, 10, 64, 13, 'north', 'iron' if not BA.MODERNE else 'oak')
    ch.lieu(A, 20, 14, 'controle_prison', 'Salle de contrôle et armurerie')
    # la cour : traces de l'émeute (graffitis, feu, barricades)
    for _ in range(14):
        x, z = rng.randint(x0 + 6, x1 - 6), rng.randint(0, z1 - 30)
        m.set(x, 64, z, S(rng.choice(['oak_planks', 'barrel', 'iron_bars', 'campfire'])) if rng.random() < 0.85 else S('coal_block'))
    ch.panneau(0, 64, z1 - 4, ['PILLARDS', 'ICI C\'EST', 'NOUS', 'LA LOI'], rotation=8, couleur='red')
    ch.panneau(-6, 64, z1 + 3, ['ÉTABLISSEMENT', 'DE DÉTENTION', 'SAINT-AURÈLE', 'Accès interdit'], rotation=0)
    ch.lieux.append(('prison', 'Établissement de détention', 0, 0, W // 2, D // 2))
    return ch.terminer(0.45)


# ============================================================================ 36 — gare
def gare(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, sol='gray_concrete')
    m = ch.m
    # quai le long de la voie (la voie passe en z = 0, posée par rails.py)
    m.fill(ch.x0 + 2, 64, 3, ch.x1 - 2, 64, 6, S('smooth_stone_slab', type='bottom'))
    for x in range(ch.x0 + 4, ch.x1 - 2, 8):
        m.fill(x, 65, 6, x, 68, 6, S('dark_oak_fence', east=False, north=False, south=False, west=False, waterlogged=False))
        m.fill(x - 3, 69, 3, x + 3, 69, 7, S('dark_oak_slab', type='bottom', waterlogged=False))
    R = ch.rep(-10, 8, 'north')
    BA.maison(ch, R, 20, 10, 1, mur='bricks', toit='dark_oak')
    ch.panneau(0, 65, 6, ['GARE', site['nom'][-15:], 'Prochain train :', '— annulé —'], rotation=8)
    ch.lieux.append(('gare', site['nom'], 0, 4, W // 2, 8))
    return ch.terminer(0.45)


# ============================================================================ université (labo civil, 19)
def universite(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, H=44)
    rng = ch.rng
    for k, (ox, oz, L, P, nom) in enumerate(((-70, -50, 46, 22, 'Pavillon des sciences'), (-10, -50, 40, 22, 'Bibliothèque'),
                                              (-70, 0, 40, 20, 'Résidences'))):
        R = ch.rep(ox, oz, 'south')
        _boite(R, L, P, 9, rng.choice(['bricks', 'light_gray_concrete', 'white_terracotta']))
        _vitres(R, L, P, 65, 66, 3)
        _plancher(R, L, P, 68)
        BA.ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'oak')
        if k == 0:
            for a in range(3, L - 3, 4):
                R.set(a, 64, 3, S('brewing_stand', has_bottle_0=False, has_bottle_1=False, has_bottle_2=False))
                R.set(a + 1, 64, 3, S('smooth_quartz'))
            for a in range(2, L - 2, 6):
                ch.coffre(R, a, 64, P - 3, 'north', SI.LOOT_LABO)
            ch.lieu(R, L, P, 'labo_civil', 'Laboratoire de biologie (université)')
        elif k == 1:
            for b in range(3, P - 3, 3):
                R.fill(3, 64, b, L - 4, 66, b, S('bookshelf'))
            ch.coffre(R, L - 3, 64, 2, 'south', SI.LOOT_MAISON)
            ch.lieu(R, L, P, 'bibliotheque', 'Bibliothèque universitaire')
        else:
            for a in range(2, L - 2, 4):
                ZM.lit(R, a, 64, 3, 'north', rng.choice(['white', 'blue', 'gray']))
                ZM.lit(R, a, 69, 3, 'north', rng.choice(['white', 'blue', 'gray']))
            ch.coffre(R, L - 3, 64, P - 3, 'north', SI.LOOT_MAISON)
            ch.lieu(R, L, P, 'residences', 'Résidences étudiantes')
    ch.panneau(30, 64, 30, ['UNIVERSITÉ', 'DU QUÉBEC', 'campus des', 'Laurentides'], rotation=0)
    ch.lieux.append(('universite', site['nom'], 0, 0, W // 2, D // 2))
    return ch.terminer(0.5)


# ============================================================================ port fluvial
def port(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, sol='gravel')
    m = ch.m
    # quai en planches sur le côté de la rivière (sud), bittes d'amarrage, entrepôt
    m.fill(ch.x0 + 2, 63, D // 2 - 8, ch.x1 - 2, 63, ch.z1, S('spruce_planks'))
    for x in range(ch.x0 + 4, ch.x1 - 2, 6):
        m.set(x, 64, ch.z1 - 1, S('spruce_fence', east=False, north=False, south=False, west=False, waterlogged=False))
    R = ch.rep(-W // 2 + 4, -D // 2 + 3, 'south')
    _boite(R, 26, 14, 7, 'spruce_planks', 'spruce_planks')
    R.vide(8, 64, 13, 17, 68, 13)
    for a in range(2, 24, 4):
        ch.coffre(R, a, 64, 2, 'south', SI.LOOT_VILLE, baril=True)
    ch.panneau(W // 2 - 6, 64, -D // 2 + 6, ['PORT', 'DE SAINT-AURÈLE', 'Marina', 'municipale'], rotation=8)
    ch.lieux.append(('port', site['nom'], 0, 0, W // 2, D // 2))
    return ch.terminer(0.5)


# ============================================================================ hôtel
def hotel(site, plan):
    W, D = site['larg'], site['prof']
    ch = Chantier(site, W, D, H=50)
    rng = ch.rng
    L, P = W - 10, D - 12
    R = ch.rep(-L // 2, -D // 2 + 4, 'south')
    _boite(R, L, P, 20, 'stone_bricks', 'polished_andesite')
    for e in range(5):
        y = 64 + 4 * e
        if e:
            _plancher(R, L, P, y - 1, (2, 2, 3, 6))
        _vitres(R, L, P, y + 1, y + 2, 3)
        for a in range(2, L - 4, 5):
            ZM.lit(R, a + 1, y, P - 3, 'south', rng.choice(['white', 'red', 'light_gray']))
            if rng.random() < 0.5:
                ch.coffre(R, a + 3, y, P - 2, 'north', SI.LOOT_MAISON)
    R.fill(2, 64, 2, 2, 83, 2, S('scaffolding', bottom=False, distance=0, waterlogged=False))
    BA.ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'dark_oak')
    R.fill(L // 2 - 4, 64, P - 6, L // 2 + 4, 64, P - 6, S('smooth_quartz'))          # comptoir de la réception
    ch.coffre(R, L // 2, 64, P - 7, 'north', SI.LOOT_VILLE)
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 70, z, ['HÔTEL', 'DES LAURENTIDES', '★★★', 'Complet'], mur=R.d('south'))
    ch.lieu(R, L, P, 'hotel', site['nom'])
    return ch.terminer(0.55)
