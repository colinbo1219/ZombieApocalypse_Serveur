# -*- coding: utf-8 -*-
"""ville_bat : la bibliothèque de bâtiments urbains des villes générées (ville.py).

Chaque fonction pose un bâtiment dans un repère R (façade en b = P-1, tournée vers la rue) ou occupe un îlot B entier
(x1, z1, x2, z2 : la surface constructible, trottoirs exclus). Sol de marche à y=64 (local), comme les autres sites.
"""
import numpy as np

import sites as SI
import batisse as BA
from batisse import S, AIR, ZM, RU, COULEURS_AUTO
from za_meubles import Repere

ASPH = S('gray_concrete')


def _nv(ch):
    """Nom de la ville en construction."""
    return getattr(ch, 'nom_ville', 'Laurentia')
TROTTOIR = S('smooth_stone')


def lot(ch, B, cote, s, L, P):
    """Repère d'un bâtiment L x P posé dans le pâté B=(x1,z1,x2,z2), façade sur la rue du côté `cote`,
    à l'abscisse s le long de ce côté."""
    x1, z1, x2, z2 = B
    if cote == 'south':
        return ch.rep(s, z2 - (P - 1), 'south')
    if cote == 'north':
        return ch.rep(s + L - 1, z1 + (P - 1), 'north')
    if cote == 'east':
        return ch.rep(x2 - (P - 1), s + L - 1, 'east')
    return ch.rep(x1 + (P - 1), s, 'west')


def rangee(ch, B, cote, s0, s1, P, choisir):
    """Une rangée de bâtiments de profondeur P le long d'un côté du pâté, de s0 à s1 ; choisir() -> (L, fonction)."""
    s = s0
    while True:
        L, fn = choisir()
        if s + L - 1 > s1:
            break
        fn(ch, lot(ch, B, cote, s, L, P), L, P)
        s += L + ch.rng.choice((1, 2, 2, 3))


def perimetre(ch, B, P, choisir, marge=2, cotes=('north', 'south', 'west', 'east')):
    """Remplit les côtés d'un pâté avec des bâtiments de profondeur P."""
    x1, z1, x2, z2 = B
    for cote in cotes:
        if cote in ('north', 'south'):
            rangee(ch, B, cote, x1 + marge, x2 - marge, P, choisir)
        else:
            rangee(ch, B, cote, z1 + P + 3, z2 - P - 3, P, choisir)


def cour(ch, B, P, genre):
    """Le cœur du pâté : stationnement (ville) ou jardins et arbres (banlieue)."""
    x1, z1, x2, z2 = B
    a1, b1, a2, b2 = x1 + P + 3, z1 + P + 3, x2 - P - 3, z2 - P - 3
    if a2 - a1 < 6 or b2 - b1 < 6:
        return
    m, rng = ch.m, ch.rng
    if genre in ('centre', 'civique', 'commercial'):
        m.fill(a1, 63, b1, a2, 63, b2, ASPH)
        for x in range(a1 + 2, a2 - 2, 4):
            m.fill(x, 63, b1 + 1, x, 63, b1 + 5, S('white_concrete'))
            m.fill(x, 63, b2 - 5, x, 63, b2 - 1, S('white_concrete'))
        ch.voitures(a1 + 3, b1 + 3, a2 - 3, b2 - 3, max(2, (a2 - a1) // 10), 'north')
    else:
        for _ in range(max(2, (a2 - a1) * (b2 - b1) // 220)):
            x, z = rng.randint(a1 + 2, a2 - 2), rng.randint(b1 + 2, b2 - 2)
            try:
                RU.arbre_rue(ch.R0, x, z, rng)
            except Exception:
                pass


# ============================================================================ bâtiments urbains
VITRES = ['light_blue_stained_glass_pane', 'gray_stained_glass_pane', 'cyan_stained_glass_pane', 'glass_pane',
          'black_stained_glass_pane']
CADRES = ['light_gray_concrete', 'gray_concrete', 'white_concrete', 'smooth_quartz', 'polished_andesite',
          'polished_deepslate', 'stone_bricks']
# enseigne en lettres géantes -> nom du lieu
ENSEIGNES = {'GROUPE BORÉAL': 'Tour du Groupe Boréal', 'LAURENTIDE': 'Tour Laurentide', 'ASSURANCES NORD': 'Tour Assurances Nord',
             'TOUR ÉTOILE': 'Tour Étoile', 'CENTRE LAVAL': 'Centre Laval', 'TOUR DU LAC': 'Tour du Lac',
             'TOUR MONTCALM': 'Tour Montcalm', 'TOUR LAURENTIA': 'Tour Laurentia', 'MAISON RADIO': 'Maison de la radio',
             'TOUR CARTIER': 'Tour Cartier', 'LE BOREAL': 'Le Boréal', 'TOUR FRONTENAC': 'Tour Frontenac'}


def enseigne(ch):
    """Une enseigne pas encore prise dans ce quartier (puis des tours sans nom)."""
    if not hasattr(ch, 'enseignes'):
        ch.enseignes = [k for k in ENSEIGNES if k != 'TOUR LAURENTIA']
        ch.rng.shuffle(ch.enseignes)
    return ch.enseignes.pop() if ch.enseignes else None


def echelle(R, a, b, y1, y2, appui):
    """Puits d'échelle (pour monter d'étage en étage) : appui en b-1, trous dans les planchers."""
    R.fill(a, y1, b - 1, a, y2, b - 1, appui)
    R.vide(a, y1, b, a, y2, b)
    for y in range(y1, y2 + 1):
        R.set(a, y, b, R.S('ladder', facing='south', waterlogged=False))


def tour(ch, R, L, P, etages=None, nom=None):
    rng = ch.rng
    et = etages or rng.randint(9, 18)
    top = 63 + 4 * et
    cad = S(rng.choice(CADRES))
    vit = S(rng.choice(VITRES))
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, top, P - 1, vit)
    R.vide(1, 64, 1, L - 2, top, P - 2)
    for a in list(range(0, L, 4)) + [L - 1]:
        R.fill(a, 64, 0, a, top, 0, cad)
        R.fill(a, 64, P - 1, a, top, P - 1, cad)
    for b in list(range(0, P, 4)) + [P - 1]:
        R.fill(0, 64, b, 0, top, b, cad)
        R.fill(L - 1, 64, b, L - 1, top, b, cad)
    for e in range(et + 1):
        y = 63 + 4 * e
        R.fill(0, y, 0, L - 1, y, P - 1, cad)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('polished_andesite'))
    # hall : portes, accueil
    R.vide(L // 2 - 2, 64, P - 1, L // 2 + 1, 66, P - 1)
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'birch')
    R.fill(L // 2 - 3, 64, P - 6, L // 2 + 2, 64, P - 6, S('smooth_quartz'))
    # étages : bureaux, lampes, un coffre de temps en temps
    for e in range(et):
        y = 64 + 4 * e
        ZM.lampe_plafond(R, L // 2, y + 2, P // 2, 'sea_lantern', 'light_gray_concrete')
        if e > 0:
            for k in range(3):
                a, b = rng.randint(3, L - 4), rng.randint(3, P - 4)
                if R.est_air(a, y, b):
                    ZM.bureau(R, a, y, b, rng.choice(['north', 'south', 'east', 'west']), 'spruce', True, None)
        if e % 3 == 1:
            ch.coffre(R, L - 2, y, 2, 'west', SI.LOOT_VILLE)
    echelle(R, 2, 2, 64, top + 1, cad)
    # toit : parapet, antenne, réservoir, héliport sur les grandes tours
    R.fill(0, top + 1, 0, L - 1, top + 1, P - 1, cad)
    R.vide(1, top + 1, 1, L - 2, top + 1, P - 2)
    R.fill(L - 4, top + 1, P - 4, L - 4, top + 9, P - 4, S('iron_bars'))
    R.set(L - 4, top + 10, P - 4, S('lightning_rod', facing='up', powered=False, waterlogged=False))
    if L >= 20 and P >= 20:
        R.fill(L // 2 - 3, top, P // 2 - 3, L // 2 + 3, top, P // 2 + 3, S('yellow_concrete'))
        R.fill(L // 2 - 2, top, P // 2 - 2, L // 2 + 2, top, P // 2 + 2, S('gray_concrete'))
        for b in range(P // 2 - 2, P // 2 + 3):
            R.set(L // 2 - 1, top, b, S('white_concrete'))
            R.set(L // 2 + 1, top, b, S('white_concrete'))
        R.set(L // 2, top, P // 2, S('white_concrete'))
    else:
        R.fill(3, top + 1, 3, 5, top + 3, 5, R.S('barrel', facing='up', open=False))
    # enseigne géante en haut de la façade
    txt = nom or enseigne(ch)
    if txt:
        w = ZM.largeur_texte(txt)
        if w <= L - 2:
            ZM.lettres(R, (L - w) // 2, top - 6, P, txt, S('white_concrete'), 'east')
        ch.lieu(R, L, P, 'tour', ENSEIGNES.get(txt, txt.title()))


def immeuble(ch, R, L, P, etages=None, commerce=None):
    rng = ch.rng
    et = etages or rng.randint(3, 6)
    top = 63 + 4 * et
    mur = S(rng.choice(['bricks', 'red_terracotta', 'light_gray_concrete', 'white_terracotta', 'brown_terracotta',
                        'stone_bricks', 'mud_bricks']))
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, top, P - 1, mur)
    R.vide(1, 64, 1, L - 2, top, P - 2)
    for e in range(1, et + 1):
        R.fill(1, 63 + 4 * e, 1, L - 2, 63 + 4 * e, P - 2, S('spruce_planks'))
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('oak_planks'))
    for e in range(et):
        y = 65 + 4 * e
        for a in range(2, L - 2, 3):
            for b in (0, P - 1):
                R.fill(a, y, b, a, y + 1, b, S('glass_pane'))
        for b in range(2, P - 2, 3):
            for a in (0, L - 1):
                R.fill(a, y, b, a, y + 1, b, S('glass_pane'))
        # balcons sur la façade
        if e > 0 and rng.random() < 0.6:
            a = rng.randint(2, L - 4)
            R.fill(a, y - 1, P, a + 2, y - 1, P, S('smooth_stone_slab', type='top'))
            for k in range(3):
                R.set(a + k, y, P, S('iron_bars'))
        # logement : lit, table, coffre
        if L >= 9 and P >= 9:
            ZM.lit(R, 2, y - 1, 2, 'north', rng.choice(['white', 'blue', 'red', 'light_gray', 'green']))
            ZM.table(R, L // 2, y - 1, P // 2, 'spruce')
            if rng.random() < 0.5:
                ch.coffre(R, L - 2, y - 1, P - 2, 'west', SI.LOOT_MAISON)
    echelle(R, L - 2, 2, 64, top - 1, mur)
    # escalier de secours sur le côté
    for e in range(1, et):
        y = 63 + 4 * e
        R.fill(-1, y, 2, -1, y, 4, S('iron_bars'))
        R.fill(-1, y - 3, 3, -1, y, 3, R.S('ladder', facing='west', waterlogged=False))
    R.fill(0, top + 1, 0, L - 1, top + 1, P - 1, S('smooth_stone_slab', type='bottom'))
    # rez-de-chaussée commercial
    if commerce:
        R.vide(1, 64, P - 1, L - 2, 66, P - 1)
        R.fill(1, 65, P - 1, L - 2, 66, P - 1, S('glass_pane'))
        ZM.porte(R, 2, 64, P - 1, 'north', 'oak')
        R.fill(L - 4, 64, P - 4, L - 2, 64, P - 4, S('smooth_quartz'))
        ch.coffre(R, L - 3, 64, 2, 'south', SI.LOOT_VILLE, baril=True)
        x, z = R.xz(L // 2, P)
        ch.panneau(x, 67, z, ['', commerce.upper()[:15], '', ''], mur=R.d('south'))
    else:
        ZM.porte(R, L // 2, 64, P - 1, 'north', 'oak')


def banque(ch, R, L, P):
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 71, P - 1, S('quartz_bricks'))
    R.vide(1, 64, 1, L - 2, 70, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('polished_diorite'))
    R.fill(0, 72, 0, L - 1, 72, P - 1, S('smooth_quartz_slab', type='bottom'))
    for a in range(1, L - 1, 3):
        R.fill(a, 64, P, a, 70, P, S('quartz_pillar', axis='y'))
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'dark_oak')
    R.fill(2, 64, P - 6, L - 3, 64, P - 6, S('polished_andesite'))
    # la chambre forte
    R.fill(2, 64, 1, 7, 68, 6, S('iron_block'))
    R.vide(3, 64, 2, 6, 67, 5)
    R.set(5, 64, 6, AIR)
    R.set(5, 65, 6, AIR)
    ch.coffre(R, 3, 64, 2, 'south', SI.LOOT_MILITAIRE)
    ch.coffre(R, 6, 64, 2, 'south', SI.LOOT_VILLE)
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 70, z, ['CAISSE', 'POPULAIRE', _nv(ch).upper()[:15], _nv(ch).upper()[15:30]], mur=R.d('south'))
    ch.lieu(R, L, P, 'banque', 'Caisse populaire de ' + _nv(ch))


def hotel(ch, R, L, P):
    immeuble(ch, R, L, P, etages=8)
    w = ZM.largeur_texte('HOTEL BOREAL')
    if w <= L:
        ZM.lettres(R, (L - w) // 2, 63 + 4 * 8 - 6, P, 'HÔTEL BORÉAL', S('red_concrete'), 'east')
    ch.lieu(R, L, P, 'hotel', 'Hôtel Boréal')


def commissariat(ch, R, L, P):
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 70, P - 1, S('light_gray_concrete'))
    R.fill(0, 68, 0, L - 1, 68, P - 1, S('blue_concrete'))
    R.vide(1, 64, 1, L - 2, 70, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('gray_concrete'))
    R.fill(0, 71, 0, L - 1, 71, P - 1, S('smooth_stone_slab', type='bottom'))
    for a in range(2, L - 2, 3):
        R.fill(a, 65, P - 1, a, 66, P - 1, S('glass_pane'))
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'iron')
    # cellules
    for k in range(3):
        a = 2 + 4 * k
        if a + 3 < L - 1:
            R.fill(a, 64, 1, a + 3, 66, 4, S('stone_bricks'))
            R.vide(a + 1, 64, 1, a + 2, 66, 3)
            R.fill(a + 1, 64, 4, a + 2, 66, 4, S('iron_bars'))
    ch.coffre(R, L - 2, 64, 2, 'west', SI.LOOT_MILITAIRE)
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 70, z, ['POLICE', 'Service de police', _nv(ch)[:15], _nv(ch)[15:30]], mur=R.d('south'))
    for k in range(2):
        x, z = R.xz(3 + 5 * k, P + 4)
        RU.voiture(ch.R0, x, z, R.d('south'), 'white', 64, 'police', portes=ch.rng.random() < 0.5)
    ch.lieu(R, L, P, 'commissariat', 'Poste de police de ' + _nv(ch))


def hotel_de_ville(ch, R, L, P):
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 73, P - 1, S('stone_bricks'))
    R.vide(1, 64, 1, L - 2, 72, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('polished_andesite'))
    for a in range(2, L - 2, 3):
        R.fill(a, 65, P - 1, a, 69, P - 1, S('glass_pane'))
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'dark_oak')
    # fronton et coupole
    for k in range(L // 2 + 1):
        R.fill(k, 74 + k // 2, P - 2, L - 1 - k, 74 + k // 2, P - 1, S('stone_brick_slab', type='bottom'))
    R.fill(L // 2 - 2, 74, P // 2 - 2, L // 2 + 2, 78, P // 2 + 2, S('oxidized_copper'))
    R.fill(L // 2, 79, P // 2, L // 2, 84, P // 2, S('iron_bars'))
    R.fill(1, 64, 2, L - 2, 64, 2, R.S('spruce_stairs', facing='north', half='bottom'))
    ch.coffre(R, 2, 64, 1, 'south', SI.LOOT_VILLE)
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 72, z, ['HÔTEL DE VILLE', _nv(ch).upper()[:15], _nv(ch).upper()[15:30], 'Fondée en 1871'], mur=R.d('south'))
    ch.lieu(R, L, P, 'hotel_ville', 'Hôtel de ville de ' + _nv(ch))


def hopital(ch, B):
    """Grand hôpital : un pâté entier (ailes, urgences, ambulances, héliport)."""
    x1, z1, x2, z2 = B
    L, P = x2 - x1 - 14, z2 - z1 - 30
    R = ch.rep(x1 + 7, z1 + 8, 'south')
    et = 5
    top = 63 + 4 * et
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, top, P - 1, S('white_concrete'))
    R.vide(1, 64, 1, L - 2, top, P - 2)
    for e in range(1, et + 1):
        R.fill(1, 63 + 4 * e, 1, L - 2, 63 + 4 * e, P - 2, S('light_gray_concrete'))
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('white_terracotta'))
    for e in range(et):
        y = 65 + 4 * e
        for a in range(2, L - 2, 3):
            for b in (0, P - 1):
                R.fill(a, y, b, a, y + 1, b, S('light_blue_stained_glass_pane'))
        # chambres : lits alignés, lampes
        for a in range(3, L - 3, 4):
            ZM.lit(R, a, y - 1, 2, 'north', 'white')
            ZM.lit(R, a, y - 1, P - 4, 'south', 'white')
        ZM.lampe_plafond(R, L // 2, y + 2, P // 2, 'sea_lantern', 'light_gray_concrete')
        ch.coffre(R, 1, y - 1, P // 2, 'east', SI.LOOT_LABO if e % 2 else SI.LOOT_VILLE)
    echelle(R, L - 3, 3, 64, top - 1, S('white_concrete'))
    # urgences : auvent rouge, portes, ambulances
    R.fill(L // 2 - 6, 67, P, L // 2 + 6, 67, P + 6, S('red_concrete'))
    for a in (L // 2 - 6, L // 2 + 6):
        R.fill(a, 64, P + 6, a, 66, P + 6, S('white_concrete'))
    R.vide(L // 2 - 2, 64, P - 1, L // 2 + 1, 66, P - 1)
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'birch', ouverte=True)
    w = ZM.largeur_texte('URGENCE')
    ZM.lettres(R, (L - w) // 2, top - 6, P, 'URGENCE', S('red_concrete'), 'east')
    for k in (-1, 1):
        x, z = R.xz(L // 2 + 4 * k, P + 10)
        try:
            RU.ambulance_blocs(ch.R0, x, z, R.d('south'))
        except Exception:
            pass
    # héliport sur le toit
    R.fill(L // 2 - 4, top + 1, P // 2 - 4, L // 2 + 4, top + 1, P // 2 + 4, S('yellow_concrete'))
    R.fill(L // 2 - 3, top + 1, P // 2 - 3, L // 2 + 3, top + 1, P // 2 + 3, S('gray_concrete'))
    for b in range(P // 2 - 2, P // 2 + 3):
        R.set(L // 2 - 1, top + 1, b, S('white_concrete'))
        R.set(L // 2 + 1, top + 1, b, S('white_concrete'))
    R.set(L // 2, top + 1, P // 2, S('white_concrete'))
    # morgue au sous-sol
    R.vide(2, 58, 2, 14, 62, 10)
    R.fill(2, 57, 2, 14, 57, 10, S('polished_andesite'))
    for a in range(3, 14, 2):
        R.set(a, 58, 3, S('iron_trapdoor', facing='south', half='bottom', open=False, powered=False, waterlogged=False))
    R.vide(15, 58, 6, 15, 63, 6)
    for y in range(58, 64):
        R.set(15, y, 7, S('white_concrete'))
        R.set(15, y, 6, R.S('ladder', facing='north', waterlogged=False))
    ch.coffre(R, 13, 58, 9, 'north', SI.LOOT_LABO)
    x, z = R.xz(L // 2, P + 1)
    ch.panneau(x, 64, z, ['HÔPITAL', 'RÉGIONAL', _nv(ch).upper()[:15], 'Urgence 24 h'], rotation=0)
    ch.lieu(R, L, P, 'hopital_ville', 'Hôpital régional de ' + _nv(ch))


def parking_etage(ch, B):
    x1, z1, x2, z2 = B
    L, P = x2 - x1 - 16, z2 - z1 - 16
    R = ch.rep(x1 + 8, z1 + 8, 'south')
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    for e in range(4):
        y = 63 + 5 * e
        R.fill(0, y, 0, L - 1, y, P - 1, S('light_gray_concrete'))
        for a in range(0, L, 8):
            for b in range(0, P, 8):
                R.fill(a, y + 1, b, a, y + 4, b, S('gray_concrete'))
        if e < 3:
            R.vide(L - 6, y, 2, L - 2, y, P - 3)
            for k in range(P - 5):
                R.set(L - 4, y + 1 + k // 5, 2 + k, S('smooth_stone_slab', type='bottom'))
        for _ in range(ch.rng.randint(3, 7)):
            a, b = ch.rng.randint(3, L - 10), ch.rng.randint(3, P - 4)
            x, z = R.xz(a, b)
            try:
                RU.voiture(ch.R0, x, z, ch.rng.choice(['north', 'south']), ch.rng.choice(COULEURS_AUTO), y + 1,
                           ch.rng.choice(['auto', 'auto', 'brulee']), portes=ch.rng.random() < 0.3)
            except Exception:
                pass
    R.fill(0, 83, 0, L - 1, 83, P - 1, S('smooth_stone_slab', type='bottom'))
    ch.coffre(R, 2, 69, 2, 'south', SI.LOOT_VILLE)
    ch.lieu(R, L, P, 'parking', 'Stationnement étagé')


def place(ch, B, nom):
    """Place publique : dalles, fontaine, statue, bancs, arbres."""
    x1, z1, x2, z2 = B
    m, rng = ch.m, ch.rng
    m.fill(x1 + 2, 63, z1 + 2, x2 - 2, 63, z2 - 2, S('polished_andesite'))
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    m.fill(cx - 4, 63, cz - 4, cx + 4, 64, cz + 4, S('stone_bricks'))
    m.fill(cx - 3, 64, cz - 3, cx + 3, 64, cz + 3, S('water', level=0))
    m.fill(cx, 64, cz, cx, 68, cz, S('chiseled_stone_bricks'))
    m.set(cx, 69, cz, S('lantern', hanging=False, waterlogged=False))
    for _ in range(10):
        x, z = rng.randint(x1 + 5, x2 - 5), rng.randint(z1 + 5, z2 - 5)
        if abs(x - cx) > 7 or abs(z - cz) > 7:
            try:
                RU.arbre_rue(ch.R0, x, z, rng)
            except Exception:
                pass
    for k in range(-8, 9, 4):
        if k:
            RU.banc(ch.R0, cx + k, cz + 8, 'north')
            RU.banc(ch.R0, cx + k, cz - 8, 'south')
    ch.panneau(cx, 64, cz + 5, ['PLACE', nom[:15], _nv(ch)[:15], ''], rotation=0)
    tableau_affichage(ch, cx - 2, cz - 12)
    ch.lieu(ch.rep(x1, z1, 'south'), x2 - x1, z2 - z1, 'place', 'Place ' + nom)


AVIS = [['AVIS DE', 'RECHERCHE', 'Martin Pelletier', '9 ans'], ['ÉVACUATION', 'Autobus au', 'stade, 7 h', 'Ordre no 7'],
        ['PRIX — JOUR 7', 'Pain 4 $', 'Eau 6 $', 'Essence 3 $/L'], ['PERDU : CHIEN', 'Caramel', 'Récompense', ''],
        ['QUARANTAINE', 'Ne touchez pas', 'les morts.', 'Santé Québec'], ['ON EST AU', 'STADE. VENEZ.', 'Famille', 'Tremblay'],
        ['DON DE SANG', 'Annulé', '', ''], ['COUVRE-FEU', '20 h', 'Restez chez', 'vous.']]


def tableau_affichage(ch, x, z):
    """Tableau d'affichage (Supplementaries) avec ses avis épinglés : recherche, prix du dernier jour, évacuation."""
    m, rng = ch.m, ch.rng
    for k in range(3):
        m.set(x + k, 64, z, S('spruce_log', axis='y'))
        m.set(x + k, 65, z, S('supplementaries:notice_board', facing='south', has_book='false'))
        m.set(x + k, 66, z, S('spruce_slab', type='bottom'))
    for k, avis in enumerate(rng.sample(AVIS, 3)):
        ch.panneau(x + k, 64, z + 1, avis, mur='south')


def parc(ch, B, nom):
    """Parc de quartier : sentiers, étang, aire de jeux, arbres, bancs."""
    x1, z1, x2, z2 = B
    m, rng = ch.m, ch.rng
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    m.fill(x1 + 4, 63, cz - 1, x2 - 4, 63, cz + 1, S('dirt_path'))
    m.fill(cx - 1, 63, z1 + 4, cx + 1, 63, z2 - 4, S('dirt_path'))
    # étang
    ex, ez = x1 + 26, z1 + 26
    for dx in range(-12, 13):
        for dz in range(-8, 9):
            if (dx / 12.0) ** 2 + (dz / 8.0) ** 2 <= 1:
                m.set(ex + dx, 62, ez + dz, S('dirt'))
                m.set(ex + dx, 63, ez + dz, S('water', level=0))
            elif (dx / 13.0) ** 2 + (dz / 9.0) ** 2 <= 1:
                m.set(ex + dx, 63, ez + dz, S('sand'))
    for k in range(5):
        m.set(ex - 6 + 3 * k, 64, ez + 2 - k % 2, S('lily_pad'))
    # aire de jeux : bac à sable, glissoire, balançoires
    jx, jz = x2 - 30, z2 - 30
    m.fill(jx, 63, jz, jx + 14, 63, jz + 10, S('sand'))
    for k in range(4):
        m.set(jx + 2 + k, 64 + k, jz + 2, S('quartz_stairs', facing='west', half='bottom', shape='straight', waterlogged=False))
    m.fill(jx + 6, 64, jz + 2, jx + 6, 67, jz + 2, S('red_concrete'))
    for x in (jx + 9, jx + 13):
        m.fill(x, 64, jz + 6, x, 67, jz + 6, S('spruce_fence', waterlogged=False))
    m.fill(jx + 9, 68, jz + 6, jx + 13, 68, jz + 6, S('spruce_planks'))
    for x in (jx + 10, jx + 12):
        m.fill(x, 66, jz + 6, x, 67, jz + 6, S('chain', axis='y', waterlogged=False))
        m.set(x, 65, jz + 6, S('spruce_slab', type='bottom', waterlogged=False))
    for _ in range(26):
        x, z = rng.randint(x1 + 4, x2 - 4), rng.randint(z1 + 4, z2 - 4)
        if abs(x - cx) > 3 and abs(z - cz) > 3 and abs(x - ex) > 15 and not (jx - 2 <= x <= jx + 16 and jz - 2 <= z <= jz + 12):
            try:
                RU.arbre_rue(ch.R0, x, z, rng)
            except Exception:
                pass
    for k in range(-24, 25, 12):
        if k:
            RU.banc(ch.R0, cx + k, cz + 2, 'north')
            RU.lampadaire_parc(ch.R0, cx + k + 2, cz - 2)
    ch.panneau(cx + 3, 64, z2 - 3, ['PARC', nom[:15], 'Ville de', _nv(ch)[:15]], rotation=0)
    ch.lieu(ch.rep(x1, z1, 'south'), x2 - x1, z2 - z1, 'parc', 'Parc ' + nom)


# ---------------------------------------------------------------- industriel
def entrepot(ch, R, L, P):
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 73, P - 1, S('light_gray_concrete' if ch.rng.random() < 0.5 else 'iron_block'))
    R.vide(1, 64, 1, L - 2, 73, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('smooth_stone'))
    R.fill(0, 74, 0, L - 1, 74, P - 1, S('smooth_stone_slab', type='bottom'))
    for a in range(3, L - 6, 9):
        R.vide(a, 64, P - 1, a + 4, 68, P - 1)
        R.fill(a, 68, P - 1, a + 4, 68, P - 1, S('iron_trapdoor', facing='north', half='top', open=False, powered=False,
                                                    waterlogged=False))
    for b in range(3, P - 4, 4):
        R.fill(3, 64, b, L - 4, 66, b, R.S('barrel', facing='up', open=False))
    for k in range(3):
        ch.coffre(R, ch.rng.randint(2, L - 3), 64, ch.rng.choice((2, P - 3)), 'south', SI.LOOT_VILLE)
    ch.lieu(R, L, P, 'entrepot', 'Entrepôt')


def usine(ch, B):
    x1, z1, x2, z2 = B
    L, P = x2 - x1 - 20, z2 - z1 - 34
    R = ch.rep(x1 + 10, z1 + 10, 'south')
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 79, P - 1, S('bricks'))
    R.vide(1, 64, 1, L - 2, 79, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('gray_concrete'))
    # toit en dents de scie
    for a in range(0, L, 6):
        for k in range(5):
            R.fill(a + k, 80 + k, 0, a + k, 80 + k, P - 1, S('iron_block') if k < 4 else S('glass'))
    for a in range(4, L - 4, 5):
        for b in (0, P - 1):
            R.fill(a, 67, b, a + 1, 75, b, S('glass_pane'))
    # cheminées
    for k in range(3):
        a, b = 6 + k * 14, 4
        if a + 2 < L:
            R.fill(a, 80, b, a + 2, 110, b + 2, S('bricks'))
            R.vide(a + 1, 80, b + 1, a + 1, 110, b + 1)
    # machines et chaînes de montage
    for b in range(6, P - 6, 6):
        R.fill(4, 64, b, L - 5, 64, b, S('smooth_stone_slab', type='top'))
        for a in range(6, L - 6, 7):
            R.set(a, 65, b, S('blast_furnace', facing='south', lit=False))
    for k in range(4):
        ch.coffre(R, ch.rng.randint(2, L - 3), 64, ch.rng.randint(2, P - 3), 'south', SI.LOOT_VILLE)
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'iron')
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 70, z, ['USINE', 'BORÉAL MÉTAL', _nv(ch)[:15], ''], mur=R.d('south'))
    ch.lieu(R, L, P, 'usine', 'Usine Boréal Métal')


def citernes(ch, B):
    x1, z1, x2, z2 = B
    m = ch.m
    for k, (cx, cz) in enumerate(((x1 + 18, z1 + 18), (x1 + 44, z1 + 18), (x1 + 18, z1 + 44), (x1 + 44, z1 + 44))):
        r = 9
        for y in range(64, 84):
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    d = (dx * dx + dz * dz) ** 0.5
                    if r - 1 <= d <= r:
                        m.set(cx + dx, y, cz + dz, S('white_concrete' if y % 6 else 'light_gray_concrete'))
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r:
                    m.set(cx + dx, 84, cz + dz, S('light_gray_concrete'))
        m.fill(cx + r, 64, cz, cx + r, 84, cz, S('ladder', facing='east', waterlogged=False))
    # tuyaux
    m.fill(x1 + 18, 66, z1 + 30, x1 + 44, 66, z1 + 30, S('iron_block'))
    m.fill(x1 + 30, 66, z1 + 18, x1 + 30, 66, z1 + 44, S('iron_block'))
    ch.lieux.append(('depot_carburant', 'Réservoirs de carburant', x1 + 31, z1 + 31, 28, 28))


def grue(ch, x, z, h=46, bras=28):
    m = ch.m
    m.fill(x - 1, 64, z - 1, x + 1, 64 + h, z + 1, S('yellow_concrete'))
    m.vide(x, 64, z, x, 63 + h, z)
    for y in range(64, 64 + h):
        m.set(x, y, z, S('ladder', facing='south', waterlogged=False))
        m.set(x, y, z - 1, S('yellow_concrete'))
    m.fill(x - 2, 64 + h, z - 2, x + 2, 66 + h, z + 2, S('yellow_concrete'))
    m.fill(x - 10, 67 + h, z, x + bras, 67 + h, z, S('yellow_concrete'))
    m.fill(x - 10, 63 + h, z - 1, x - 6, 66 + h, z + 1, S('gray_concrete'))
    m.fill(x + bras - 4, 50 + h, z, x + bras - 4, 66 + h, z, S('chain', axis='y', waterlogged=False))
    m.fill(x + bras - 6, 47 + h, z - 1, x + bras - 2, 49 + h, z + 1, S('orange_concrete'))
    # centre du lieu = le mât (za_p129 sait la faire tomber : h=46, bras=28)
    ch.lieux.append(('grue', 'Grue de chantier', x, z, bras + 2, 6))


def conteneurs(ch, B, n):
    x1, z1, x2, z2 = B
    m, rng = ch.m, ch.rng
    if x2 - x1 < 18 or z2 - z1 < 12:
        return
    for _ in range(n):
        x, z = rng.randint(x1 + 4, x2 - 12), rng.randint(z1 + 4, z2 - 6)
        col = rng.choice(['red', 'blue', 'green', 'orange', 'gray', 'white', 'cyan'])
        h = rng.choice((0, 0, 3))
        m.fill(x, 64 + h, z, x + 7, 66 + h, z + 2, S(col + '_concrete'))
        if rng.random() < 0.3:
            ch.coffre(ch.R0, x, 64, z + 3, 'north', SI.LOOT_VILLE, baril=True)


