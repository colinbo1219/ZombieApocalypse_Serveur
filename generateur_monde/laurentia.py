# -*- coding: utf-8 -*-
"""laurentia : la ville de Laurentia (directeur artistique : « des villes mémorables »).

Neuf quartiers de 240 x 240 blocs (une grille 3 x 3 centrée en (-1800, 3600), dans les plaines du sud), chacun un site
du plan (type « quartier ») : centre-ville (tours, métro), quartier civique (hôpital, police, hôtel de ville, métro),
boulevard commercial, banlieues (maisons, école, église, parc), zones industrielles (entrepôts, usine, citernes, grue,
rails). Chaque quartier a son sort : évacué, abandonné, pillé, brûlé, envahi, tenu par une faction, en quarantaine.
Les avenues de bordure (4 blocs de chaque côté) forment avec le quartier voisin des avenues de 8 ; les rues intérieures
font 7 blocs. Sol de marche à y=64 (local), comme les autres sites ; le métro descend à y=50.
"""
import random

import numpy as np

import sites as SI
import batisse as BA
from batisse import Chantier, S, AIR, ZM, RU, COULEURS_AUTO
from za_blocs import Monde
from za_meubles import Ctx, Repere

T = 240
DEMI = T // 2
Y0 = 44            # bas du chantier (métro, parkings)
HAUT = 120         # jusqu'à y=163 (tours)
CENTRE = (-1800, 3600)
YSOL = 67          # hauteur du sol de toute la ville (même valeur partout : les avenues se raccordent)

QUARTIERS = [
    # (i, j, clé, nom, genre, état)
    (-1, -1, 'erables', 'Les Érables', 'banlieue', 'evacuee'),
    (0, -1, 'saint_joseph', 'Saint-Joseph', 'banlieue', 'faction'),
    (1, -1, 'laurier', "Parc d'affaires Laurier", 'industriel', 'envahie'),
    (-1, 0, 'vieux', 'Vieux-Laurentia', 'banlieue', 'abandon'),
    (0, 0, 'centre', 'Centre-ville', 'centre', 'envahie'),
    (1, 0, 'hopital', "Quartier de l'Hôpital", 'civique', 'quarantaine'),
    (-1, 1, 'les_pins', 'Les Pins', 'banlieue', 'brulee'),
    (0, 1, 'commerces', 'Boulevard des Commerces', 'commercial', 'pillee'),
    (1, 1, 'industriel_sud', 'Zone industrielle sud', 'industriel', 'brulee'),
]
# lignes de métro : tunnel est-ouest sous la rue centrale (z local 0), dans ces quartiers
METRO = {'centre', 'hopital'}

ASPH = S('gray_concrete')
TROTTOIR = S('smooth_stone')
BORDURE = S('polished_andesite')


def sites_du_plan():
    out = []
    for n, (i, j, k, nom, genre, etat) in enumerate(QUARTIERS):
        out.append({'id': 'laurentia_' + k, 'type': 'quartier', 'nom': 'Laurentia — ' + nom,
                    'x': CENTRE[0] + i * T, 'z': CENTRE[1] + j * T, 'larg': T, 'prof': T, 'y': YSOL,
                    'genre': genre, 'etat': etat, 'cle': k, 'graine': 5100 + n, 'bible': True})
    return out


# ============================================================================ chantier de quartier (sous-sol compris)
class ChantierVille(Chantier):
    def __init__(self, site):
        self.site = site
        self.rng = random.Random(site['graine'])
        self.m = Monde(-DEMI, Y0, -DEMI, T, HAUT, T)
        self.ctx = Ctx(self.m, site['graine'])
        self.coffres = []
        self.lieux = []
        m = self.m
        x0, z0, x1, z1 = -DEMI, -DEMI, DEMI - 1, DEMI - 1
        m.fill(x0, Y0, z0, x1, 57, z1, S('stone'))
        m.fill(x0, 58, z0, x1, 62, z1, S('dirt'))
        m.fill(x0, 63, z0, x1, 63, z1, S('grass_block', snowy=False))
        self.R0 = Repere(self.ctx, 0, 0)
        self.x0, self.z0, self.x1, self.z1 = x0, z0, x1, z1


# ============================================================================ rues
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


def rues(ch, nom_q):
    m, rng = ch.m, ch.rng
    # trottoirs (bandes de 2) d'abord, chaussées par-dessus
    for (a, b) in ((-116, -115), (114, 115), (-5, -4), (4, 5)):
        m.fill(-DEMI, 63, a, DEMI - 1, 63, b, TROTTOIR)
        m.fill(a, 63, -DEMI, b, 63, DEMI - 1, TROTTOIR)
    for (a, b) in ((-DEMI, -117), (116, DEMI - 1), (-3, 3)):
        m.fill(-DEMI, 63, a, DEMI - 1, 63, b, ASPH)
        m.vide(-DEMI, 64, a, DEMI - 1, 75, b)
        m.fill(a, 63, -DEMI, b, 63, DEMI - 1, ASPH)
        m.vide(a, 64, -DEMI, b, 75, DEMI - 1)
    # marquage : pointillés jaunes au milieu des rues, double ligne au bord du quartier (milieu des avenues)
    for t in range(-DEMI, DEMI):
        if abs(t) > 4 and t % 6 < 3:
            m.set(t, 63, 0, S('yellow_concrete'))
            m.set(0, 63, t, S('yellow_concrete'))
        if not (-118 <= t <= -114 or 113 <= t <= 117 or -4 <= t <= 4):
            for e in (-DEMI, DEMI - 1):
                m.set(t, 63, e, S('yellow_concrete'))
                m.set(e, 63, t, S('yellow_concrete'))
    # passages piétons autour du carrefour central
    for k in range(-3, 4):
        if k % 2 == 0:
            for e in (-7, -6, 6, 7):
                m.set(e, 63, k, S('white_concrete'))
                m.set(k, 63, e, S('white_concrete'))
    # lampadaires (tous éteints : plus de courant), feux, mobilier
    for t in range(-108, 109, 16):
        if abs(t) < 10:
            continue
        RU.lampadaire(ch.R0, t, -5, 'south')
        RU.lampadaire(ch.R0, t, 5, 'north')
        RU.lampadaire(ch.R0, -5, t, 'east')
        RU.lampadaire(ch.R0, 5, t, 'west')
        RU.lampadaire(ch.R0, t, -115, 'north')
        RU.lampadaire(ch.R0, t, 114, 'south')
        RU.lampadaire(ch.R0, -115, t, 'west')
        RU.lampadaire(ch.R0, 114, t, 'east')
    RU.feu_circulation(ch.R0, -5, -5, 'south', 3, 'north')
    RU.feu_circulation(ch.R0, 5, 5, 'north', 3, 'south')
    RU.feu_circulation(ch.R0, 5, -5, 'west', 3, 'east')
    RU.feu_circulation(ch.R0, -5, 5, 'east', 3, 'west')
    for t in range(-100, 101, 32):
        if abs(t) < 12:
            continue
        RU.poubelle(ch.R0, t + 3, -4)
        RU.borne_fontaine(ch.R0, t + 5, 4)
        RU.banc(ch.R0, -4, t + 4, 'east')
    RU.boite_postale(ch.R0, 4, -12, 'west')
    try:
        RU.abribus(ch.ctx, ch.R0, 20, 6, 6, 'north')
    except Exception:
        pass
    # plaques de rue au carrefour
    noms = ['rue Principale', 'avenue Laurier', 'rue Saint-Denis', 'rue des Érables', 'boul. Boréal', 'rue Notre-Dame',
            'rue du Parc', 'avenue du Lac', 'rue Champlain', 'rue de la Gare']
    ch.panneau(-5, 64, -6, ['', rng.choice(noms), rng.choice(noms), ''], rotation=0)
    ch.panneau(4, 64, 6, ['LAURENTIA', nom_q[:15], nom_q[15:30], ''], rotation=8)


def blocs():
    """Les quatre pâtés de maisons d'un quartier (x1, z1, x2, z2)."""
    return [(-113, -113, -7, -7), (7, -113, 113, -7), (-113, 7, -7, 113), (7, 7, 113, 113)]


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
    ch.panneau(x, 70, z, ['CAISSE', 'POPULAIRE', 'LAURENTIA', ''], mur=R.d('south'))
    ch.lieu(R, L, P, 'banque', 'Caisse populaire de Laurentia')


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
    ch.panneau(x, 70, z, ['POLICE', 'Service de police', 'de Laurentia', ''], mur=R.d('south'))
    for k in range(2):
        x, z = R.xz(3 + 5 * k, P + 4)
        RU.voiture(ch.R0, x, z, R.d('south'), 'white', 64, 'police', portes=ch.rng.random() < 0.5)
    ch.lieu(R, L, P, 'commissariat', 'Poste de police de Laurentia')


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
    ch.panneau(x, 72, z, ['HÔTEL DE VILLE', 'LAURENTIA', 'Fondée en 1871', ''], mur=R.d('south'))
    ch.lieu(R, L, P, 'hotel_ville', 'Hôtel de ville de Laurentia')


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
    ch.panneau(x, 64, z, ['HÔPITAL', 'RÉGIONAL DE', 'LAURENTIA', 'Urgence 24 h'], rotation=0)
    ch.lieu(R, L, P, 'hopital_ville', 'Hôpital régional de Laurentia')


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
    ch.panneau(cx, 64, cz + 5, ['PLACE', nom[:15], 'Laurentia', ''], rotation=0)
    ch.lieu(ch.rep(x1, z1, 'south'), x2 - x1, z2 - z1, 'place', 'Place ' + nom)


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
    ch.panneau(cx + 3, 64, z2 - 3, ['PARC', nom[:15], 'Ville de Laurentia', ''], rotation=0)
    ch.lieu(ch.rep(x1, z1, 'south'), x2 - x1, z2 - z1, 'parc', 'Parc ' + nom)


def metro(ch):
    """Station de métro sous la rue centrale (tunnel est-ouest, raccordé au quartier voisin)."""
    m = ch.m
    # tunnel sur toute la largeur du quartier : z -3..3, y 49..55, voies sur y 49
    m.vide(-DEMI, 49, -3, DEMI - 1, 55, 3)
    m.fill(-DEMI, 48, -3, DEMI - 1, 48, 3, S('gravel'))
    m.fill(-DEMI, 56, -4, DEMI - 1, 56, 4, S('stone_bricks'))
    m.fill(-DEMI, 48, -4, DEMI - 1, 56, -4, S('stone_bricks'))
    m.fill(-DEMI, 48, 4, DEMI - 1, 56, 4, S('stone_bricks'))
    for x in range(-DEMI, DEMI):
        m.set(x, 49, -1, S('rail', shape='east_west', waterlogged=False))
        m.set(x, 49, 1, S('rail', shape='east_west', waterlogged=False))
    # quai côté nord (z -11..-5) avec escaliers vers la surface
    m.vide(20, 49, -11, 70, 55, -4)
    m.fill(20, 48, -11, 70, 49, -5, S('polished_andesite'))
    m.fill(20, 49, -5, 70, 49, -5, S('yellow_concrete'))
    for x in range(24, 70, 8):
        m.fill(x, 50, -10, x, 55, -10, S('white_concrete'))
        ch.ctx.lampe(x, 55, -7, S('sea_lantern'), S('light_gray_concrete'))
    for k in range(13):
        m.vide(30 + k, 50 + k // 2, -13, 32 + k, 56 + k // 2, -12)
    # bouche de métro à la surface (sur le trottoir nord)
    m.vide(38, 56, -13, 44, 64, -12)
    for k in range(7):
        m.fill(38 + k, 56 + k, -13, 38 + k, 56 + k, -12, S('stone_brick_slab', type='bottom'))
    m.fill(37, 64, -14, 45, 64, -14, S('green_concrete'))
    m.fill(37, 66, -14, 45, 66, -11, S('green_concrete'))
    m.fill(37, 64, -11, 37, 65, -11, S('green_concrete'))
    m.fill(45, 64, -11, 45, 65, -11, S('green_concrete'))
    ch.panneau(41, 65, -14, ['MÉTRO', 'Ligne 1', 'Centre — Hôpital', ''], mur='north')
    ch.coffre(ch.R0, 66, 49, -10, 'west', SI.LOOT_VILLE)
    # wagon arrêté au quai
    m.fill(30, 50, -2, 58, 53, 2, S('white_concrete'))
    m.vide(31, 50, -1, 57, 52, 1)
    for x in range(32, 58, 4):
        m.fill(x, 51, -2, x + 1, 52, -2, S('glass_pane'))
    m.fill(30, 52, -2, 58, 52, -2, S('blue_concrete'))
    ch.lieux.append(('metro', 'Station de métro de Laurentia', 45, -5, 30, 10))


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
    ch.panneau(x, 70, z, ['USINE', 'BORÉAL MÉTAL', 'Laurentia', ''], mur=R.d('south'))
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


def conteneurs(ch, B, n):
    x1, z1, x2, z2 = B
    m, rng = ch.m, ch.rng
    for _ in range(n):
        x, z = rng.randint(x1 + 4, x2 - 12), rng.randint(z1 + 4, z2 - 6)
        col = rng.choice(['red', 'blue', 'green', 'orange', 'gray', 'white', 'cyan'])
        h = rng.choice((0, 0, 3))
        m.fill(x, 64 + h, z, x + 7, 66 + h, z + 2, S(col + '_concrete'))
        if rng.random() < 0.3:
            ch.coffre(ch.R0, x, 64, z + 3, 'north', SI.LOOT_VILLE, baril=True)


def rails_bord(ch):
    """Voie ferrée de desserte le long du bord sud du quartier (trottoir sud transformé en ballast)."""
    m = ch.m
    for x in range(-DEMI + 1, DEMI - 1):
        m.set(x, 63, 111, S('gravel'))
        m.set(x, 64, 111, S('rail', shape='east_west', waterlogged=False))
    for x in range(-90, 60, 22):
        m.fill(x, 64, 109, x + 16, 67, 113, S('brown_concrete'))
        m.vide(x + 1, 65, 110, x + 15, 66, 112)


# ============================================================================ les quartiers
def q_centre(ch):
    rng = ch.rng
    B = blocs()
    metro(ch)
    place(ch, B[3], 'Champlain')
    commerces = ['Restaurant', 'Pharmacie', 'Boutique', 'Café', 'Nettoyeur', 'Quincaillerie', 'Librairie', 'Bar',
                 'Fleuriste', None]

    def mix():
        if rng.random() < 0.4:
            return (rng.choice((18, 20)), lambda c, R, L, P: tour(c, R, L, P))
        return (rng.choice((14, 16)), lambda c, R, L, P: immeuble(c, R, L, P, etages=rng.randint(4, 8),
                                                                   commerce=rng.choice(commerces)))
    P = 22
    for k, b in enumerate(B[:3]):
        x1, z1, x2, z2 = b
        if k == 0:
            tour(ch, lot(ch, b, 'north', x1 + 3, 22, P), 22, P, etages=rng.randint(17, 20), nom='TOUR LAURENTIA')
            banque(ch, lot(ch, b, 'south', x1 + 3, 20, P), 20, P)
            rangee(ch, b, 'north', x1 + 27, x2 - 2, P, mix)
            rangee(ch, b, 'south', x1 + 25, x2 - 2, P, mix)
        elif k == 1:
            hotel(ch, lot(ch, b, 'north', x1 + 3, 24, P), 24, P)
            rangee(ch, b, 'north', x1 + 29, x2 - 2, P, mix)
            rangee(ch, b, 'south', x1 + 2, x2 - 2, P, mix)
        else:
            rangee(ch, b, 'north', x1 + 2, x2 - 2, P, mix)
            rangee(ch, b, 'south', x1 + 2, x2 - 2, P, mix)
        perimetre(ch, b, P, mix, cotes=('west', 'east'))
        cour(ch, b, P, 'centre')


def q_civique(ch):
    rng = ch.rng
    B = blocs()
    metro(ch)
    hopital(ch, B[1])
    parking_etage(ch, B[3])
    b = B[0]
    x1, z1, x2, z2 = b
    commissariat(ch, lot(ch, b, 'south', x1 + 6, 26, 18), 26, 18)
    hotel_de_ville(ch, lot(ch, b, 'north', x1 + 30, 30, 22), 30, 22)
    BA.caserne(ch, lot(ch, b, 'south', x2 - 24, 15, 13), 15, 13, 'Laurentia')
    bureaux = lambda: (rng.choice((12, 14)), lambda c, R, L, P: immeuble(c, R, L, P, etages=rng.randint(3, 5)))
    rangee(ch, b, 'north', x1 + 2, x1 + 27, 18, bureaux)
    rangee(ch, b, 'north', x1 + 63, x2 - 2, 18, bureaux)
    rangee(ch, b, 'south', x1 + 35, x2 - 27, 18, bureaux)
    perimetre(ch, b, 18, bureaux, cotes=('west', 'east'))
    cour(ch, b, 18, 'civique')
    b = B[2]
    perimetre(ch, b, 14, lambda: (rng.choice((12, 14)), lambda c, R, L, P: immeuble(
        c, R, L, P, commerce=rng.choice([None, None, 'Pharmacie', 'Dépanneur', 'Restaurant']))))
    cour(ch, b, 14, 'civique')


def q_commercial(ch):
    rng = ch.rng
    B = blocs()

    def magasin(c, R, L, P):
        nom = rng.choice(['Épicerie', 'Quincaillerie', 'Restaurant', 'Pharmacie', 'Vêtements', 'Électronique',
                          'Dépanneur', 'Animalerie', 'Meubles', 'Sports', 'Casse-croûte', 'Nettoyeur'])
        BA.commerce(c, R, L, P, nom)
    for b in (B[0], B[1], B[2]):
        perimetre(ch, b, 14, lambda: (rng.choice((12, 14, 16)), magasin))
        cour(ch, b, 14, 'commercial')
    # grand magasin + station-service dans le dernier pâté
    b = B[3]
    x1, z1, x2, z2 = b
    R = ch.rep(x1 + 6, z1 + 6, 'south')
    BA.commerce(ch, R, 60, 40, 'MAGASIN À RAYONS')
    ch.lieu(R, 60, 40, 'grand_magasin', 'Magasin à rayons Laurentia')
    m = ch.m
    sx, sz = x1 + 20, z2 - 30
    m.fill(sx, 63, sz, sx + 30, 63, sz + 20, ASPH)
    m.fill(sx + 4, 69, sz + 4, sx + 26, 69, sz + 14, S('white_concrete'))
    for x in (sx + 5, sx + 25):
        for z in (sz + 5, sz + 13):
            m.fill(x, 64, z, x, 68, z, S('light_gray_concrete'))
    for x in range(sx + 9, sx + 23, 6):
        m.fill(x, 64, sz + 9, x, 65, sz + 9, S('red_concrete'))
    BA.commerce(ch, ch.rep(sx + 32, sz + 4, 'south'), 12, 10, 'Station-service')
    ch.lieux.append(('station', 'Station-service du boulevard', sx + 15, sz + 10, 18, 12))
    ch.voitures(sx + 4, sz + 4, sx + 26, sz + 16, 4, 'east')


def q_banlieue(ch, nom_q):
    rng = ch.rng
    B = blocs()

    def maison(c, R, L, P):
        BA.maison(c, R, L, P, etages=2 if rng.random() < 0.35 else 1)
        for a in range(-1, L + 1):
            R.set(a, 64, P + 1, S('spruce_fence'))
        R.set(L // 2, 64, P + 1, AIR)
    speciaux = ['ecole', 'eglise', 'parc', 'sport']
    rng.shuffle(speciaux)
    for k, b in enumerate(B):
        sp = speciaux[k]
        x1, z1, x2, z2 = b
        if sp == 'parc':
            parc(ch, b, rng.choice(['des Pionniers', 'du Souvenir', 'Jeanne-Mance', 'Laval']))
            continue
        if sp == 'sport':
            m = ch.m
            m.fill(x1 + 10, 63, z1 + 10, x2 - 10, 63, z2 - 40, S('green_concrete'))
            for x in range(x1 + 10, x2 - 9, 2):
                m.set(x, 64, z1 + 10, S('white_concrete'))
                m.set(x, 64, z2 - 40, S('white_concrete'))
            m.fill(x1 + 10, 64, (z1 + z2 - 30) // 2, x2 - 10, 64, (z1 + z2 - 30) // 2, S('white_carpet'))
            for z in (z1 + 12, z2 - 42):
                m.fill((x1 + x2) // 2 - 3, 64, z, (x1 + x2) // 2 + 3, 66, z, S('iron_bars'))
            ch.lieux.append(('parc', 'Terrain de soccer de ' + nom_q, (x1 + x2) // 2, (z1 + z2 - 30) // 2, 40, 30))
            s = x1 + 4
            while s + 12 < x2 - 4:
                maison(ch, lot(ch, b, 'south', s, 11, 10), 11, 10)
                s += 13
            continue
        if sp == 'ecole':
            BA.ecole(ch, lot(ch, b, 'north', x1 + 20, 25, 20), 25, 20, 'Laurentia')
        elif sp == 'eglise':
            BA.eglise(ch, lot(ch, b, 'north', x1 + 30, 15, 25), 15, 25)
            ch.lieu(lot(ch, b, 'north', x1 + 30, 15, 25), 15, 25, 'eglise', 'Église Saint-Joseph' if 'Joseph' in nom_q
                    else 'Église de ' + nom_q)
        s = x1 + 4
        while s + 12 < x2 - 4:
            maison(ch, lot(ch, b, 'south', s, 11, 10), 11, 10)
            s += 13
        # rangée nord : autour de l'école ou de l'église (posées entre x1+20 et x1+45) et du dépanneur (x2-18)
        for (d, f) in ((x1 + 4, x1 + 18), (x1 + 47, x2 - 21)):
            s = d
            while s + 10 <= f:
                maison(ch, lot(ch, b, 'north', s, 10, 10), 10, 10)
                s += 13
        for cote in ('west', 'east'):
            s = z1 + 30
            while s + 11 < z2 - 16:
                maison(ch, lot(ch, b, cote, s, 10, 10), 10, 10)
                s += 13
        # rue résidentielle au milieu du pâté : deux rangées de maisons de plus, face à face
        zm = (z1 + z2) // 2 + 6
        m = ch.m
        m.fill(x1 + 14, 63, zm - 2, x2 - 14, 63, zm + 2, ASPH)
        m.vide(x1 + 14, 64, zm - 2, x2 - 14, 72, zm + 2)
        m.fill(x1 + 14, 63, zm - 3, x2 - 14, 63, zm - 3, TROTTOIR)
        m.fill(x1 + 14, 63, zm + 3, x2 - 14, 63, zm + 3, TROTTOIR)
        Bn, Bs = (x1, z1, x2, zm - 4), (x1, zm + 4, x2, z2)
        for (Bx, cote) in ((Bn, 'south'), (Bs, 'north')):
            s = x1 + 16
            while s + 10 <= x2 - 16:
                maison(ch, lot(ch, Bx, cote, s, 10, 10), 10, 10)
                s += 12
        for t in range(x1 + 20, x2 - 16, 18):
            RU.lampadaire(ch.R0, t, zm - 3, 'south')
        ch.voitures(x1 + 18, zm - 1, x2 - 18, zm + 1, 2, 'east')
        BA.commerce(ch, lot(ch, b, 'north', x2 - 18, 14, 12), 14, 12, 'Dépanneur')
        ch.lieu(lot(ch, b, 'north', x2 - 18, 14, 12), 14, 12, 'depanneur', 'Dépanneur de ' + nom_q)


def q_industriel(ch):
    rng = ch.rng
    B = blocs()
    usine(ch, B[0])
    citernes(ch, B[1])
    grue(ch, B[1][2] - 18, B[1][3] - 14)
    for b in (B[2], B[3]):
        x1, z1, x2, z2 = b
        for k in range(2):
            R = ch.rep(x1 + 6 + k * 52, z1 + 6, 'south')
            if x1 + 6 + k * 52 + 46 < x2:
                entrepot(ch, R, 46, 40)
        conteneurs(ch, (x1, z1 + 52, x2, z2 - 6), 14)
        ch.voitures(x1 + 10, z1 + 50, x2 - 10, z2 - 10, 4, 'east')
    rails_bord(ch)


# ============================================================================ le sort de chaque quartier (couche « apocalypse »)
def etat_quartier(ch, etat):
    m, rng = ch.m, ch.rng
    rs = np.random.default_rng(rng.randint(0, 1 << 30))
    pal = m.pal
    asphalte = np.array([p in ('minecraft:gray_concrete', 'minecraft:smooth_stone') for p in pal], bool)
    sol = np.zeros(m.a.shape, bool)
    yl = 63 - m.y0
    sol[yl] = asphalte[m.a[yl]]
    alea = rs.random(m.a.shape)
    # la nature reprend la chaussée (sauf là où une faction entretient)
    reprise = {'abandon': 0.18, 'envahie': 0.12, 'evacuee': 0.08, 'pillee': 0.06, 'brulee': 0.03,
               'quarantaine': 0.03, 'faction': 0.0}[etat]
    if reprise:
        mousse, gazon = m.id(S('moss_block')), m.id(S('grass_block', snowy=False))
        terre = m.id(S('coarse_dirt'))
        m.a[sol & (alea < reprise * 0.4)] = mousse
        m.a[sol & (alea >= reprise * 0.4) & (alea < reprise * 0.7)] = gazon
        m.a[sol & (alea >= reprise * 0.7) & (alea < reprise)] = terre
        herbe = m.id(S('grass'))
        dessus = np.zeros(m.a.shape, bool)
        dessus[yl + 1] = np.isin(m.a[yl], [mousse, gazon]) & (m.a[yl + 1] == 0)
        m.a[dessus & (alea < 0.7)] = herbe
    if etat == 'brulee':
        bois = np.array([any(k in p for k in ('planks', 'terracotta', 'concrete', 'bricks', 'wool', 'log', 'quartz'))
                         and 'gray_concrete' not in p for p in pal], bool)
        cible = bois[m.a] & (alea < 0.45)
        cible[:yl + 1] = False
        noir = [m.id(S('blackstone')), m.id(S('coal_block')), m.id(S('black_concrete')), m.id(S('basalt', axis='y'))]
        k = rs.integers(0, len(noir), m.a.shape)
        for i, nid in enumerate(noir):
            m.a[cible & (k == i)] = nid
        feuilles = np.array(['leaves' in p for p in pal], bool)
        m.a[feuilles[m.a] & (alea < 0.85)] = 0
        verre = np.array(['glass' in p for p in pal], bool)
        m.a[verre[m.a] & (alea < 0.85)] = 0
        gazon = np.array([p.startswith('minecraft:grass_block') for p in pal], bool)
        m.a[gazon[m.a] & (alea < 0.6)] = m.id(S('coarse_dirt'))
        for _ in range(30):
            x, z = rng.randint(-110, 110), rng.randint(-110, 110)
            if m.est_air(x, 64, z):
                m.set(x, 64, z, S('campfire', facing='north', lit=False, signal_fire=False, waterlogged=False))
    elif etat == 'envahie':
        for _ in range(260):
            x, z, y = rng.randint(-118, 118), rng.randint(-118, 118), rng.choice((64, 64, 64, 68, 72))
            if m.est_air(x, y, z) and not m.est_air(x, y - 1, z):
                m.set(x, y, z, rng.choice([S('cobweb'), S('bone_block', axis='y'), S('red_carpet'), S('cobweb')]))
        for _ in range(20):
            ch.voitures(-110, -3, 110, 3, 1, rng.choice(['east', 'west']))
    elif etat == 'evacuee':
        # embouteillage de l'exode sur la rue centrale, vers l'est (la sortie de la ville)
        for x in range(-108, 108, 7):
            for z in (-2, 2):
                if rng.random() < 0.8:
                    try:
                        RU.voiture(ch.R0, x, z, 'east', rng.choice(COULEURS_AUTO), 64,
                                   rng.choice(['auto', 'auto', 'auto', 'taxi']), portes=rng.random() < 0.6)
                    except Exception:
                        pass
        for (x, z, rot) in ((-30, -6, 0), (30, 6, 8), (-6, 40, 4), (6, -40, 12)):
            ch.panneau(x, 64, z, ['ÉVACUATION', 'Suivez les', 'flèches →', 'Ordre no 7'], rotation=rot)
        for _ in range(40):
            x, z = rng.randint(-110, 110), rng.choice((-6, -5, 5, 6))
            if m.est_air(x, 64, z):
                m.set(x, 64, z, S('barrel', facing='up', open=True))
    elif etat == 'faction':
        # barricades aux entrées du quartier, bannières, potagers
        for (x1, z1, x2, z2) in ((-3, -DEMI, 3, -DEMI + 1), (-3, DEMI - 2, 3, DEMI - 1), (-DEMI, -3, -DEMI + 1, 3),
                                 (DEMI - 2, -3, DEMI - 1, 3)):
            m.fill(x1, 64, z1, x2, 65, z2, S('cobblestone_wall', east='low', west='low', north='none', south='none',
                                            up=True, waterlogged=False))
            m.fill(x1, 66, z1, x2, 66, z2, S('oak_fence', waterlogged=False))
        for t in range(-100, 101, 24):
            if abs(t) > 10:
                m.set(t, 64, -6, S('green_banner', rotation=0))
                m.set(-6, 64, t, S('green_banner', rotation=4))
        for _ in range(12):
            x, z = rng.randint(-100, 100), rng.randint(-100, 100)
            if all(m.est_air(x + dx, 64, z + dz) for dx in range(3) for dz in range(3)):
                for dx in range(3):
                    for dz in range(3):
                        m.set(x + dx, 63, z + dz, S('farmland', moisture=7))
                        m.set(x + dx, 64, z + dz, S(rng.choice(['wheat', 'carrots', 'potatoes']), age=7))
        for _ in range(6):
            x, z = rng.randint(-100, 100), rng.randint(-100, 100)
            if m.est_air(x, 64, z):
                m.set(x, 64, z, S('campfire', facing='north', lit=False, signal_fire=False, waterlogged=False))
    elif etat == 'quarantaine':
        # clôture tout autour, portails aux avenues, tentes et sacs de sable
        for t in range(-DEMI + 6, DEMI - 6):
            for e in (-DEMI + 5, DEMI - 6):
                if not (-6 <= t <= 6):
                    if m.est_air(t, 64, e):
                        m.fill(t, 64, e, t, 66, e, S('iron_bars', waterlogged=False))
                    if m.est_air(e, 64, t):
                        m.fill(e, 64, t, e, 66, t, S('iron_bars', waterlogged=False))
        for (x, z, rot) in ((-8, -DEMI + 4, 0), (8, DEMI - 5, 8), (-DEMI + 4, 8, 12), (DEMI - 5, -8, 4)):
            ch.panneau(x, 64, z, ['ZONE DE', 'QUARANTAINE', 'Accès interdit', 'Forces armées'], rotation=rot)
        for _ in range(8):
            x, z = rng.randint(-100, 90), rng.randint(-100, 90)
            if all(m.est_air(x + dx, 64, z + dz) for dx in range(6) for dz in range(5)):
                for dx in range(6):
                    for dz in range(5):
                        h = 66 - abs(dz - 2)
                        m.fill(x + dx, 64, z + dz, x + dx, h, z + dz, S('white_wool'))
                m.vide(x + 1, 64, z + 1, x + 4, 65, z + 3)
                ZM.lit(Repere(ch.ctx, x + 2, z + 2), 0, 64, 0, 'north', 'green')
        for _ in range(30):
            x, z = rng.randint(-112, 112), rng.randint(-112, 112)
            if m.est_air(x, 64, z) and not m.est_air(x, 63, z):
                m.set(x, 64, z, S('mud_brick_slab', type='bottom', waterlogged=False))
    elif etat == 'pillee':
        # la moitié des portes arrachées (les deux moitiés ensemble)
        bas = np.array(['_door' in p and 'half=lower' in p for p in pal], bool)
        arr = bas[m.a] & (alea < 0.5)
        m.a[arr] = 0
        haut = np.zeros(m.a.shape, bool)
        haut[1:] = arr[:-1]
        m.a[haut] = 0
        ch.coffres = [c for i, c in enumerate(ch.coffres) if i % 2 == 0]
        for _ in range(60):
            x, z = rng.randint(-110, 110), rng.randint(-110, 110)
            if m.est_air(x, 64, z) and not m.est_air(x, 63, z):
                m.set(x, 64, z, rng.choice([S('brown_carpet'), S('white_carpet'), S('barrel', facing='up', open=True)]))
    return {'abandon': 0.6, 'envahie': 0.85, 'evacuee': 0.5, 'pillee': 0.65, 'brulee': 0.9, 'quarantaine': 0.4,
            'faction': 0.2}[etat]


# ============================================================================ point d'entrée (sites.structure_de -> batisse.quartier)
def quartier(site, plan):
    ch = ChantierVille(site)
    nom_q = site['nom'].split('— ')[-1]
    rues(ch, nom_q)
    g = site['genre']
    if g == 'centre':
        q_centre(ch)
    elif g == 'civique':
        q_civique(ch)
    elif g == 'commercial':
        q_commercial(ch)
    elif g == 'industriel':
        q_industriel(ch)
    else:
        q_banlieue(ch, nom_q)
    force = etat_quartier(ch, site['etat'])
    # « de Les Érables » -> « des Érables »
    ch.lieux = [(g, n.replace('de Les ', 'des ').replace('de Le ', 'du ').replace('primaire de Laurentia',
                'primaire ' + ('des ' + nom_q[4:] if nom_q.startswith('Les ') else 'de ' + nom_q)), x, z, dx, dz)
                for (g, n, x, z, dx, dz) in ch.lieux]
    # lampadaires de rue (éteints) : Skript les rallume quand le quartier retrouve le courant (za_p128)
    rue = [(l['x'], l['y'], l['z']) for l in ch.ctx.lampes if 'froglight' in l['on']]
    st = ch.terminer(force)
    st.lampes = rue
    return st
