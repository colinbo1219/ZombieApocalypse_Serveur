# -*- coding: utf-8 -*-
"""ville : générateur de villes complètes (conseil des 4 : « des villes avec une personnalité, pas une grille de parcelles »).

    VILLE (graine, type, taille) → QUARTIERS → RÉSEAU ROUTIER → ÎLOTS → PARCELLES → BÂTIMENTS → DÉTAILS → APOCALYPSE

* Type de ville : métropole, industrielle (autour d'une voie ferrée), résidentielle (étalée, beaucoup de parcs)...
  Le type fixe les quartiers (genre, place, sort) et le rythme des rues.
* Réseau routier hiérarchisé : boulevards (13 blocs, terre-plein planté) qui se croisent à un rond-point, avenues (9),
  rues (7), petites rues résidentielles (5), ruelles derrière les commerces (3), rue de ceinture. Les rues secondaires
  naissent dans les mailles des avenues et s'arrêtent sur elles (carrefours en T) : pas de grille régulière.
* Îlots de tailles variées ; chaque îlot reçoit une « recette » tirée selon son quartier (maisons + parc, appartements +
  stationnement, école + terrain, commerces + ruelle, tours + place...) : même quartier, jamais le même rythme.
* Bâtiments : ville_bat.py (tours, immeubles, hôpital, usine...) et batisse.py (maisons, école, église...).
* Apocalypse : un sort par quartier (évacué, abandonné, pillé, brûlé, envahi, quarantaine militaire, tenu par une
  faction, zone de guerre), appliqué couche par couche sur toute la ville.
La ville entière est construite une fois (déterministe) puis découpée en fenêtres de 240 x 240 (sites « ville_tuile »)
pour la pose dans les régions : les fenêtres ne se voient pas, un bâtiment peut être à cheval sur deux.
"""
import math
import random

import numpy as np

import sites as SI
import batisse as BA
import ville_bat as VB
from batisse import Chantier, S, AIR, ZM, RU, COULEURS_AUTO
from ville_bat import lot, rangee, perimetre, ASPH, TROTTOIR
from za_blocs import Monde
from za_meubles import Ctx, Repere

TUILE = 240
Y0 = 44            # bas du chantier (métro, morgue)
HAUT = 120         # jusqu'à y=163 local (tours)

# ---------------------------------------------------------------------------- les villes de la carte
# (le type décide des quartiers ; « sorts » : un sort par genre de quartier, dans l'ordre des quartiers du type)
VILLES = [
    {'id': 'laurentia', 'nom': 'Laurentia', 'type': 'metropole', 'x': -1800, 'z': 3600, 'n': 3, 'graine': 7101,
     'sortie': ('est', [(-700, 3600), (80, 3600)], 'Boulevard Laurentien')},
    {'id': 'saint_remi', 'nom': 'Saint-Rémi-de-la-Voie', 'type': 'industrielle', 'x': 1200, 'z': 4200, 'n': 2,
     'graine': 7202, 'sortie': ('ouest', [(500, 4200), (35, 4200)], 'Rue de la Gare')},
    {'id': 'sainte_agathe', 'nom': 'Sainte-Agathe-des-Champs', 'type': 'residentielle', 'x': -400, 'z': 3000, 'n': 2,
     'graine': 7303, 'sortie': ('est', [(-45, 3000)], 'Chemin Sainte-Agathe')},
]

# quartiers de chaque type : (genre, fx, fz, sort) — fx, fz : position relative (0..1) du « germe » du quartier
TYPES = {
    'metropole': {
        'quartiers': [('centre', 0.5, 0.5, 'envahie'), ('affaires', 0.52, 0.28, 'guerre'),
                      ('civique', 0.78, 0.5, 'quarantaine'), ('commercial', 0.5, 0.78, 'pillee'),
                      ('residentiel', 0.24, 0.5, 'evacuee'), ('residentiel', 0.78, 0.2, 'abandon'),
                      ('banlieue', 0.2, 0.82, 'brulee'), ('riche', 0.2, 0.18, 'faction'),
                      ('pauvre', 0.8, 0.85, 'envahie'), ('industriel', 0.92, 0.66, 'brulee')],
        'avenues': (120, 170), 'metro': True, 'rail': None},
    'industrielle': {
        'quartiers': [('centre', 0.5, 0.42, 'guerre'), ('industriel', 0.25, 0.75, 'faction'),
                      ('industriel', 0.78, 0.75, 'envahie'), ('gare', 0.5, 0.68, 'quarantaine'),
                      ('pauvre', 0.2, 0.25, 'envahie'), ('pauvre', 0.8, 0.25, 'brulee'),
                      ('commercial', 0.5, 0.15, 'pillee')],
        'avenues': (110, 150), 'metro': False, 'rail': 0.62, 'campagne': 0.15},
    'residentielle': {
        'quartiers': [('centre', 0.5, 0.5, 'abandon'), ('banlieue', 0.22, 0.3, 'evacuee'),
                      ('banlieue', 0.75, 0.75, 'abandon'), ('riche', 0.78, 0.25, 'faction'),
                      ('banlieue', 0.25, 0.78, 'pillee'), ('parc', 0.5, 0.2, 'abandon')],
        'avenues': (100, 130), 'metro': False, 'rail': None, 'campagne': 0.3},
}

# taille visée des îlots et largeur des rues secondaires, par genre de quartier
GENRES = {
    'centre': (58, 7), 'affaires': (66, 7), 'civique': (90, 7), 'commercial': (64, 7), 'residentiel': (56, 7),
    'banlieue': (62, 5), 'riche': (84, 5), 'pauvre': (48, 5), 'industriel': (112, 7), 'gare': (90, 7),
    'parc': (110, 5),
}
NOMS = {
    'centre': ['Centre-ville'], 'affaires': ["Quartier des affaires"], 'civique': ["Quartier de l'Hôpital"],
    'commercial': ['Boulevard des Commerces', 'Les Galeries'], 'gare': ['Quartier de la Gare'],
    'residentiel': ['Le Plateau', 'Saint-Joseph', 'Le Faubourg', 'Haut-Laurier', 'Les Cèdres'],
    'banlieue': ['Les Érables', 'Les Pins', 'Bois-Joli', 'Petite-Rivière', 'Les Bouleaux', 'Le Domaine'],
    'riche': ['Côte-Sainte-Anne', 'Le Belvédère', 'Mont-Royal-des-Pins'],
    'pauvre': ['Le Bas-de-la-Ville', 'Saint-Roch', 'Les Tanneries', 'La Cité ouvrière'],
    'industriel': ['Parc industriel', "Parc d'affaires Laurier", 'Les Forges', 'La Fonderie'],
    'parc': ['Parc régional', 'Les Prés'],
}


# ============================================================================ plan de la ville (données pures, déterministes)
class Route:
    def __init__(self, axe, c, a, b, w, k):
        self.axe, self.c, self.a, self.b, self.w, self.k = axe, c, a, b, w, k   # axe 'x' : longe x (z fixe = c)
        self.bout = None    # impasse : z du rond de virage

    def rect(self):
        h = self.w // 2
        if self.axe == 'x':
            return (self.a, self.c - h, self.b, self.c + h)
        return (self.c - h, self.a, self.c + h, self.b)


def _noms_quartiers():
    """Noms des quartiers, uniques sur toute la carte (sauf « Centre-ville »), ville par ville dans l'ordre de VILLES."""
    pris, res = set(), {}
    for w in VILLES:
        r = random.Random(w['graine'] * 31)
        res[w['id']] = []
        for (g, _fx, _fz, _s) in TYPES[w['type']]['quartiers']:
            pool = [n for n in NOMS[g] if n not in pris] or NOMS[g]
            n = r.choice(pool)
            pris.add(n)
            res[w['id']].append(n)
    return res


def plan_ville(v):
    """Rues, îlots et quartiers d'une ville, en coordonnées locales centrées (x, z dans [-S/2, S/2[).
    Lignes « nominales » (avenues) découpées en tronçons maille par maille : les avenues nord-sud se décalent d'une
    rangée à l'autre (carrefours en baïonnette), certaines s'interrompent (deux mailles fusionnent : carrefours en T),
    les petites villes laissent des coins en champs et en boisés (contour irrégulier, plus de ceinture complète)."""
    rng = random.Random(v['graine'])
    S_ = v['n'] * TUILE
    D = S_ // 2
    ty = TYPES[v['type']]
    germes = []
    noms = _noms_quartiers()[v['id']]
    for k, (g, fx, fz, sort) in enumerate(ty['quartiers']):
        nom = noms[k]
        germes.append({'id': '%s_%s%d' % (v['id'], g, k), 'genre': g, 'sort': sort, 'nom': nom,
                       'gx': -D + fx * S_ + rng.uniform(-20, 20), 'gz': -D + fz * S_ + rng.uniform(-20, 20)})

    def quartier_de(x, z):
        return min(germes, key=lambda q: (q['gx'] - x) ** 2 + (q['gz'] - z) ** 2)

    def lignes():
        L = [(-D + 3, 7, 'ceinture'), (0, 13, 'boulevard'), (D - 4, 7, 'ceinture')]
        for sens in (-1, 1):
            p = 0
            while True:
                p += sens * rng.randint(*ty['avenues'])
                if abs(p) > D - 70:
                    break
                L.append((p, 9, 'avenue'))
        return sorted(L)
    LX, LZ = lignes(), lignes()
    rail = None
    if ty['rail']:
        rz = int(-D + ty['rail'] * S_)
        LZ = sorted([l for l in LZ if abs(l[0] - rz) > 40 or l[2] != 'avenue'] + [(rz, 11, 'rail')])
        rail = Route('x', rz, -D, D - 1, 11, 'rail')
    nx, nz = len(LX) - 1, len(LZ) - 1
    # coins en campagne (petites villes) : la ville s'effiloche au lieu de finir sur un carré
    nature = set()
    if ty.get('campagne') and nx >= 3 and nz >= 3:
        for i in range(nx):
            for j in range(nz):
                bord = (i in (0, nx - 1)) + (j in (0, nz - 1))
                if bord == 2 and rng.random() < 0.75 or bord == 1 and rng.random() < ty['campagne']:
                    nature.add((i, j))
    # décalages des avenues nord-sud, rangée par rangée
    ov = {}
    for i, (c, w, k) in enumerate(LX):
        for j in range(nz):
            ov[i, j] = rng.choice((0, 0, -5, 5, -9, 9, -14, 14)) if k == 'avenue' else 0

    def xpos(i, j):
        return LX[i][0] + ov[i, j]
    # fusions : un tronçon d'avenue disparaît, deux mailles n'en font qu'une
    fus = set()
    pris = set()
    for i in range(1, nx):
        if LX[i][2] != 'avenue':
            continue
        for j in range(nz):
            a, b = (i - 1, j), (i, j)
            if a in pris or b in pris or a in nature or b in nature:
                continue
            if rng.random() < 0.25:
                fus.add((i, j))
                pris.update((a, b))
    routes = []
    # tronçons nord-sud
    for i in range(nx + 1):
        c, w, k = LX[i]
        for j in range(nz):
            cotes = [(i - 1, j), (i, j)]
            dedans = [m for m in cotes if 0 <= m[0] < nx and m not in nature]
            if not dedans or (i, j) in fus:
                continue
            za = LZ[j][0] - LZ[j][1] // 2
            zb = LZ[j + 1][0] + LZ[j + 1][1] // 2
            routes.append(Route('z', xpos(i, j), max(-D, za), min(D - 1, zb), w, k))
    # tronçons est-ouest (ils vont jusqu'aux avenues décalées, de part et d'autre)
    for j in range(nz + 1):
        c, w, k = LZ[j]
        if k == 'rail':
            continue
        for i in range(nx):
            cotes = [(i, j - 1), (i, j)]
            dedans = [m for m in cotes if 0 <= m[1] < nz and m not in nature]
            if not dedans:
                continue
            rangs = [r for r in (j - 1, j) if 0 <= r < nz]
            xa = min(xpos(i, r) for r in rangs) - LX[i][1] // 2
            xb = max(xpos(i + 1, r) for r in rangs) + LX[i + 1][1] // 2
            routes.append(Route('x', c, max(-D, xa), min(D - 1, xb), w, k))
    if rail:
        routes.append(rail)
    # mailles, découpées en îlots par des rues secondaires (qui s'arrêtent aux avenues) ou des impasses
    ilots = []

    def couper(x1, z1, x2, z2, prof=0):
        cx, cz = (x1 + x2) / 2, (z1 + z2) / 2
        q = quartier_de(cx, cz)
        cible, wr = GENRES[q['genre']]
        w, h = x2 - x1 + 1, z2 - z1 + 1
        # impasse à rond de virage (banlieue, beaux quartiers) : la rue entre et ne ressort pas
        if q['genre'] in ('banlieue', 'riche', 'pauvre') and prof <= 2 and w >= 64 and h >= 74 and rng.random() < 0.55:
            c = int(x1 + w * rng.uniform(0.4, 0.6))
            R = 7
            nord = rng.random() < 0.5
            L = int(h * rng.uniform(0.55, 0.68))
            if nord:
                zf = z1 + L
                ri = Route('z', c, z1 - 2, zf, 2 * R + 1, 'impasse')
                ri.bout = zf
                routes.append(ri)
                couper(x1, z1, c - R - 1, zf + R, prof + 2)
                couper(c + R + 1, z1, x2, zf + R, prof + 2)
                ilots.append({'x1': x1, 'z1': zf + R + 1, 'x2': x2, 'z2': z2, 'q': q['id']})
            else:
                zf = z2 - L
                ri = Route('z', c, zf, z2 + 2, 2 * R + 1, 'impasse')
                ri.bout = zf
                routes.append(ri)
                couper(x1, zf - R, c - R - 1, z2, prof + 2)
                couper(c + R + 1, zf - R, x2, z2, prof + 2)
                ilots.append({'x1': x1, 'z1': z1, 'x2': x2, 'z2': zf - R - 1, 'q': q['id']})
            return
        if prof < 6 and max(w, h) > cible * 1.45 and min(w, h) > 26:
            if w >= h:
                c = int(x1 + w * rng.uniform(0.38, 0.62))
                routes.append(Route('z', c, z1, z2, wr, 'rue' if wr == 7 else 'petite'))
                couper(x1, z1, c - wr // 2 - 1, z2, prof + 1)
                couper(c + wr // 2 + 1, z1, x2, z2, prof + 1)
            else:
                c = int(z1 + h * rng.uniform(0.38, 0.62))
                routes.append(Route('x', c, x1, x2, wr, 'rue' if wr == 7 else 'petite'))
                couper(x1, z1, x2, c - wr // 2 - 1, prof + 1)
                couper(x1, c + wr // 2 + 1, x2, z2, prof + 1)
            return
        ilots.append({'x1': x1, 'z1': z1, 'x2': x2, 'z2': z2, 'q': q['id']})

    def bornes(i0, i1, j):
        """Emprise d'une maille (colonnes i0..i1 de la rangée j) entre les tronçons qui l'entourent."""
        x1 = xpos(i0, j) + LX[i0][1] // 2 + 1
        x2 = xpos(i1 + 1, j) - LX[i1 + 1][1] // 2 - 1
        z1 = LZ[j][0] + LZ[j][1] // 2 + 1
        z2 = LZ[j + 1][0] - LZ[j + 1][1] // 2 - 1
        return x1, z1, x2, z2
    for j in range(nz):
        i = 0
        while i < nx:
            i1 = i + 1 if (i + 1, j) in fus else i
            x1, z1, x2, z2 = bornes(i, i1, j)
            if (i, j) in nature:
                # campagne : jusqu'au bord de la ville du côté extérieur
                if i == 0:
                    x1 = -D
                if i == nx - 1:
                    x2 = D - 1
                if j == 0:
                    z1 = -D
                if j == nz - 1:
                    z2 = D - 1
                q = quartier_de((x1 + x2) / 2, (z1 + z2) / 2)
                ilots.append({'x1': x1, 'z1': z1, 'x2': x2, 'z2': z2, 'q': q['id'], 'nature': True})
            elif x2 - x1 > 12 and z2 - z1 > 12:
                couper(x1, z1, x2, z2)
            i = i1 + 1
    # quartiers : leurs îlots bâtis, leur centre, leur emprise (pour la zone vivante de p97)
    quartiers = []
    for q in germes:
        mes = [b for b in ilots if b['q'] == q['id'] and not b.get('nature')]
        if not mes:
            continue
        q = dict(q)
        q['x1'] = min(b['x1'] for b in mes)
        q['z1'] = min(b['z1'] for b in mes)
        q['x2'] = max(b['x2'] for b in mes)
        q['z2'] = max(b['z2'] for b in mes)
        b0 = min(mes, key=lambda b: ((b['x1'] + b['x2']) / 2 - q['gx']) ** 2 + ((b['z1'] + b['z2']) / 2 - q['gz']) ** 2)
        q['cx'], q['cz'] = (b0['x1'] + b0['x2']) // 2, (b0['z1'] + b0['z2']) // 2
        quartiers.append(q)
    return {'S': S_, 'routes': routes, 'ilots': ilots, 'quartiers': quartiers, 'rail': rail, 'metro': ty['metro']}


# ============================================================================ chantier d'une ville entière
class ChantierCite(Chantier):
    def __init__(self, v, pv):
        self.site = {'id': v['id'], 'graine': v['graine']}
        self.rng = random.Random(v['graine'] + 1)
        S_ = pv['S']
        D = S_ // 2
        self.m = Monde(-D, Y0, -D, S_, HAUT, S_)
        self.ctx = Ctx(self.m, v['graine'])
        self.coffres = []
        self.lieux = []
        m = self.m
        m.fill(-D, Y0, -D, D - 1, 57, D - 1, S('stone'))
        m.fill(-D, 58, -D, D - 1, 62, D - 1, S('dirt'))
        m.fill(-D, 63, -D, D - 1, 63, D - 1, S('grass_block', snowy=False))
        self.R0 = Repere(self.ctx, 0, 0)
        self.x0, self.z0, self.x1, self.z1 = -D, -D, D - 1, D - 1


# ---------------------------------------------------------------------------- rues
def dessiner_rues(ch, pv):
    m, rng = ch.m, ch.rng
    # îlots : trottoir (bande de 2) autour, gazon dedans
    genre = {q['id']: q['genre'] for q in pv['quartiers']}
    for b in pv['ilots']:
        if b.get('nature'):
            continue
        m.fill(b['x1'], 63, b['z1'], b['x2'], 63, b['z2'], TROTTOIR)
        m.fill(b['x1'] + 2, 63, b['z1'] + 2, b['x2'] - 2, 63, b['z2'] - 2, S('grass_block', snowy=False))
        if genre.get(b['q']) in ('industriel', 'gare'):
            # cours d'usine : gravier, asphalte fissuré, quelques touffes
            for x in range(b['x1'] + 2, b['x2'] - 1):
                for z in range(b['z1'] + 2, b['z2'] - 1):
                    r = rng.random()
                    m.set(x, 63, z, S('gravel') if r < 0.45 else ASPH if r < 0.75 else S('coarse_dirt') if r < 0.9
                          else S('grass_block', snowy=False))
    rail = pv['rail']
    for r in pv['routes']:
        x1, z1, x2, z2 = r.rect()
        if r.k in ('rail', 'impasse'):
            continue
        m.fill(x1, 63, z1, x2, 63, z2, ASPH)
        m.vide(x1, 64, z1, x2, 80, z2)
    for r in pv['routes']:
        if r.k == 'impasse':
            impasse(ch, r)
    for r in pv['routes']:
        x1, z1, x2, z2 = r.rect()
        if r.k in ('rail', 'impasse'):
            continue
        h = r.w // 2
        for t in range(r.a, r.b + 1):
            if r.k == 'boulevard':
                # terre-plein central planté (3 de large), entrecoupé aux carrefours
                for e in (-1, 0, 1):
                    x, z = (t, r.c + e) if r.axe == 'x' else (r.c + e, t)
                    if m.get(x, 63, z) == ASPH:
                        m.set(x, 63, z, S('grass_block', snowy=False))
                if t % 12 == 0:
                    x, z = (t, r.c) if r.axe == 'x' else (r.c, t)
                    m.set(x, 64, z, S('oak_log', axis='y'))
                    m.set(x, 65, z, S('oak_leaves', persistent=True, distance=1, waterlogged=False))
            elif r.k in ('avenue',) and t % 6 < 4:
                for e in (-1, 1):
                    x, z = (t, r.c + e) if r.axe == 'x' else (r.c + e, t)
                    m.set(x, 63, z, S('yellow_concrete'))
            elif r.k in ('rue', 'ceinture') and t % 6 < 3:
                x, z = (t, r.c) if r.axe == 'x' else (r.c, t)
                m.set(x, 63, z, S('yellow_concrete'))
    # les rues qui se croisent ont été peintes l'une sur l'autre : on nettoie les carrefours
    for r in pv['routes']:
        for o in pv['routes']:
            if r.axe == o.axe or r.k == 'rail' or o.k == 'rail':
                continue
            if r.axe == 'x' and o.a <= r.c <= o.b and r.a <= o.c <= r.b:
                ax1, az1, ax2, az2 = r.rect()
                bx1, bz1, bx2, bz2 = o.rect()
                cx1, cz1, cx2, cz2 = max(ax1, bx1), max(az1, bz1), min(ax2, bx2), min(az2, bz2)
                if cx1 <= cx2 and cz1 <= cz2:
                    m.fill(cx1, 63, cz1, cx2, 63, cz2, ASPH)
                    m.vide(cx1, 64, cz1, cx2, 66, cz2)
                    # passages piétons
                    for k in range(cx1, cx2 + 1, 2):
                        for zz in (cz1 - 2, cz2 + 2):
                            if m.get(k, 63, zz) == ASPH:
                                m.set(k, 63, zz, S('white_concrete'))
    # voie ferrée : ballast, deux voies, passages à niveau
    if rail:
        x1, z1, x2, z2 = rail.rect()
        m.fill(x1, 63, z1, x2, 63, z2, S('gravel'))
        m.vide(x1, 64, z1, x2, 80, z2)
        for x in range(x1, x2 + 1):
            for z in (rail.c - 2, rail.c + 2):
                m.set(x, 64, z, S('rail', shape='east_west', waterlogged=False))
        for r in pv['routes']:
            if r.axe == 'z' and r.k != 'rail':
                a1, _, a2, _ = r.rect()
                m.fill(a1, 63, z1, a2, 63, z2, ASPH)
                for z in (z1 - 1, z2 + 1):
                    m.set(a1 - 1, 64, z, S('red_concrete'))
                    m.set(a1 - 1, 65, z, S('white_concrete'))
        # wagons abandonnés sur la voie
        for x in range(x1 + 20, x2 - 40, rng.randint(70, 110)):
            m.fill(x, 64, rail.c + 1, x + 16, 67, rail.c + 3, S(rng.choice(['brown_concrete', 'red_terracotta', 'gray_concrete'])))
            m.vide(x + 1, 65, rail.c + 2, x + 15, 66, rail.c + 2)
            ch.coffre(ch.R0, x + 8, 65, rail.c + 2, 'north', SI.LOOT_VILLE, baril=True)
    # rond-point au croisement des boulevards
    for dx in range(-15, 16):
        for dz in range(-15, 16):
            d = math.hypot(dx, dz)
            if d <= 15:
                m.set(dx, 63, dz, ASPH)
                m.vide(dx, 64, dz, dx, 70, dz)
            if d <= 7:
                m.set(dx, 63, dz, S('grass_block', snowy=False))
            if 7 < d <= 8:
                m.set(dx, 64, dz, S('stone_brick_wall', east='none', west='none', north='none', south='none', up=True,
                                    waterlogged=False))
    m.fill(-1, 64, -1, 1, 64, 1, S('chiseled_stone_bricks'))
    m.fill(0, 65, 0, 0, 69, 0, S('stone_bricks'))
    m.set(0, 70, 0, S('lantern', hanging=False, waterlogged=False))
    # lampadaires le long des îlots (tous éteints), bornes, feux aux grands carrefours
    for b in pv['ilots']:
        if b.get('nature'):
            continue
        for x in range(b['x1'] + 6, b['x2'] - 5, 18):
            RU.lampadaire(ch.R0, x, b['z1'], 'north')
            RU.lampadaire(ch.R0, x, b['z2'], 'south')
        for z in range(b['z1'] + 6, b['z2'] - 5, 18):
            RU.lampadaire(ch.R0, b['x1'], z, 'west')
            RU.lampadaire(ch.R0, b['x2'], z, 'east')
        if rng.random() < 0.3:
            RU.borne_fontaine(ch.R0, b['x1'] + 3, b['z1'])
        if rng.random() < 0.25:
            RU.poubelle(ch.R0, b['x2'] - 3, b['z2'])


def impasse(ch, r):
    """Impasse de banlieue : chaussée de 5 entre deux bandes de gazon plantées, rond de virage au bout (îlot central)."""
    m, rng = ch.m, ch.rng
    x1, z1, x2, z2 = r.rect()
    R = r.w // 2
    m.vide(x1, 64, z1, x2, 80, z2)
    m.fill(x1, 63, z1, x2, 63, z2, S('grass_block', snowy=False))
    m.fill(r.c - R, 63, z1, r.c - R, 63, z2, TROTTOIR)
    m.fill(r.c + R, 63, z1, r.c + R, 63, z2, TROTTOIR)
    m.fill(r.c - 2, 63, z1, r.c + 2, 63, z2, ASPH)
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            d = math.hypot(dx, dz)
            if d <= R + 0.4:
                m.set(r.c + dx, 63, r.bout + dz, ASPH)
                m.vide(r.c + dx, 64, r.bout + dz, r.c + dx, 70, r.bout + dz)
            if d <= 2.2:
                m.set(r.c + dx, 63, r.bout + dz, S('grass_block', snowy=False))
    m.set(r.c, 64, r.bout, S('oak_log', axis='y'))
    m.fill(r.c - 1, 65, r.bout - 1, r.c + 1, 66, r.bout + 1, S('oak_leaves', persistent=True, distance=1, waterlogged=False))
    m.set(r.c, 65, r.bout, S('oak_log', axis='y'))
    # arbres le long des bandes de gazon (hors rond)
    for t in range(min(z1, z2) + 3, max(z1, z2) - 2, 9):
        if abs(t - r.bout) > R + 1:
            for x in (r.c - R + 2, r.c + R - 2):
                if rng.random() < 0.7:
                    m.set(x, 64, t, S('birch_log', axis='y'))
                    m.set(x, 65, t, S('birch_log', axis='y'))
                    m.fill(x - 1, 66, t - 1, x + 1, 67, t + 1, S('birch_leaves', persistent=True, distance=1,
                                                                  waterlogged=False))
    ch.panneau(r.c + 3, 64, z1 + 2 if r.bout > z1 + 10 else z2 - 2, ['Cul-de-sac', '', '', ''], mur='east')


def campagne(ch, b):
    """Coin de ville resté en campagne : champ en rangs, ou boisé, avec sa clôture et parfois une grange."""
    m, rng = ch.m, ch.rng
    x1, z1, x2, z2 = b['x1'], b['z1'], b['x2'], b['z2']
    if rng.random() < 0.55:
        for x in range(x1 + 2, x2 - 1):
            for z in range(z1 + 2, z2 - 1):
                if (x - x1) % 5 == 0:
                    m.set(x, 63, z, S('water'))
                else:
                    m.set(x, 63, z, S('farmland', moisture=7))
                    if rng.random() < 0.8:
                        m.set(x, 64, z, S(rng.choice(['wheat', 'wheat', 'carrots', 'potatoes']), age=rng.randint(4, 7)))
        for x in range(x1 + 1, x2):
            m.set(x, 64, z1 + 1, S('oak_fence', waterlogged=False))
            m.set(x, 64, z2 - 1, S('oak_fence', waterlogged=False))
        for z in range(z1 + 1, z2):
            m.set(x1 + 1, 64, z, S('oak_fence', waterlogged=False))
            m.set(x2 - 1, 64, z, S('oak_fence', waterlogged=False))
        for _ in range(max(2, (x2 - x1) * (z2 - z1) // 900)):
            x, z = rng.randint(x1 + 4, x2 - 4), rng.randint(z1 + 4, z2 - 4)
            m.set(x, 64, z, S('hay_block', axis='y'))
    else:
        for _ in range((x2 - x1) * (z2 - z1) // 40):
            x, z = rng.randint(x1 + 2, x2 - 2), rng.randint(z1 + 2, z2 - 2)
            if not m.est_air(x, 64, z):
                continue
            bois = rng.choice(['spruce', 'spruce', 'birch', 'oak'])
            h = rng.randint(4, 7)
            m.fill(x - 2, 62 + h, z - 2, x + 2, 63 + h, z + 2, S(bois + '_leaves', persistent=True, distance=1,
                                                                    waterlogged=False))
            m.fill(x - 1, 64 + h, z - 1, x + 1, 64 + h, z + 1, S(bois + '_leaves', persistent=True, distance=1,
                                                                    waterlogged=False))
            m.fill(x, 64, z, x, 63 + h, z, S(bois + '_log', axis='y'))
        for _ in range((x2 - x1) * (z2 - z1) // 60):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            if m.est_air(x, 64, z):
                m.set(x, 64, z, S(rng.choice(['fern', 'grass'])))


# ---------------------------------------------------------------------------- métro (métropole)
def metro(ch, pv, quartiers):
    """Ligne 1 sous le boulevard est-ouest ; stations dans les quartiers centraux, bouches sur le terre-plein."""
    m = ch.m
    D = pv['S'] // 2
    m.vide(-D + 20, 49, -3, D - 21, 55, 3)
    m.fill(-D + 20, 48, -4, D - 21, 48, 4, S('gravel'))
    m.fill(-D + 20, 56, -4, D - 21, 56, 4, S('stone_bricks'))
    for x in range(-D + 20, D - 20):
        m.set(x, 49, -2, S('rail', shape='east_west', waterlogged=False))
        m.set(x, 49, 2, S('rail', shape='east_west', waterlogged=False))
    stations = []
    for q in quartiers:
        if q['genre'] in ('centre', 'affaires', 'civique') and abs(q['cz']) < D * 0.6:
            x = max(-D + 60, min(D - 60, int(q['cx'])))
            if all(abs(x - s) > 70 for s in stations) and abs(x) > 24:
                stations.append(x)
    for k, x in enumerate(stations):
        # quais
        m.vide(x - 20, 49, -7, x + 20, 55, 7)
        m.fill(x - 20, 48, -7, x + 20, 49, -4, S('polished_andesite'))
        m.fill(x - 20, 48, 4, x + 20, 49, 7, S('polished_andesite'))
        m.fill(x - 20, 49, -4, x + 20, 49, -4, S('yellow_concrete'))
        m.fill(x - 20, 49, 4, x + 20, 49, 4, S('yellow_concrete'))
        for xx in range(x - 16, x + 17, 8):
            ch.ctx.lampe(xx, 55, -6, S('sea_lantern'), S('light_gray_concrete'))
            ch.ctx.lampe(xx, 55, 6, S('sea_lantern'), S('light_gray_concrete'))
        # escalier : du terre-plein du boulevard jusqu'au quai nord
        for i in range(13):
            m.vide(x - 6 + i, 50 + i, -1, x - 6 + i, 56 + i, 1)
            m.fill(x - 6 + i, 50 + i - 1, -1, x - 6 + i, 50 + i - 1, 1, S('stone_brick_slab', type='top'))
        m.vide(x - 6, 50, -3, x - 4, 54, 3)
        # édicule vitré sur le terre-plein
        m.fill(x - 7, 64, -2, x + 8, 66, -2, S('glass_pane'))
        m.fill(x - 7, 64, 2, x + 8, 66, 2, S('glass_pane'))
        m.fill(x - 7, 67, -2, x + 8, 67, 2, S('green_concrete'))
        m.fill(x + 7, 64, -1, x + 7, 66, 1, S('glass_pane'))
        ch.panneau(x + 8, 65, 0, ['MÉTRO', 'Ligne 1', '', ''], mur='east')
        # rame arrêtée
        if k % 2 == 0:
            m.fill(x - 14, 50, -3, x + 14, 53, -1, S('white_concrete'))
            m.vide(x - 13, 50, -2, x + 13, 52, -2)
            m.fill(x - 14, 52, -3, x + 14, 52, -3, S('blue_concrete'))
        ch.coffre(ch.R0, x + 18, 49, 6, 'west', SI.LOOT_VILLE)
        ch.lieux.append(('metro', 'Station de métro %d' % (k + 1), x, 0, 22, 9))


# ============================================================================ bâtiments supplémentaires (types de la ville)
def maison_riche(ch, R, L, P):
    BA.maison(ch, R, L, P, etages=2, mur=ch.rng.choice(['white_terracotta', 'stone_bricks', 'light_gray_concrete', 'bricks']),
              toit='dark_oak')
    # piscine creusée dans la cour arrière, haie
    R.fill(2, 62, -9, L - 3, 63, -4, S('white_concrete'))
    R.fill(3, 63, -8, L - 4, 63, -5, S('water', level=0))
    for a in range(-1, L + 1):
        R.set(a, 64, -11, S('oak_leaves', persistent=True, distance=1, waterlogged=False))
    x, z = R.xz(L + 3, P - 3)
    try:
        RU.voiture(ch.R0, x, z, R.d('south'), ch.rng.choice(['black', 'white', 'gray']), 64, 'auto')
    except Exception:
        pass


def duplex(ch, R, L, P):
    BA.maison(ch, R, L, P, etages=2, mur=ch.rng.choice(['bricks', 'red_terracotta', 'brown_terracotta']), toit='spruce')
    # escalier extérieur en colimaçon vers le logement du haut
    for k in range(4):
        R.set(L - 2, 64 + k, P + (k % 2), R.S('spruce_stairs', facing='west', half='bottom'))
    R.fill(L - 3, 68, P, L - 1, 68, P + 1, S('spruce_planks'))
    R.fill(L - 3, 69, P + 1, L - 1, 69, P + 1, S('iron_bars'))
    ZM.porte(R, L - 2, 68, P - 1, 'north', 'spruce')


def petite_maison(ch, R, L, P):
    rng = ch.rng
    mur = S(rng.choice(['stripped_spruce_log', 'oak_planks', 'cracked_stone_bricks', 'mud_bricks']))
    R.fill(0, 63, 0, L - 1, 63, P - 1, S('oak_planks'))
    R.fill(0, 64, 0, L - 1, 66, P - 1, mur)
    R.vide(1, 64, 1, L - 2, 66, P - 2)
    R.fill(0, 67, 0, L - 1, 67, P - 1, S('iron_trapdoor', facing='north', half='bottom', open=False, powered=False,
                                         waterlogged=False))
    R.set(2, 65, P - 1, S('glass_pane'))
    ZM.porte(R, L // 2, 64, P - 1, 'north', 'oak')
    ZM.lit(R, 1, 64, 1, 'north', 'brown')
    ch.coffre(R, L - 2, 64, 1, 'south', SI.LOOT_MAISON, baril=True)
    for _ in range(3):
        R.set(rng.randint(0, L - 1), 64, P + rng.randint(1, 2), R.S('barrel', facing='up', open=False))


def restaurant(ch, R, L, P):
    nom = ch.rng.choice(['Casse-croûte Chez Ti-Jean', 'Restaurant Le Boréal', 'Pizzéria Laurentienne',
                         'Rôtisserie du Coin', 'Patate Chez Mado'])
    BA.commerce(ch, R, L, P, nom.split()[0])
    for a in range(1, L - 1, 3):
        ZM.table(R, a, 64, P + 1, 'spruce')
    ch.lieu(R, L, P, 'depanneur', nom)


def cinema(ch, R, L, P):
    BA.commerce(ch, R, L, P, 'Cinéma')
    R.fill(-1, 68, P, L, 69, P + 1, S('red_concrete'))
    x, z = R.xz(L // 2, P + 2)
    ch.panneau(x, 68, z, ['CINÉMA ROYAL', 'Ce soir :', 'FERMÉ', 'jusqu\'à nouvel ordre'], mur=R.d('south'))
    ch.lieu(R, L, P, 'cinema', 'Cinéma Royal')


def supermarche(ch, R, L, P):
    BA.commerce(ch, R, L, P, 'Supermarché')
    for b in range(3, P - 5, 3):
        R.fill(3, 64, b, L - 4, 65, b, R.S('barrel', facing='up', open=False))
    ch.lieu(R, L, P, 'grand_magasin', 'Supermarché')


def poste_electrique(ch, B):
    x1, z1, x2, z2 = B
    m = ch.m
    for x in range(x1 + 2, x2 - 1):
        for z in (z1 + 2, z2 - 2):
            m.fill(x, 64, z, x, 66, z, S('iron_bars', waterlogged=False))
    for z in range(z1 + 2, z2 - 1):
        for x in (x1 + 2, x2 - 2):
            m.fill(x, 64, z, x, 66, z, S('iron_bars', waterlogged=False))
    m.fill(x1 + 3, 63, z1 + 3, x2 - 3, 63, z2 - 3, S('gravel'))
    for x in range(x1 + 6, x2 - 6, 8):
        for z in range(z1 + 6, z2 - 6, 8):
            m.fill(x, 64, z, x + 2, 67, z + 2, S('iron_block'))
            m.set(x + 1, 68, z + 1, S('lightning_rod', facing='up', powered=False, waterlogged=False))
            m.fill(x + 1, 69, z + 1, x + 1, 72, z + 1, S('chain', axis='y', waterlogged=False))
    ch.panneau((x1 + x2) // 2, 64, z2 - 1, ['DANGER', 'Haute tension', 'Hydro', ''], rotation=0)
    ch.lieux.append(('poste_electrique', 'Poste électrique', (x1 + x2) // 2, (z1 + z2) // 2, (x2 - x1) // 2, (z2 - z1) // 2))


def gare(ch, B, nom):
    x1, z1, x2, z2 = B
    L, P = min(60, x2 - x1 - 10), min(24, z2 - z1 - 6)
    R = lot(ch, B, 'south', (x1 + x2) // 2 - L // 2, L, P)
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 72, P - 1, S('bricks'))
    R.vide(1, 64, 1, L - 2, 71, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('polished_andesite'))
    R.fill(0, 73, 0, L - 1, 73, P - 1, S('deepslate_tile_slab', type='bottom'))
    for a in range(3, L - 3, 4):
        R.fill(a, 66, P - 1, a + 1, 70, P - 1, S('glass_pane'))
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'dark_oak')
    R.fill(L // 2 - 1, 74, P // 2, L // 2 + 1, 80, P // 2 + 2, S('bricks'))
    ZM.horloge(R, L // 2, 78, P // 2 + 3, 'south') if hasattr(ZM, 'horloge') else None
    for b in range(4, P - 4, 4):
        ZM.canape(R, 3, 64, b, 'east', 3, 'spruce', 'spruce')
    ch.coffre(R, L - 3, 64, 2, 'west', SI.LOOT_VILLE)
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 71, z, ['GARE', nom[:15], nom[15:30], 'VIA Laurentides'], mur=R.d('south'))
    ch.lieu(R, L, P, 'gare', 'Gare de ' + nom)


def depot_bus(ch, B):
    x1, z1, x2, z2 = B
    L, P = min(48, x2 - x1 - 6), min(30, z2 - z1 - 6)
    R = lot(ch, B, 'north', x1 + 3, L, P)
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 71, P - 1, S('light_gray_concrete'))
    R.vide(1, 64, 1, L - 2, 71, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('gray_concrete'))
    for a in range(2, L - 8, 10):
        R.vide(a, 64, P - 1, a + 6, 69, P - 1)
    for k, a in enumerate(range(6, L - 10, 10)):
        x, z = R.xz(a, P // 2)
        try:
            RU.autobus_scolaire_blocs(ch.R0, x, z, 64, porte_ouverte=k % 2 == 0)
        except Exception:
            pass
    ch.lieu(R, L, P, 'garage', 'Dépôt d\'autobus')


def piscine(ch, B):
    x1, z1, x2, z2 = B
    m = ch.m
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    m.fill(cx - 14, 63, cz - 9, cx + 14, 63, cz + 9, S('smooth_stone'))
    m.fill(cx - 12, 59, cz - 7, cx + 12, 62, cz + 7, S('light_blue_concrete'))
    m.fill(cx - 11, 60, cz - 6, cx + 11, 63, cz + 6, S('water', level=0))
    for x in range(cx - 14, cx + 15):
        for z in (cz - 10, cz + 10):
            m.fill(x, 64, z, x, 65, z, S('iron_bars', waterlogged=False))
    m.fill(cx + 13, 64, cz - 2, cx + 13, 68, cz - 2, S('white_concrete'))
    m.fill(cx + 12, 68, cz - 2, cx + 13, 68, cz - 2, S('white_concrete'))
    ch.lieux.append(('parc', 'Piscine municipale', cx, cz, 16, 12))


def stade(ch, B, nom):
    x1, z1, x2, z2 = B
    m = ch.m
    m.fill(x1 + 8, 63, z1 + 8, x2 - 8, 63, z2 - 8, S('green_concrete'))
    for k in range(4):
        m.fill(x1 + 4 - k, 64 + k, z1 + 4 - k, x2 - 4 + k, 64 + k, z1 + 5 - k, S('light_gray_concrete'))
        m.fill(x1 + 4 - k, 64 + k, z2 - 5 + k, x2 - 4 + k, 64 + k, z2 - 4 + k, S('light_gray_concrete'))
    for x in range(x1 + 10, x2 - 9, 2):
        m.set(x, 64, (z1 + z2) // 2, S('white_carpet'))
    for z in (z1 + 10, z2 - 10):
        m.fill((x1 + x2) // 2 - 3, 64, z, (x1 + x2) // 2 + 3, 66, z, S('iron_bars', waterlogged=False))
    for (x, z) in ((x1 + 3, z1 + 3), (x2 - 3, z1 + 3), (x1 + 3, z2 - 3), (x2 - 3, z2 - 3)):
        m.fill(x, 64, z, x, 78, z, S('gray_concrete'))
        ch.ctx.lampe(x, 79, z, S('sea_lantern'), S('light_gray_concrete'))
    ch.lieux.append(('arena', 'Stade ' + nom, (x1 + x2) // 2, (z1 + z2) // 2, (x2 - x1) // 2, (z2 - z1) // 2))


# ============================================================================ recettes d'îlots (le rythme d'un quartier)
def recettes(ch, b, q, uniques, v):
    """Choisit et pose la recette d'un îlot. b : îlot ; q : quartier ; uniques : bâtiments déjà posés dans la ville."""
    rng = ch.rng
    if b.get('nature'):
        campagne(ch, b)
        return
    B = (b['x1'] + 2, b['z1'] + 2, b['x2'] - 2, b['z2'] - 2)
    W, H = B[2] - B[0] + 1, B[3] - B[1] + 1
    g = q['genre']
    petit = min(W, H)
    commerces = ['Pharmacie', 'Café', 'Nettoyeur', 'Quincaillerie', 'Librairie', 'Fleuriste', 'Bar', 'Boulangerie', None]

    def immeubles(etmin, etmax, com=0.4):
        return lambda: (rng.choice((12, 14, 16)), lambda c, R, L, P: VB.immeuble(
            c, R, L, P, etages=rng.randint(etmin, etmax), commerce=rng.choice(commerces) if rng.random() < com else None))

    def maisons(fn=None, larg=(9, 10, 11)):
        def poser(c, R, L, P):
            (fn or BA.maison)(c, R, L, P) if fn else BA.maison(c, R, L, P, etages=2 if rng.random() < 0.3 else 1)
            for a in range(-1, L + 1):
                R.set(a, 64, P + 1, S('spruce_fence', waterlogged=False))
            R.set(L // 2, 64, P + 1, AIR)
        return lambda: (rng.choice(larg), poser)

    def unique(nom):
        if nom in uniques:
            return False
        uniques.add(nom)
        return True

    def cour_(P, genre):
        VB.cour(ch, B, P, genre)

    # ---- grands équipements (une fois par ville, sur un îlot assez grand)
    if g == 'civique' and petit >= 80 and unique('hopital'):
        VB.hopital(ch, B)
        return
    if g in ('centre', 'civique') and petit >= 60 and unique('mairie'):
        VB.hotel_de_ville(ch, lot(ch, B, 'south', B[0] + (W - 30) // 2, 30, 22), 30, 22)
        VB.place(ch, (B[0], B[1], B[2], B[3] - 26), v['nom'])
        return
    if g == 'gare' and petit >= 40 and unique('gare'):
        gare(ch, B, v['nom'])
        return
    if g in ('commercial', 'centre') and petit >= 64 and unique('magasin'):
        R = ch.rep(B[0] + 4, B[1] + 4, 'south')
        BA.commerce(ch, R, min(60, W - 8), min(40, H - 16), 'MAGASIN À RAYONS')
        ch.lieu(R, min(60, W - 8), min(40, H - 16), 'grand_magasin', 'Magasin à rayons ' + v['nom'])
        return
    if g in ('civique', 'centre', 'affaires') and petit >= 56 and unique('parking'):
        VB.parking_etage(ch, B)
        return
    if g in ('residentiel', 'banlieue', 'pauvre') and petit >= 50 and unique('ecole_' + q['id']):
        BA.ecole(ch, lot(ch, B, 'north', B[0] + 4, 25, 20), 25, 20, q['nom'])
        m = ch.m
        m.fill(B[0] + 4, 63, B[1] + 26, B[2] - 4, 63, B[3] - 4, S('green_concrete'))
        perimetre(ch, B, 10, maisons(), cotes=('south',))
        return
    if g in ('banlieue', 'residentiel', 'riche') and petit >= 60 and unique('eglise_' + q['id']):
        BA.eglise(ch, lot(ch, B, 'north', B[0] + W // 2 - 7, 15, 25), 15, 25)
        ch.lieu(lot(ch, B, 'north', B[0] + W // 2 - 7, 15, 25), 15, 25, 'eglise', 'Église de ' + q['nom'])
        perimetre(ch, B, 10, maisons(), cotes=('south', 'west', 'east'))
        return
    if g in ('banlieue', 'residentiel') and petit >= 56 and unique('stade_' + v['id']):
        stade(ch, B, q['nom'])
        return
    if g == 'banlieue' and petit >= 44 and unique('piscine_' + v['id']):
        piscine(ch, B)
        perimetre(ch, B, 10, maisons(), cotes=('north', 'south'))
        return
    if g == 'industriel' and petit >= 40 and unique('poste_' + v['id']):
        poste_electrique(ch, B)
        return
    if g in ('gare', 'industriel') and petit >= 40 and unique('bus_' + v['id']):
        depot_bus(ch, B)
        return
    # ---- recettes courantes
    r = rng.random()
    if g in ('centre', 'affaires'):
        if g == 'affaires' or r < 0.45:
            tours = lambda: (rng.choice((18, 20)), lambda c, R, L, P: VB.tour(c, R, L, P))
            perimetre(ch, B, min(22, petit // 3), tours if petit >= 50 else immeubles(4, 8))
            cour_(min(22, petit // 3), 'centre')
        elif r < 0.6 and petit >= 40:
            VB.place(ch, B, rng.choice(['Champlain', 'Cartier', 'du Marché', 'de la Gare', "d'Youville"]))
        else:
            if W > 40 and H > 40:
                VB.banque(ch, lot(ch, B, 'north', B[0] + 2, 20, 18), 20, 18) if unique('banque_' + q['id']) else None
            perimetre(ch, B, 16, immeubles(4, 8, 0.8))
            ruelle(ch, B)
            cour_(16, 'centre')
    elif g == 'commercial':
        if r < 0.3 and petit >= 40:
            supermarche(ch, ch.rep(B[0] + 4, B[1] + 4, 'south'), min(44, W - 8), min(30, H - 14), )
            VB.cour(ch, B, 0, 'commercial')
        elif r < 0.5:
            mix = lambda: rng.choice([(14, lambda c, R, L, P: restaurant(c, R, L, P)),
                                      (16, lambda c, R, L, P: BA.commerce(c, R, L, P, rng.choice(
                                          ['Épicerie', 'Vêtements', 'Électronique', 'Sports', 'Meubles']))),
                                      (18, lambda c, R, L, P: cinema(c, R, L, P) if unique('cinema') else BA.commerce(
                                          c, R, L, P, 'Animalerie'))])
            perimetre(ch, B, 14, mix)
            cour_(14, 'commercial')
        else:
            perimetre(ch, B, 14, lambda: (rng.choice((12, 14, 16)), lambda c, R, L, P: BA.commerce(
                c, R, L, P, rng.choice(['Dépanneur', 'Quincaillerie', 'Pharmacie', 'Vêtements', 'Nettoyeur', 'Sports']))))
            ruelle(ch, B)
            cour_(14, 'commercial')
    elif g == 'civique':
        if r < 0.5 and unique('police'):
            VB.commissariat(ch, lot(ch, B, 'south', B[0] + 2, 26, 18), 26, 18)
            BA.caserne(ch, lot(ch, B, 'north', B[0] + 4, 15, 13), 15, 13, v['nom'])
        perimetre(ch, B, 16, immeubles(3, 6, 0.2), cotes=('west', 'east'))
        cour_(16, 'civique')
    elif g == 'residentiel':
        if r < 0.5:
            perimetre(ch, B, 14, immeubles(3, 6, 0.3))
            cour_(14, 'residentiel')
        elif r < 0.8:
            perimetre(ch, B, 11, lambda: (rng.choice((10, 11)), lambda c, R, L, P: duplex(c, R, L, P)))
            cour_(11, 'banlieue')
        else:
            VB.parc(ch, B, rng.choice(['Jeanne-Mance', 'des Pionniers', 'du Souvenir', 'Laval', 'Molson'])) if petit >= 50 \
                else perimetre(ch, B, 14, immeubles(3, 5))
    elif g == 'banlieue':
        if r < 0.12 and petit >= 50:
            VB.parc(ch, B, rng.choice(['des Pionniers', 'du Souvenir', 'des Lilas', 'du Ruisseau']))
        else:
            perimetre(ch, B, 10, maisons() if r < 0.8 else lambda: (10, lambda c, R, L, P: duplex(c, R, L, P)))
            cour_(10, 'banlieue')
    elif g == 'riche':
        perimetre(ch, B, 13, lambda: (rng.choice((14, 15)), lambda c, R, L, P: maison_riche(c, R, L, P)))
        cour_(13, 'banlieue')
    elif g == 'pauvre':
        if r < 0.45:
            perimetre(ch, B, 8, lambda: (rng.choice((7, 8)), lambda c, R, L, P: petite_maison(c, R, L, P)))
            cour_(8, 'banlieue')
        else:
            perimetre(ch, B, 14, immeubles(2, 4, 0.2))
            cour_(14, 'residentiel')
    elif g in ('industriel', 'gare'):
        if r < 0.3 and petit >= 70 and len([u for u in uniques if u.startswith('usine')]) < 2:
            uniques.add('usine%d' % len(uniques))
            VB.usine(ch, B)
        elif r < 0.45 and petit >= 64:
            VB.citernes(ch, B)
            VB.grue(ch, B[2] - 14, B[3] - 12)
        elif r < 0.75:
            k = 0
            for s in range(B[0] + 4, B[2] - 40, 50):
                VB.entrepot(ch, ch.rep(s, B[1] + 4, 'south'), 44, min(36, H - 14))
                k += 1
            VB.conteneurs(ch, (B[0], B[1] + min(36, H - 14) + 8, B[2], B[3]), max(3, W * H // 600))
        else:
            perimetre(ch, B, 12, lambda: (12, lambda c, R, L, P: BA.garage(c, R, L, P, 'ATELIER')))
            VB.conteneurs(ch, (B[0] + 14, B[1] + 14, B[2] - 14, B[3] - 14), max(2, W * H // 900))
    elif g == 'parc':
        VB.parc(ch, B, rng.choice(['régional', 'des Prés', 'de la Source']))


def ruelle(ch, B):
    """Ruelle (3 de large) au milieu de l'îlot, derrière les rangées : bennes, cordes à linge, poubelles."""
    x1, z1, x2, z2 = B
    if z2 - z1 < 46:
        return
    m, rng = ch.m, ch.rng
    zc = (z1 + z2) // 2
    m.fill(x1 + 18, 63, zc - 1, x2 - 18, 63, zc + 1, ASPH)
    for x in range(x1 + 22, x2 - 22, rng.randint(9, 14)):
        if m.est_air(x, 64, zc - 1):
            m.fill(x, 64, zc - 1, x + 1, 65, zc - 1, S('green_concrete'))
        if rng.random() < 0.5 and m.est_air(x + 3, 64, zc + 1):
            m.set(x + 3, 64, zc + 1, S('barrel', facing='up', open=False))


# ============================================================================ l'apocalypse : un sort par quartier
SORTS = {'abandon': 0.6, 'envahie': 0.85, 'evacuee': 0.5, 'pillee': 0.65, 'brulee': 0.9, 'quarantaine': 0.4,
         'faction': 0.2, 'guerre': 0.8}


def carte_quartiers(pv):
    """Pour chaque colonne (x, z) : l'index du quartier (îlot le plus proche pour les rues)."""
    S_ = pv['S']
    D = S_ // 2
    qs = pv['quartiers']
    xs = np.arange(-D, D)
    X, Z = np.meshgrid(xs, xs)   # [z][x]
    best = np.full(X.shape, 1e18)
    idx = np.zeros(X.shape, np.int16)
    for i, q in enumerate(qs):
        d = (X - q['gx']) ** 2 + (Z - q['gz']) ** 2
        m = d < best
        best = np.where(m, d, best)
        idx = np.where(m, i, idx)
    return idx


def apocalypse(ch, pv, v):
    """Le sort de chaque quartier, appliqué couche par couche (pas de tableau aléatoire géant)."""
    m, rng = ch.m, ch.rng
    qs = pv['quartiers']
    carte = carte_quartiers(pv)
    sort_col = np.array([list(SORTS).index(q['sort']) for q in qs], np.int8)[carte]   # [z][x]
    force = np.array([SORTS[q['sort']] for q in qs])[carte]
    reprise = np.array([{'abandon': 0.18, 'envahie': 0.12, 'evacuee': 0.08, 'pillee': 0.06, 'brulee': 0.03,
                         'quarantaine': 0.03, 'faction': 0.0, 'guerre': 0.05}[q['sort']] for q in qs])[carte]
    rs = np.random.default_rng(v['graine'])
    ks = list(SORTS)
    brule = sort_col == ks.index('brulee')
    guerre = sort_col == ks.index('guerre')
    pal = lambda: m.pal
    # identifiants utiles
    i_asph = m.id(ASPH)
    i_trot = m.id(TROTTOIR)
    mousse, gazon, terre, herbe = m.id(S('moss_block')), m.id(S('grass_block', snowy=False)), m.id(S('coarse_dirt')), m.id(S('grass'))
    toile = m.id(S('cobweb'))
    noirs = [m.id(S('blackstone')), m.id(S('coal_block')), m.id(S('black_concrete')), m.id(S('basalt', axis='y'))]
    lierres = {}
    for face in ('east', 'west', 'south', 'north'):
        props = {k: 'false' for k in ('east', 'north', 'south', 'up', 'west')}
        props[face] = 'true'
        lierres[face] = m.id(S('vine', **props))
    P = m.pal
    verre = np.array(['glass' in p for p in P] + [False] * 64, bool)
    bois = np.array([any(k in p for k in ('planks', 'terracotta', 'concrete', 'bricks', 'wool', 'log', 'quartz'))
                     and 'gray_concrete' not in p and 'yellow_concrete' not in p for p in P] + [False] * 64, bool)
    feuilles = np.array(['leaves' in p for p in P] + [False] * 64, bool)
    solide = np.array([p != AIR and not any(k in p for k in ('glass', 'pane', 'door', 'sign', 'leaves', 'grass', 'flower',
                                                            'fence', 'wall', 'stairs', 'slab', 'carpet', 'rail', 'torch',
                                                            'lantern', 'bed', 'water', 'button', 'trapdoor', 'vine',
                                                            'bars', 'banner', 'chain', 'ladder')) for p in P] + [False] * 64, bool)
    yl = 63 - m.y0
    H = m.a.shape[0]
    for y in range(H):
        a = m.a[y]
        al = rs.random(a.shape, dtype=np.float32)
        if y == yl:
            sol = (a == i_asph) | (a == i_trot)
            a[sol & (al < reprise * 0.4)] = mousse
            a[sol & (al >= reprise * 0.4) & (al < reprise * 0.7)] = gazon
            a[sol & (al >= reprise * 0.7) & (al < reprise)] = terre
            g = a == gazon
            a[g & brule & (al > 0.4)] = terre
            continue
        if y < yl:
            continue
        v_ = verre[a]
        a[v_ & (al < 0.45 * force)] = 0
        a[v_ & brule & (al < 0.85)] = 0
        a[v_ & (al > 1 - 0.05 * force)] = toile
        b_ = bois[a] & (brule | (guerre & (al < 0.25))) & (al < 0.45)
        if b_.any():
            k = rs.integers(0, 4, a.shape)
            for i, nid in enumerate(noirs):
                a[b_ & (k == i)] = nid
        a[feuilles[a] & brule & (al < 0.85)] = 0
        # lierre sur les murs (selon l'abandon) et herbes folles au pied
        if y > yl + 1:
            src = solide[a]
            air = a == 0
            for (dx, dz, face) in ((1, 0, 'east'), (-1, 0, 'west'), (0, 1, 'south'), (0, -1, 'north')):
                vois = np.zeros(a.shape, bool)
                if dx > 0:
                    vois[:, :-1] = src[:, 1:]
                elif dx < 0:
                    vois[:, 1:] = src[:, :-1]
                elif dz > 0:
                    vois[:-1, :] = src[1:, :]
                else:
                    vois[1:, :] = src[:-1, :]
                c = air & vois & (al < 0.035 * force) & ~brule
                a[c] = lierres[face]
                air = a == 0
        if y == yl + 1:
            dessous = m.a[yl]
            g = (np.isin(dessous, [gazon, mousse])) & (a == 0)
            a[g & (al < 0.35 * force + 0.1)] = herbe
    # détails de chaque sort
    for q in qs:
        detail_sort(ch, q)


def _dans(q, x, z):
    return q['x1'] <= x <= q['x2'] and q['z1'] <= z <= q['z2']


def detail_sort(ch, q):
    m, rng = ch.m, ch.rng
    s = q['sort']
    x1, z1, x2, z2 = q['x1'], q['z1'], q['x2'], q['z2']
    n = max(1, (x2 - x1) * (z2 - z1) // 4000)

    def libre(x, z, y=64):
        return m.est_air(x, y, z) and not m.est_air(x, y - 1, z)
    if s in ('brulee', 'guerre'):
        for _ in range(n * 2):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            if libre(x, z):
                m.set(x, 64, z, S('campfire', facing='north', lit=False, signal_fire=False, waterlogged=False))
    if s == 'guerre':
        # cratères d'obus, lignes de sacs de sable, barbelés, épaves brûlées
        for _ in range(n * 3):
            cx, cz, r = rng.randint(x1, x2), rng.randint(z1, z2), rng.randint(2, 4)
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if dx * dx + dz * dz <= r * r:
                        for y in range(63 - (r - int(math.hypot(dx, dz))) // 2, 67):
                            if m.dedans(cx + dx, y, cz + dz):
                                m.set(cx + dx, y, cz + dz, AIR if y >= 63 else S('coarse_dirt'))
        for _ in range(n * 3):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            sens = rng.choice(((1, 0), (0, 1)))
            for k in range(rng.randint(5, 12)):
                xx, zz = x + sens[0] * k, z + sens[1] * k
                if m.dedans(xx, 64, zz) and libre(xx, zz):
                    m.set(xx, 64, zz, S('mud_bricks'))
                    if m.est_air(xx, 65, zz):
                        m.set(xx, 65, zz, S('mud_brick_slab', type='bottom', waterlogged=False))
        for _ in range(n * 6):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            if libre(x, z):
                m.set(x, 64, z, S('cobweb'))
        for _ in range(n * 2):
            x, z = rng.randint(x1 + 4, x2 - 4), rng.randint(z1 + 4, z2 - 4)
            if libre(x, z):
                try:
                    RU.voiture(ch.R0, x, z, rng.choice(['north', 'east']), 'black', 64, 'brulee')
                except Exception:
                    pass
    elif s == 'envahie':
        for _ in range(n * 30):
            x, z, y = rng.randint(x1, x2), rng.randint(z1, z2), rng.choice((64, 64, 64, 68, 72))
            if m.dedans(x, y, z) and m.est_air(x, y, z) and not m.est_air(x, y - 1, z):
                m.set(x, y, z, rng.choice([S('cobweb'), S('bone_block', axis='y'), S('red_carpet'), S('cobweb')]))
    elif s == 'evacuee':
        for _ in range(n * 10):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            if libre(x, z) and m.get(x, 63, z) == ASPH:
                try:
                    RU.voiture(ch.R0, x, z, rng.choice(['east', 'west', 'north', 'south']), rng.choice(COULEURS_AUTO), 64,
                               rng.choice(['auto', 'auto', 'taxi']), portes=rng.random() < 0.6)
                except Exception:
                    pass
        for _ in range(n):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            if libre(x, z):
                ch.panneau(x, 64, z, ['ÉVACUATION', 'Suivez les', 'flèches →', 'Ordre no 7'], rotation=rng.randint(0, 15))
        for _ in range(n * 6):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            if libre(x, z):
                m.set(x, 64, z, S('barrel', facing='up', open=True))
    elif s == 'faction':
        for _ in range(n * 3):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            if libre(x, z):
                m.set(x, 64, z, S('green_banner', rotation=rng.randint(0, 15)))
        for _ in range(n * 2):
            x, z = rng.randint(x1, x2 - 3), rng.randint(z1, z2 - 3)
            if all(m.est_air(x + dx, 64, z + dz) and m.get(x + dx, 63, z + dz) == m.id(S('grass_block', snowy=False))
                   for dx in range(3) for dz in range(3)):
                for dx in range(3):
                    for dz in range(3):
                        m.set(x + dx, 63, z + dz, S('farmland', moisture=7))
                        m.set(x + dx, 64, z + dz, S(rng.choice(['wheat', 'carrots', 'potatoes']), age=7))
        # barricades sur les rues qui entrent dans le quartier (au bord de son emprise)
        for (x, z) in ((x1, (z1 + z2) // 2), (x2, (z1 + z2) // 2), ((x1 + x2) // 2, z1), ((x1 + x2) // 2, z2)):
            for k in range(-4, 5):
                xx, zz = (x, z + k) if x in (x1, x2) else (x + k, z)
                if m.dedans(xx, 64, zz) and m.est_air(xx, 64, zz):
                    m.fill(xx, 64, zz, xx, 65, zz, S('cobblestone'))
    elif s == 'quarantaine':
        for _ in range(n * 2):
            x, z = rng.randint(x1, x2 - 6), rng.randint(z1, z2 - 5)
            if all(m.est_air(x + dx, 64, z + dz) for dx in range(6) for dz in range(5)):
                for dx in range(6):
                    for dz in range(5):
                        m.fill(x + dx, 64, z + dz, x + dx, 66 - abs(dz - 2), z + dz, S('white_wool'))
                m.vide(x + 1, 64, z + 1, x + 4, 65, z + 3)
        for _ in range(n):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            if libre(x, z):
                ch.panneau(x, 64, z, ['ZONE DE', 'QUARANTAINE', 'Accès interdit', 'Forces armées'], rotation=rng.randint(0, 15))
        for _ in range(n * 8):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            if libre(x, z):
                m.set(x, 64, z, S('mud_brick_slab', type='bottom', waterlogged=False))
    elif s == 'pillee':
        for _ in range(n * 10):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            if libre(x, z):
                m.set(x, 64, z, rng.choice([S('brown_carpet'), S('white_carpet'), S('barrel', facing='up', open=True)]))


# ============================================================================ construction d'une ville (une fois, en cache)
_VILLES = {}


def construire(v):
    if v['id'] in _VILLES:
        return _VILLES[v['id']]
    pv = plan_ville(v)
    ch = ChantierCite(v, pv)
    dessiner_rues(ch, pv)
    if pv['metro']:
        metro(ch, pv, pv['quartiers'])
    qd = {q['id']: q for q in pv['quartiers']}
    uniques = set()
    # les grands îlots d'abord (les grands équipements y trouvent leur place)
    for b in sorted(pv['ilots'], key=lambda b: -min(b['x2'] - b['x1'], b['z2'] - b['z1'])):
        q = qd.get(b['q'])
        if q:
            try:
                recettes(ch, b, q, uniques, v)
            except Exception as e:   # un îlot raté ne doit pas faire tomber la ville
                print('  [%s] îlot (%d,%d) : %s' % (v['id'], b['x1'], b['z1'], e))
    # lampadaires de rue : on garde leur quartier (Skript les rallume avec le courant)
    carte = carte_quartiers(pv)
    D = pv['S'] // 2
    rue = []
    for l in ch.ctx.lampes:
        if 'froglight' in l['on']:
            q = pv['quartiers'][carte[l['z'] + D, l['x'] + D]]
            rue.append((l['x'], l['y'], l['z'], q['id']))
    for l in ch.ctx.lampes:
        m = ch.m
        m.set(l['x'], l['y'], l['z'], l['off'])
    ch.m.passe_connexions()
    ch.m.passe_escaliers()
    import za_moderne
    za_moderne.habiller(ch.ctx)
    apocalypse(ch, pv, v)
    ch.m.compacter()
    st = SI.Structure.depuis_monde(v['id'], ch.m, ch.coffres)
    _VILLES[v['id']] = (st, pv, list(ch.lieux), rue)
    return _VILLES[v['id']]


# ============================================================================ le plan de la carte : fenêtres et quartiers
def y_ville(v):
    import terrain as T
    D = v['n'] * TUILE // 2
    xs = np.linspace(v['x'] - D, v['x'] + D, 9)
    zs = np.linspace(v['z'] - D, v['z'] + D, 9)
    X, Z = np.meshgrid(xs, zs)
    h, _, _ = T.base(X, Z)
    return int(max(64, round(float(np.median(h)))))


def sites_du_plan():
    out = []
    for v in VILLES:
        y = y_ville(v)
        n = v['n']
        for i in range(n):
            for j in range(n):
                out.append({'id': '%s_t%d%d' % (v['id'], i, j), 'type': 'ville_tuile', 'nom': v['nom'],
                            'x': v['x'] + (i - (n - 1) / 2) * TUILE, 'z': v['z'] + (j - (n - 1) / 2) * TUILE,
                            'larg': TUILE, 'prof': TUILE, 'y': y, 'ville': v['id'], 'ti': i, 'tj': j, 'bible': True})
    for s in out:
        s['x'], s['z'] = int(s['x']), int(s['z'])
    return out


def routes_du_plan():
    """Les routes qui relient chaque ville au réseau (boulevard central -> route existante)."""
    out = []
    for v in VILLES:
        D = v['n'] * TUILE // 2
        cote, pts, nom = v['sortie']
        dep = {'est': (v['x'] + D, v['z']), 'ouest': (v['x'] - D, v['z']), 'nord': (v['x'], v['z'] - D),
               'sud': (v['x'], v['z'] + D)}[cote]
        out.append((nom, [dep] + pts))
    return out


def quartiers_du_plan():
    """Les quartiers de toutes les villes, en coordonnées du monde (zones vivantes, lieux, économie)."""
    out = []
    for v in VILLES:
        pv = plan_ville(v)
        y = y_ville(v)
        for q in pv['quartiers']:
            out.append({'id': q['id'], 'type': 'quartier', 'genre': q['genre'], 'sort': q['sort'],
                        'nom': '%s — %s' % (v['nom'], q['nom']), 'x': v['x'] + q['cx'], 'z': v['z'] + q['cz'], 'y': y,
                        'dx': (q['x2'] - q['x1']) // 2 + 4, 'dz': (q['z2'] - q['z1']) // 2 + 4, 'ville': v['id']})
    return out


def tuile(site, plan):
    """La fenêtre 240 x 240 d'une ville (sites.structure_de -> batisse.ville_tuile)."""
    v = next(v for v in VILLES if v['id'] == site['ville'])
    st, pv, lieux, rue = construire(v)
    D = pv['S'] // 2
    x0 = -D + site['ti'] * TUILE
    z0 = -D + site['tj'] * TUILE
    sx, sz = x0 - st.ox, z0 - st.oz
    a = st.a[:, sz:sz + TUILE, sx:sx + TUILE].copy()
    dedans = lambda x, z: x0 <= x < x0 + TUILE and z0 <= z < z0 + TUILE
    out = SI.Structure(site['id'], a, st.pal, x0, st.oy, z0,
                       [s for s in st.signs if dedans(s['x'], s['z'])],
                       [c for c in st.containers if dedans(c['x'], c['z'])],
                       [c for c in st.coffres if dedans(c[0], c[2])])
    # lieux et lampadaires : chacun dans la fenêtre qui contient son centre
    out.lieux = [l for l in lieux if dedans(l[2], l[3])]
    out.lampes = [l for l in rue if dedans(l[0], l[2])]
    return out
