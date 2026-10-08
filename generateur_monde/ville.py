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
from ville_bat import lot, rangee, perimetre, echelle, _nv, ASPH, TROTTOIR
from za_blocs import Monde
from za_meubles import Ctx, Repere

TUILE = 240
Y0 = 44            # bas du chantier (métro, morgue)
HAUT = 120         # jusqu'à y=163 local (tours)

# ---------------------------------------------------------------------------- les villes de la carte
# (le type décide des quartiers ; « sorts » : un sort par genre de quartier, dans l'ordre des quartiers du type)
VILLES = [
    {'id': 'laurentia', 'nom': 'Laurentia', 'type': 'metropole', 'x': -1800, 'z': 3600, 'n': 3, 'graine': 7101,
     'sortie': None},      # l'autoroute 20 la traverse (surélevée au-dessus du boulevard est-ouest)
    {'id': 'saint_remi', 'nom': 'Saint-Rémi-de-la-Voie', 'type': 'industrielle', 'x': 1200, 'z': 4200, 'n': 2,
     'graine': 7202, 'sortie': ('ouest', [(500, 4200), (35, 4200)], 'Rue de la Gare')},
    {'id': 'sainte_agathe', 'nom': 'Sainte-Agathe-des-Champs', 'type': 'residentielle', 'x': -400, 'z': 3000, 'n': 2,
     'graine': 7303, 'sortie': ('est', [(-45, 3000)], 'Chemin Sainte-Agathe')},
    {'id': 'fort_lafleche', 'nom': 'Fort-Laflèche', 'type': 'militaire', 'x': 3400, 'z': 3100, 'n': 2, 'graine': 7404,
     'sortie': ('sud', [(3400, 3600)], 'Chemin de la Garnison')},
    {'id': 'mont_levis', 'nom': 'Mont-Lévis', 'type': 'universitaire', 'x': -3000, 'z': 3100, 'n': 2, 'graine': 7505,
     'sortie': ('sud', [(-3000, 3600)], "Boulevard de l'Université")},
    {'id': 'saint_jacques', 'nom': 'Saint-Jacques-des-Ponts', 'type': 'riviere', 'x': 1900, 'z': 1300, 'n': 2,
     'graine': 7606, 'y': 64, 'sortie': ('est', [(2300, 1090), (2456, 1021)], 'Route des Ponts', -150)},
]

# autoroute 20 : traverse les plaines du sud d'ouest en est ; dans Laurentia, elle passe en hauteur (ville.py)
AUTOROUTES = [('Autoroute 20 ouest', [(-5100, 3600), (-2160, 3600)]),
              ('Autoroute 20 est', [(-1440, 3600), (80, 3600), (5100, 3600)])]

# quartiers de chaque type : (genre, fx, fz, sort) — fx, fz : position relative (0..1) du « germe » du quartier
TYPES = {
    'metropole': {
        'quartiers': [('centre', 0.5, 0.5, 'envahie'), ('affaires', 0.52, 0.28, 'guerre'),
                      ('civique', 0.78, 0.5, 'quarantaine'), ('commercial', 0.5, 0.78, 'pillee'),
                      ('residentiel', 0.24, 0.5, 'evacuee'), ('residentiel', 0.78, 0.2, 'abandon'),
                      ('banlieue', 0.2, 0.82, 'brulee'), ('riche', 0.2, 0.18, 'faction'),
                      ('pauvre', 0.8, 0.85, 'envahie'), ('industriel', 0.92, 0.66, 'brulee')],
        'avenues': (120, 170), 'metro': True, 'rail': None, 'aerienne': True},
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
    # ville de garnison : la base au nord (clôturée), les logements des familles, un petit centre
    'militaire': {
        'quartiers': [('base', 0.35, 0.22, 'guerre'), ('base', 0.72, 0.25, 'quarantaine'),
                      ('centre', 0.5, 0.62, 'evacuee'), ('logements', 0.2, 0.75, 'abandon'),
                      ('logements', 0.8, 0.72, 'evacuee'), ('commercial', 0.5, 0.88, 'pillee')],
        'avenues': (110, 140), 'metro': False, 'rail': None, 'campagne': 0.2},
    # ville universitaire : le campus (pavillons, bibliothèque, quadrilatère, tour de l'horloge), la vie étudiante
    'universitaire': {
        'quartiers': [('campus', 0.4, 0.3, 'quarantaine'), ('campus', 0.68, 0.3, 'abandon'),
                      ('centre', 0.5, 0.62, 'envahie'), ('residentiel', 0.8, 0.7, 'pillee'),
                      ('commercial', 0.25, 0.6, 'pillee'), ('parc', 0.22, 0.85, 'abandon'),
                      ('riche', 0.75, 0.9, 'faction')],
        'avenues': (100, 140), 'metro': False, 'rail': None, 'campagne': 0.2},
    # ville de rivière : la rivière Blanche la coupe en deux ; quais, ponts, un tunnel, le vieux port
    'riviere': {
        'quartiers': [('vieux', 0.4, 0.3, 'abandon'), ('centre', 0.65, 0.3, 'envahie'), ('port', 0.5, 0.62, 'faction'),
                      ('residentiel', 0.2, 0.7, 'evacuee'), ('banlieue', 0.78, 0.8, 'pillee'),
                      ('industriel', 0.15, 0.25, 'brulee'), ('riche', 0.85, 0.2, 'guerre')],
        'avenues': (100, 130), 'metro': False, 'rail': None, 'riviere': True},
}

# taille visée des îlots et largeur des rues secondaires, par genre de quartier
GENRES = {
    'centre': (58, 7), 'affaires': (66, 7), 'civique': (90, 7), 'commercial': (64, 7), 'residentiel': (56, 7),
    'banlieue': (62, 5), 'riche': (84, 5), 'pauvre': (48, 5), 'industriel': (112, 7), 'gare': (90, 7),
    'parc': (110, 5), 'base': (110, 7), 'logements': (58, 5), 'campus': (120, 7), 'vieux': (52, 5), 'port': (72, 7),
}
NOMS = {
    'centre': ['Centre-ville'], 'affaires': ["Quartier des affaires"], 'civique': ["Quartier de l'Hôpital"],
    'commercial': ['Boulevard des Commerces', 'Les Galeries', 'La Promenade', 'Le Carrefour', 'Rue du Marché'], 'gare': ['Quartier de la Gare'],
    'residentiel': ['Le Plateau', 'Saint-Joseph', 'Le Faubourg', 'Haut-Laurier', 'Les Cèdres', 'Villeray', 'Limoilou'],
    'banlieue': ['Les Érables', 'Les Pins', 'Bois-Joli', 'Petite-Rivière', 'Les Bouleaux', 'Le Domaine'],
    'riche': ['Côte-Sainte-Anne', 'Le Belvédère', 'Mont-Royal-des-Pins', 'Les Hauteurs', 'Le Golf'],
    'pauvre': ['Le Bas-de-la-Ville', 'Saint-Roch', 'Les Tanneries', 'La Cité ouvrière'],
    'industriel': ['Parc industriel', "Parc d'affaires Laurier", 'Les Forges', 'La Fonderie', 'Les Moulins'],
    'parc': ['Parc régional', 'Les Prés', 'Bois-Francs'],
    'base': ['Secteur nord de la base', 'Secteur des hangars'], 'logements': ['Logements militaires', 'Cité des familles'],
    'campus': ['Campus principal', 'Cité universitaire'], 'vieux': ['Vieille-Ville'], 'port': ['Le Vieux-Port'],
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
    # rivière (ville de rivière) : un couloir est-ouest entre deux quais, à la place des avenues qui y tombaient
    riv = None
    if ty.get('riviere'):
        zc, rw = riviere_locale(v, D)
        zq1 = int(math.floor((zc - rw).min())) - 18
        zq2 = int(math.ceil((zc + rw).max())) + 18
        LZ = sorted([l for l in LZ if not (zq1 - 45 < l[0] < zq2 + 45) or l[2] == 'ceinture'] +
                    [(zq1, 9, 'quai'), (zq2, 9, 'quai')])
        riv = {'zc': zc, 'w': rw, 'zq1': zq1, 'zq2': zq2}
    nx, nz = len(LX) - 1, len(LZ) - 1
    eau = set()
    jr = None
    if riv:
        jr = next(j for j in range(nz) if LZ[j][2] == 'quai' and LZ[j + 1][2] == 'quai')
        eau = {(i, jr) for i in range(nx)}
    # coins en campagne (petites villes) : la ville s'effiloche au lieu de finir sur un carré
    nature = set()
    hors = set(eau)
    if ty.get('campagne') and nx >= 3 and nz >= 3:
        for i in range(nx):
            for j in range(nz):
                bord = (i in (0, nx - 1)) + (j in (0, nz - 1))
                if bord == 2 and rng.random() < 0.75 or bord == 1 and rng.random() < ty['campagne']:
                    nature.add((i, j))
    hors = nature | eau     # mailles sans bâtiments
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
            if a in pris or b in pris or a in hors or b in hors:
                continue
            if rng.random() < 0.25:
                fus.add((i, j))
                pris.update((a, b))
    routes = []
    # ponts (et un tunnel) : les avenues et le boulevard franchissent la rivière, la ceinture s'arrête aux quais
    if riv:
        cand = [i for i in range(1, nx) if LX[i][2] in ('avenue', 'boulevard')]
        av = [i for i in cand if LX[i][2] == 'avenue']
        i_tun = rng.choice(av) if len(av) >= 2 else None
        i_det = rng.choice([i for i in av if i != i_tun]) if len(av) >= 2 else None
        for i in cand:
            c, w, k = LX[i]
            x = xpos(i, jr)
            if i == i_tun:
                r = Route('z', x, LZ[jr][0] - 75, LZ[jr + 1][0] + 75, w, 'tunnel')
            else:
                r = Route('z', x, LZ[jr][0] - LZ[jr][1] // 2, LZ[jr + 1][0] + LZ[jr + 1][1] // 2, w,
                          'pont_grand' if k == 'boulevard' else 'pont')
                r.detruit = i == i_det
            routes.append(r)
    # tronçons nord-sud
    for i in range(nx + 1):
        c, w, k = LX[i]
        for j in range(nz):
            cotes = [(i - 1, j), (i, j)]
            dedans = [m for m in cotes if 0 <= m[0] < nx and m not in hors]
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
            dedans = [m for m in cotes if 0 <= m[1] < nz and m not in hors]
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
            if (i, j) in eau:
                i = i1 + 1
                continue
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
    return {'S': S_, 'routes': routes, 'ilots': ilots, 'quartiers': quartiers, 'rail': rail, 'metro': ty['metro'],
            'riviere': riv, 'aerienne': ty.get('aerienne', False)}


def riviere_locale(v, D):
    """La rivière Blanche dans le repère de la ville : centre zc[x] et demi-largeur w[x], pour x de -D à D-1."""
    import plan as PL
    pts = PL._riviere(None)
    xs = v['x'] + np.arange(-D, D)
    rx = np.array([p[0] for p in pts])
    zc = np.interp(xs, rx, np.array([p[1] for p in pts])) - v['z']
    w = np.interp(xs, rx, np.array([p[2] for p in pts]))
    return zc, w


# ============================================================================ chantier d'une ville entière
class ChantierCite(Chantier):
    def __init__(self, v, pv):
        self.site = {'id': v['id'], 'graine': v['graine']}
        self.nom_ville = v['nom']
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
    SPECIAUX = ('rail', 'impasse', 'pont', 'pont_grand', 'tunnel')
    for r in pv['routes']:
        x1, z1, x2, z2 = r.rect()
        if r.k in SPECIAUX:
            continue
        m.fill(x1, 63, z1, x2, 63, z2, ASPH)
        m.vide(x1, 64, z1, x2, 80, z2)
    for r in pv['routes']:
        if r.k == 'impasse':
            impasse(ch, r)
    if pv.get('riviere'):
        riviere(ch, pv)
    for r in pv['routes']:
        x1, z1, x2, z2 = r.rect()
        if r.k in SPECIAUX:
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
            elif r.k in ('rue', 'ceinture', 'quai') and t % 6 < 3:
                x, z = (t, r.c) if r.axe == 'x' else (r.c, t)
                m.set(x, 63, z, S('yellow_concrete'))
    # les rues qui se croisent ont été peintes l'une sur l'autre : on nettoie les carrefours
    for r in pv['routes']:
        for o in pv['routes']:
            if r.axe == o.axe or r.k in ('rail', 'tunnel', 'impasse') or o.k in ('rail', 'tunnel', 'impasse'):
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
            if r.axe == 'z' and r.k == 'boulevard' and r.a < rail.c < r.b:
                passage_inferieur(ch, r, rail)
            elif r.axe == 'z' and r.k != 'rail' and r.a < rail.c < r.b:
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
    # ponts et tunnel (ville de rivière)
    for r in pv['routes']:
        if r.k in ('pont', 'pont_grand'):
            pont(ch, r, pv)
        elif r.k == 'tunnel':
            tunnel(ch, r, pv)
    # rond-point au croisement des boulevards (s'il y en a un)
    rp = not pv.get('riviere')
    for dx in range(-15, 16) if rp else ():
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
    if rp:
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
        if genre.get(b['q']) in ('residentiel', 'banlieue', 'riche', 'campus', 'vieux', 'logements', 'parc', 'centre',
                                 'pauvre'):
            arbres_de_rue(ch, b)
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
                if (x - x1) % 9 == 0:
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


# ============================================================================ grands ouvrages : rivière, ponts, tunnel, autoroute
MUR = lambda: S('stone_brick_wall', east='none', west='none', north='none', south='none', up=True, waterlogged=False)


def riviere(ch, pv):
    """La rivière Blanche dans la ville : quais de pierre, promenade plantée entre les quais et l'eau, fond varié.
    L'eau est au niveau de la rivière du monde (y local 61 = y 62 du monde : la ville est posée à y=64)."""
    m, rng = ch.m, ch.rng
    rv = pv['riviere']
    D = pv['S'] // 2
    za, zb = rv['zq1'] + 5, rv['zq2'] - 5
    herbe = S('grass_block', snowy=False)
    fonds = [S('gravel'), S('sand'), S('clay'), S('gravel'), S('mud')]
    for xi, x in enumerate(range(-D, D)):
        zc, w = rv['zc'][xi], rv['w'][xi]
        zt, zbn = int(round(zc - w)), int(round(zc + w))
        m.vide(x, 64, za, x, 100, zb)
        m.fill(x, 63, za, x, 63, zb, herbe)
        for z in range(zt, zbn + 1):
            t = (z - zc) / max(w, 1)
            fond = 61 - int(3 + 7 * max(0.0, 1 - t * t))
            m.set(x, fond, z, fonds[(x * 7 + z * 13) % len(fonds)])
            m.fill(x, fond + 1, z, x, 61, z, S('water'))
            m.vide(x, 62, z, x, 63, z)
        # quais : murs de pierre, garde-corps
        for z in (zt - 1, zbn + 1):
            m.fill(x, 50, z, x, 63, z, S('stone_bricks') if (x + z) % 9 else S('mossy_stone_bricks'))
            m.set(x, 64, z, MUR())
        # promenade le long de l'eau
        for z in list(range(zt - 6, zt - 3)) + list(range(zbn + 4, zbn + 7)):
            if za <= z <= zb:
                m.set(x, 63, z, S('polished_andesite'))
        if x % 18 == 0:
            for z, regard in ((zt - 3, 'south'), (zbn + 3, 'north')):
                RU.lampadaire_parc(ch.R0, x, z)
        elif x % 18 == 9:
            RU.banc(ch.R0, x, zt - 3, 'south')
            RU.banc(ch.R0, x, zbn + 3, 'north')
        # allées d'arbres le long de la promenade, sentiers vers la rue, kiosques et massifs là où la berge est large
        for z0, z1, za_ in ((za + 1, zt - 9, zt - 8), (zbn + 9, zb - 1, zbn + 8)):
            if za <= za_ <= zb and x % 8 == 4:
                try:
                    RU.arbre_rue(ch.R0, x, za_, rng)
                except Exception:
                    pass
            if x % 40 == 20:
                m.fill(x - 1, 63, min(z0, z1), x + 1, 63, max(z0, z1), S('polished_andesite'))
            elif z1 - z0 >= 16 and x % 40 == 0:
                kiosque(ch, x, (z0 + z1) // 2)
            elif z1 - z0 >= 8 and x % 13 == 7:
                try:
                    RU.arbre_rue(ch.R0, x, rng.randint(z0 + 1, z1 - 1), rng)
                except Exception:
                    pass
            for z in range(z0, z1 + 1):
                if rng.random() < 0.07 and m.est_air(x, 64, z) and m.get(x, 63, z) == herbe:
                    m.set(x, 64, z, S(rng.choice(['poppy', 'dandelion', 'oxeye_daisy', 'cornflower', 'grass', 'fern',
                                                  'grass', 'azure_bluet'])))
    ch.lieux.append(('riviere', 'Les quais de la rivière Blanche', 0, int(rv['zc'][D]), D, int(rv['w'][D]) + 12))


def kiosque(ch, x, z):
    """Kiosque à musique de parc : socle de pierre, colonnes, toit pointu."""
    m = ch.m
    m.fill(x - 3, 63, z - 3, x + 3, 64, z + 3, S('stone_bricks'))
    m.fill(x - 2, 64, z - 2, x + 2, 64, z + 2, S('spruce_planks'))
    for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        m.fill(x + dx, 65, z + dz, x + dx, 67, z + dz, S('white_concrete'))
    m.fill(x - 3, 68, z - 3, x + 3, 68, z + 3, S('dark_oak_planks'))
    m.fill(x - 2, 69, z - 2, x + 2, 69, z + 2, S('dark_oak_planks'))
    m.fill(x - 1, 70, z - 1, x + 1, 70, z + 1, S('dark_oak_planks'))
    m.set(x, 71, z, S('lightning_rod', facing='up', powered=False, waterlogged=False))
    m.set(x, 67, z, S('lantern', hanging=True, waterlogged=False))


def _bande_eau(pv, x):
    rv = pv['riviere']
    D = pv['S'] // 2
    zc, w = rv['zc'][x + D], rv['w'][x + D]
    return int(round(zc - w)), int(round(zc + w)), zc


def pont(ch, r, pv):
    """Pont d'avenue (ou grand pont du boulevard : trottoirs, pylônes, arches). Un pont peut être coupé (apocalypse)."""
    m, rng = ch.m, ch.rng
    x1, _, x2, _ = r.rect()
    rv = pv['riviere']
    za, zb = rv['zq1'] + 5, rv['zq2'] - 5
    grand = r.k == 'pont_grand'
    zt, zbn, zc = _bande_eau(pv, r.c)
    m.vide(x1, 64, za, x2, 90, zb)
    m.fill(x1, 62, za, x2, 62, zb, S('stone_bricks'))
    m.fill(x1, 63, za, x2, 63, zb, ASPH)
    for z in range(za, zb + 1):
        m.set(x1, 64, z, MUR())
        m.set(x2, 64, z, MUR())
        if grand:
            m.set(x1 + 1, 63, z, TROTTOIR)
            m.set(x2 - 1, 63, z, TROTTOIR)
        elif z % 6 < 3:
            m.set(r.c, 63, z, S('yellow_concrete'))
    # piles dans l'eau, et des arches sous le tablier du grand pont
    pas = 14 if grand else 12
    for z in range(zt + 4, zbn - 3, pas):
        m.fill(x1 + 1, 48, z, x2 - 1, 61, z + 2, S('stone_bricks'))
        if grand:
            for k in range(1, 5):
                for zz in (z - k, z + 2 + k):
                    if zt < zz < zbn:
                        m.fill(x1 + 1, 61 - (4 - k) // 2, zz, x2 - 1, 61, zz, S('stone_bricks'))
    if grand:
        for z in range(za + 2, zb - 1, 14):
            RU.lampadaire(ch.R0, x1 + 1, z, 'east')
            RU.lampadaire(ch.R0, x2 - 1, z + 7, 'west')
        # pylônes aux deux têtes du pont
        for z in (za, zb):
            for x in (x1, x2):
                m.fill(x, 64, z, x, 68, z, S('chiseled_stone_bricks'))
                m.set(x, 69, z, S('lantern', hanging=False, waterlogged=False))
        ch.panneau(x1 - 1 if x1 - 1 > -pv['S'] // 2 else x1, 65, za - 1, ['PONT', 'SAINT-JACQUES', '1912', ''],
                   mur='north')
    else:
        for z in range(za + 4, zb - 3, 16):
            RU.lampadaire(ch.R0, x1, z, 'east')
    if getattr(r, 'detruit', False):
        # le tablier s'est effondré au milieu : bouts de route qui pendent, débris dans l'eau, voiture au bord
        g1, g2 = int(zc) - 6, int(zc) + 6
        m.vide(x1, 60, g1, x2, 66, g2)
        for x in range(x1, x2 + 1):
            for z in (g1 - 1, g2 + 1):
                if rng.random() < 0.6:
                    m.fill(x, 59 + rng.randint(0, 2), z, x, 61, z, S('iron_bars'))
            for z in range(g1, g2 + 1):
                if rng.random() < 0.3:
                    y = 52 + rng.randint(0, 6)
                    m.set(x, y, z, S(rng.choice(['cobblestone', 'gray_concrete', 'stone_bricks', 'andesite'])))
        RU.voiture(ch.R0, r.c, g1 - 3, 'south', rng.choice(COULEURS_AUTO), 64, 'auto', portes=True)
        for z, regard in ((za + 1, 'north'), (zb - 1, 'south')):
            m.fill(x1 + 1, 64, z, x2 - 1, 64, z, S('red_concrete'))
            ch.panneau(r.c, 65, z, ['PONT FERMÉ', 'Effondrement', 'DANGER', ''], rotation=0 if regard == 'south' else 8,
                       couleur='red')
        ch.lieux.append(('pont_detruit', 'Le pont effondré', r.c, int(zc), 8, 20))
    else:
        ch.lieux.append(('pont', 'Le grand pont' if grand else 'Pont de la rue %d' % (abs(r.c) // 10), r.c, int(zc),
                         r.w // 2 + 2, (zbn - zt) // 2 + 4))


def tunnel(ch, r, pv):
    """Tunnel sous la rivière : tranchée ouverte, portail, puis tube éclairé (éteint) sous le lit, jusqu'à l'autre rive."""
    m, rng = ch.m, ch.rng
    x1, _, x2, _ = r.rect()
    zt, zbn, zc = _bande_eau(pv, r.c)
    FOND = 45
    n1 = zt - 2 - 54        # début de la descente côté nord
    s2 = zbn + 2 + 54       # fin de la remontée côté sud
    beton = S('light_gray_concrete')
    for z in range(n1, s2 + 1):
        if z < zt - 2:
            y = 63 - (z - n1) // 3
        elif z > zbn + 2:
            y = 63 - (s2 - z) // 3
        else:
            y = FOND
        y = max(FOND, y)
        if y >= 63:
            continue
        couvert = y <= 57
        m.fill(x1, y - 1, z, x2, y - 1, z, beton)
        m.fill(x1 + 1, y, z, x2 - 1, y, z, ASPH)
        if z % 6 < 3:
            m.set(r.c, y, z, S('yellow_concrete'))
        if couvert:
            m.vide(x1 + 1, y + 1, z, x2 - 1, y + 4, z)
            m.fill(x1, y + 5, z, x2, y + 5, z, beton)
            m.fill(x1, y, z, x1, y + 4, z, S('white_concrete'))
            m.fill(x2, y, z, x2, y + 4, z, S('white_concrete'))
            if z % 8 == 0:
                ch.ctx.lampe(r.c, y + 5, z, S('sea_lantern'), beton)
        else:
            m.vide(x1 + 1, y + 1, z, x2 - 1, 80, z)
            m.fill(x1, y, z, x1, 63, z, S('stone_bricks'))
            m.fill(x2, y, z, x2, 63, z, S('stone_bricks'))
            m.set(x1, 64, z, S('iron_bars'))
            m.set(x2, 64, z, S('iron_bars'))
    # portails (là où la tranchée devient tube)
    for z, mur in ((n1 + 18, 'north'), (s2 - 18, 'south')):
        m.fill(x1, 62, z, x2, 63, z, S('polished_andesite'))
        ch.panneau(r.c, 61, z - 1 if mur == 'north' else z + 1, ['TUNNEL', 'Louis-Fréchette', 'Hauteur 4 m', ''],
                   mur=mur)
    # embouteillage figé dans le tube
    for z in range(zt, zbn, 9):
        if rng.random() < 0.6:
            RU.voiture(ch.R0, r.c - 2, z, 'south', rng.choice(COULEURS_AUTO), FOND + 1,
                       'brulee' if rng.random() < 0.2 else 'auto', portes=rng.random() < 0.5)
    ch.lieux.append(('tunnel', 'Tunnel Louis-Fréchette', r.c, int(zc), 6, (s2 - n1) // 2))


def passage_inferieur(ch, r, rail):
    """Le boulevard passe sous la voie ferrée (ville industrielle) : rampes, murs, tablier de pierre sous les rails."""
    fait = ch.__dict__.setdefault('_passages', set())
    if r.c in fait:
        return
    fait.add(r.c)
    m = ch.m
    x1, _, x2, _ = r.rect()
    _, rz1, _, rz2 = rail.rect()
    a, b = rz1 - 1 - 18, rz2 + 1 + 18
    for z in range(a, b + 1):
        y = 63 - min(6, (z - a) // 3, (b - z) // 3)
        if y >= 63:
            continue
        sous_rail = rz1 - 1 <= z <= rz2 + 1
        m.fill(x1 + 1, y, z, x2 - 1, y, z, ASPH)
        if sous_rail:
            m.vide(x1 + 1, y + 1, z, x2 - 1, 62, z)
            m.fill(x1, 63, z, x2, 63, z, S('stone_bricks'))
        else:
            m.vide(x1 + 1, y + 1, z, x2 - 1, 80, z)
            m.set(x1, 64, z, S('iron_bars'))
            m.set(x2, 64, z, S('iron_bars'))
        m.fill(x1, y, z, x1, 63, z, S('stone_bricks'))
        m.fill(x2, y, z, x2, 63, z, S('stone_bricks'))
    ch.panneau(r.c, 62, rz1 - 2, ['PASSAGE', 'INFÉRIEUR', 'Hauteur 4 m', ''], mur='north')
    ch.lieux.append(('tunnel', 'Passage sous la voie ferrée', r.c, (rz1 + rz2) // 2, r.w // 2, 24))


def autoroute_aerienne(ch, pv, v):
    """L'autoroute 20 au-dessus du boulevard est-ouest : rampes aux deux bouts, tablier sur piliers, lampadaires,
    portiques de signalisation ; l'apocalypse : un bouchon figé et une travée effondrée."""
    m, rng = ch.m, ch.rng
    D = pv['S'] // 2
    TOP = 74
    beton = S('light_gray_concrete')

    def niveau(x):
        return max(0, min(22, (x + D - 8) // 2, (D - 9 - x) // 2))
    for x in range(-D, D):
        L = niveau(x)
        if L <= 0:
            continue
        y = 63 + L // 2
        demi = L % 2
        if L < 22:
            m.fill(x, 64, -6, x, y, 6, beton)
            m.fill(x, y, -5, x, y, 5, ASPH)
            if demi:
                m.fill(x, y + 1, -5, x, y + 1, 5, S('polished_andesite_slab', type='bottom'))
        else:
            m.vide(x, 66, -6, x, 72, 6)
            m.fill(x, 73, -6, x, 73, 6, S('smooth_stone'))
            m.fill(x, TOP, -6, x, TOP, 6, ASPH)
        sol = y if not demi else y + 1
        m.set(x, sol + (0 if demi else 1), -6, MUR())
        m.set(x, sol + (0 if demi else 1), 6, MUR())
        if L == 22:
            if x % 8 < 4:
                for z in (-3, 3):
                    m.set(x, TOP, z, S('white_concrete'))
            m.set(x, TOP + 1, 0, S('smooth_stone_slab', type='bottom'))
            if x % 24 == 0:
                RU.lampadaire(ch.R0, x, 0, 'north', y=TOP + 1, hauteur=4)
                RU.lampadaire(ch.R0, x, 0, 'south', y=TOP + 1, hauteur=4)
    # piliers (sur le terre-plein, en évitant le rond-point et les édicules du métro)
    for x in range(-D + 46, D - 46):
        if x % 18 or abs(x) < 17:
            continue
        if any('glass' in m.get(xx, 64, zz) for xx in (x, x + 1) for zz in (-2, 0, 2)):
            continue
        m.fill(x, 64, -1, x + 1, 72, 1, beton)
        m.fill(x, 72, -6, x + 1, 72, 6, S('smooth_stone'))
    for x in (-17, 16):
        m.fill(x, 64, -1, x + 1, 72, 1, beton)
    # portiques verts : « A-20 »
    for x, txt, mur in ((-D + 60, ['A-20 EST', 'Laurentia', 'Centre-ville', ''], 'west'),
                        (D - 61, ['A-20 OUEST', 'Laurentia', 'Mont-Lévis', ''], 'east')):
        for z in (-6, 6):
            m.fill(x, TOP + 1, z, x, TOP + 6, z, S('iron_bars'))
        m.fill(x, TOP + 5, -5, x, TOP + 7, 5, S('green_concrete'))
        ch.panneau(x - 1 if mur == 'west' else x + 1, TOP + 6, 0, txt, mur=mur, couleur='white')
    # bouchon figé : l'exode du Jour 8, pare-chocs contre pare-chocs
    x0 = rng.randint(-D // 2, -40)
    for x in range(x0, x0 + 140, 7):
        for z, d in ((-3, 'west'), (3, 'east')):
            if -D + 46 < x < D - 46 and rng.random() < 0.75:
                RU.voiture(ch.R0, x, z, d, rng.choice(COULEURS_AUTO), TOP + 1,
                           'brulee' if rng.random() < 0.15 else rng.choice(['auto', 'auto', 'taxi']),
                           portes=rng.random() < 0.5)
    # une travée effondrée sur le boulevard
    xc = rng.choice([x for x in range(40, D - 70) if x % 18 not in (0, 1, 17)])
    m.vide(xc, 72, -6, xc + 10, 77, 6)
    for x in range(xc, xc + 11):
        for z in range(-6, 7):
            if rng.random() < 0.55:
                m.fill(x, 64, z, x, 64 + rng.randint(0, 1), z, S(rng.choice(['smooth_stone', 'gray_concrete', 'cobblestone',
                                                                                 'light_gray_concrete'])))
        for xx in (xc - 1, xc + 11):
            if rng.random() < 0.5:
                zz = rng.randint(-5, 5)
                m.fill(xx, 70, zz, xx, 72, zz, S('iron_bars'))
    RU.voiture(ch.R0, xc + 5, -2, 'east', 'red', 66, 'brulee')
    ch.lieux.append(('autoroute', 'Autoroute 20 (voie surélevée)', 0, 0, D, 9))


def arbres_de_rue(ch, b):
    """Alignement d'arbres le long des trottoirs (entre les lampadaires)."""
    m, rng = ch.m, ch.rng
    for x in range(b['x1'] + 15, b['x2'] - 5, 18):
        for z in (b['z1'], b['z2']):
            if m.est_air(x, 64, z) and rng.random() < 0.85:
                try:
                    RU.arbre_rue(ch.R0, x, z, rng)
                except Exception:
                    pass
    for z in range(b['z1'] + 15, b['z2'] - 5, 18):
        for x in (b['x1'], b['x2']):
            if m.est_air(x, 64, z) and rng.random() < 0.85:
                try:
                    RU.arbre_rue(ch.R0, x, z, rng)
                except Exception:
                    pass


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
    scene_maison(ch, R, L, P)
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
    scene_maison(ch, R, L, P)


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


# ============================================================================ ville de garnison
VERT_MIL = 'green_terracotta'


def char_assaut(m, x, z, axe='x', y=64, brule=False):
    """Char d'assaut (7 x 5) : chenilles, caisse, tourelle, canon."""
    c = S('coal_block') if brule else S(VERT_MIL)
    ch_ = S('blackstone') if brule else S('black_concrete')
    def put(a, b, yy, st):
        m.set(x + a, yy, z + b, st) if axe == 'x' else m.set(x + b, yy, z + a, st)
    for a in range(-3, 4):
        for b in range(-2, 3):
            put(a, b, y, ch_ if abs(b) == 2 else c)
            if abs(b) < 2:
                put(a, b, y + 1, c)
    for a in range(-1, 2):
        for b in range(-1, 2):
            put(a, b, y + 2, c)
    for a in range(2, 6):
        put(a, 0, y + 2, S('polished_basalt', axis='x' if axe == 'x' else 'z'))


def camion_mil(m, x, z, axe='x', y=64):
    """Camion de transport de troupes : cabine, bâche verte."""
    def put(a, b, yy, st):
        m.set(x + a, yy, z + b, st) if axe == 'x' else m.set(x + b, yy, z + a, st)
    for a in range(-4, 4):
        for b in (-1, 0, 1):
            put(a, b, y, S('black_concrete') if a in (-3, 2) and b != 0 else S(VERT_MIL))
    for b in (-1, 0, 1):
        put(3, b, y + 1, S('black_stained_glass') if b == 0 else S(VERT_MIL))
        for a in range(-4, 2):
            put(a, b, y + 1, S('green_wool'))
            put(a, b, y + 2, S('green_wool') if b == 0 or a % 2 else AIR)


def helicoptere(m, x, z, y=64):
    m.fill(x - 3, y + 1, z - 1, x + 2, y + 2, z + 1, S('green_concrete'))
    m.fill(x + 3, y + 1, z - 1, x + 3, y + 2, z + 1, S('black_stained_glass'))
    m.fill(x - 9, y + 2, z, x - 4, y + 2, z, S('green_concrete'))
    m.fill(x - 9, y + 3, z, x - 9, y + 4, z, S('green_concrete'))
    m.fill(x - 3, y, z - 2, x + 2, y, z - 2, S('iron_bars'))
    m.fill(x - 3, y, z + 2, x + 2, y, z + 2, S('iron_bars'))
    m.set(x, y + 3, z, S('iron_block'))
    m.fill(x - 6, y + 4, z, x + 6, y + 4, z, S('polished_blackstone_slab', type='bottom'))
    m.fill(x, y + 4, z - 6, x, y + 4, z + 6, S('polished_blackstone_slab', type='bottom'))


def cloture_base(ch, b):
    """Clôture de la base autour de l'îlot : grillage, barbelés, guérite et barrière au milieu du côté sud."""
    m, rng = ch.m, ch.rng
    x1, z1, x2, z2 = b['x1'] + 1, b['z1'] + 1, b['x2'] - 1, b['z2'] - 1
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            m.fill(x, 64, z, x, 66, z, S('iron_bars'))
            if rng.random() < 0.4:
                m.set(x, 67, z, S('cobweb'))
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            m.fill(x, 64, z, x, 66, z, S('iron_bars'))
            if rng.random() < 0.4:
                m.set(x, 67, z, S('cobweb'))
    gx = (x1 + x2) // 2
    m.vide(gx - 3, 64, z2, gx + 3, 67, z2)
    for k in range(-3, 4):
        m.set(gx + k, 65, z2, S('red_concrete') if k % 2 else S('white_concrete'))
    m.vide(gx - 3, 64, z2, gx + 3, 64, z2)
    m.fill(gx + 5, 64, z2 - 4, gx + 8, 67, z2 - 1, S('light_gray_concrete'))
    m.vide(gx + 6, 64, z2 - 3, gx + 7, 66, z2 - 2)
    m.fill(gx + 5, 65, z2 - 3, gx + 5, 66, z2 - 2, S('glass_pane'))
    m.fill(gx + 5, 68, z2 - 4, gx + 8, 68, z2 - 1, S('smooth_stone_slab', type='bottom'))
    ch.panneau(gx - 4, 65, z2 + 1, ['ZONE MILITAIRE', 'Accès interdit', 'Halte !', ''], mur='south', couleur='red')
    for (x, z) in ((x1 + 2, z1 + 2), (x2 - 2, z1 + 2)):
        # miradors aux coins
        m.fill(x, 64, z, x, 71, z, S('spruce_log', axis='y'))
        m.fill(x - 1, 72, z - 1, x + 1, 72, z + 1, S('spruce_planks'))
        m.fill(x - 1, 73, z - 1, x + 1, 73, z + 1, S('spruce_fence'))
        m.set(x, 73, z, AIR)
        m.fill(x - 1, 75, z - 1, x + 1, 75, z + 1, S('spruce_slab', type='bottom'))
        for y in range(64, 72):
            m.set(x, y, z + 1, S('ladder', facing='south', waterlogged=False))


def caserne_mil(ch, R, L, P):
    rng = ch.rng
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 68, P - 1, S('light_gray_concrete'))
    R.fill(0, 64, 0, L - 1, 64, P - 1, S(VERT_MIL))
    R.vide(1, 64, 1, L - 2, 67, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('gray_concrete'))
    R.fill(0, 69, 0, L - 1, 69, P - 1, S('green_concrete'))
    for a in range(2, L - 2, 3):
        R.set(a, 66, 0, S('glass_pane'))
        R.set(a, 66, P - 1, S('glass_pane'))
    for a in range(2, L - 2, 3):
        ZM.lit(R, a, 64, 1, 'south', 'green')
        if P >= 8:
            R.set(a, 64, P - 2, R.S('barrel', facing='up', open=False))
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'iron')
    ch.coffre(R, 1, 64, P // 2, 'east', SI.LOOT_MILITAIRE)
    x, z = R.xz(L // 2 + 2, P)
    ch.panneau(x, 67, z, ['CASERNE', 'Bataillon %d' % rng.randint(1, 5), '', ''], mur=R.d('south'))


def hangar_mil(ch, R, L, P):
    """Hangar en demi-lune (toit arrondi), grande porte ouverte, un véhicule dedans."""
    rng = ch.rng
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 63, 0, L - 1, 63, P - 1, S('smooth_stone'))
    r = L / 2.0
    for a in range(L):
        h = int(((r * r - (a + 0.5 - r) ** 2) ** 0.5) * 0.85)
        R.fill(a, 64, 0, a, 64 + h, P - 1, S('green_terracotta' if rng.random() < 0.9 else 'light_gray_terracotta'))
        if h > 0:
            R.vide(a, 64, 1, a, 63 + h, P - 2)
    R.vide(2, 64, P - 1, L - 3, 64 + int(r * 0.6), P - 1)
    x, z = R.xz(L // 2, P // 2)
    if rng.random() < 0.5:
        helicoptere(ch.m, x, z)
    else:
        camion_mil(ch.m, x, z, 'z' if R.d('south') in ('north', 'south') else 'x')
    ch.coffre(R, 2, 64, 2, 'south', SI.LOOT_MILITAIRE)
    ch.lieu(R, L, P, 'hangar', 'Hangar militaire')


def qg(ch, R, L, P):
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 75, P - 1, S('stone_bricks'))
    R.vide(1, 64, 1, L - 2, 75, P - 2)
    for e in range(1, 3):
        R.fill(1, 63 + 4 * e, 1, L - 2, 63 + 4 * e, P - 2, S('spruce_planks'))
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('polished_andesite'))
    R.fill(0, 76, 0, L - 1, 76, P - 1, S('stone_brick_slab', type='bottom'))
    for e in range(3):
        for a in range(2, L - 2, 3):
            R.fill(a, 65 + 4 * e, P - 1, a, 66 + 4 * e, P - 1, S('glass_pane'))
            R.fill(a, 65 + 4 * e, 0, a, 66 + 4 * e, 0, S('glass_pane'))
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'iron')
    for k in range(3):
        ch.coffre(R, 2 + 3 * k, 64, 2, 'south', SI.LOOT_MILITAIRE)
    # mât et drapeau
    R.fill(L // 2 + 4, 64, P + 3, L // 2 + 4, 80, P + 3, S('iron_bars'))
    for k in range(6):
        for h in range(3):
            R.set(L // 2 + 5 + k, 77 + h, P + 3, S('white_wool') if 1 < k < 4 else S('red_wool'))
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 70, z, ['QUARTIER', 'GÉNÉRAL', _nv(ch)[:15], ''], mur=R.d('south'))
    ch.lieu(R, L, P, 'militaire', 'Quartier général de ' + _nv(ch))


def heliport(ch, B):
    m, rng = ch.m, ch.rng
    x1, z1, x2, z2 = B
    m.fill(x1 + 2, 63, z1 + 2, x2 - 2, 63, z2 - 2, S('gray_concrete'))
    pads = [((x1 + x2) // 2, (z1 + z2) // 2)] if x2 - x1 < 60 else [(x1 + 22, (z1 + z2) // 2), (x2 - 22, (z1 + z2) // 2)]
    for (cx, cz) in pads:
        for dx in range(-10, 11):
            for dz in range(-10, 11):
                d = math.hypot(dx, dz)
                if d <= 10:
                    m.set(cx + dx, 63, cz + dz, S('light_gray_concrete'))
                if 9 <= d <= 10:
                    m.set(cx + dx, 63, cz + dz, S('yellow_concrete'))
        m.fill(cx - 3, 63, cz - 4, cx - 2, 63, cz + 4, S('white_concrete'))
        m.fill(cx + 2, 63, cz - 4, cx + 3, 63, cz + 4, S('white_concrete'))
        m.fill(cx - 1, 63, cz, cx + 1, 63, cz, S('white_concrete'))
        if rng.random() < 0.7:
            helicoptere(m, cx, cz)
    # manche à air
    m.fill(x2 - 4, 64, z1 + 4, x2 - 4, 69, z1 + 4, S('iron_bars'))
    m.fill(x2 - 3, 69, z1 + 4, x2 - 1, 69, z1 + 4, S('orange_wool'))
    ch.lieux.append(('heliport', 'Héliport militaire', (x1 + x2) // 2, (z1 + z2) // 2, (x2 - x1) // 2, (z2 - z1) // 2))


def parc_vehicules(ch, B):
    m, rng = ch.m, ch.rng
    x1, z1, x2, z2 = B
    m.fill(x1 + 2, 63, z1 + 2, x2 - 2, 63, z2 - 2, ASPH)
    for z in range(z1 + 7, z2 - 6, 10):
        for x in range(x1 + 8, x2 - 7, 11):
            if rng.random() < 0.8:
                if rng.random() < 0.45:
                    char_assaut(m, x, z, 'x', brule=rng.random() < 0.2)
                else:
                    camion_mil(m, x, z, 'x')
    ch.lieux.append(('parc_vehicules', 'Parc de véhicules blindés', (x1 + x2) // 2, (z1 + z2) // 2, (x2 - x1) // 2,
                     (z2 - z1) // 2))


def depot_munitions(ch, B):
    """Igloos de munitions : buttes de terre, portes d'acier, caisses."""
    m, rng = ch.m, ch.rng
    x1, z1, x2, z2 = B
    for x in range(x1 + 4, x2 - 14, 18):
        for z in range(z1 + 4, z2 - 12, 18):
            for dx in range(13):
                for dz in range(11):
                    h = int(4.5 * (1 - ((dx - 6) / 7.0) ** 2) * (1 - (dz / 12.0) ** 2) + 0.5)
                    if h > 0:
                        m.fill(x + dx, 64, z + dz, x + dx, 63 + h, z + dz, S('dirt'))
                        m.set(x + dx, 63 + h, z + dz, S('grass_block', snowy=False))
            m.vide(x + 4, 64, z, x + 8, 66, z + 7)
            m.fill(x + 3, 64, z, x + 9, 67, z, S('stone_bricks'))
            m.vide(x + 5, 64, z, x + 7, 65, z)
            m.set(x + 5, 64, z, S('iron_door', facing='north', half='lower', hinge='left', open=False, powered=False))
            m.set(x + 5, 65, z, S('iron_door', facing='north', half='upper', hinge='left', open=False, powered=False))
            ch.coffre(ch.R0, x + 6, 64, z + 5, 'north', SI.LOOT_MILITAIRE)
            ch.coffre(ch.R0, x + 4, 64, z + 6, 'north', SI.LOOT_MILITAIRE)
    ch.lieux.append(('armurerie', 'Dépôt de munitions', (x1 + x2) // 2, (z1 + z2) // 2, (x2 - x1) // 2, (z2 - z1) // 2))


def champ_tir(ch, B):
    m, rng = ch.m, ch.rng
    x1, z1, x2, z2 = B
    m.fill(x1 + 2, 63, z1 + 2, x2 - 2, 63, z2 - 2, S('sand'))
    for x in range(x1 + 6, x2 - 4, 6):
        m.fill(x, 64, z2 - 6, x + 2, 64, z2 - 6, S('sandstone_wall', east='low', west='low', north='none', south='none',
                                                   up=False, waterlogged=False))
        m.set(x + 1, 64, z1 + 6, S('hay_block', axis='y'))
        m.set(x + 1, 65, z1 + 6, S('target', power=0))
    m.fill(x1 + 2, 64, z1 + 2, x2 - 2, 67, z1 + 3, S('dirt'))
    ch.lieux.append(('champ_tir', 'Champ de tir', (x1 + x2) // 2, (z1 + z2) // 2, (x2 - x1) // 2, (z2 - z1) // 2))


# ============================================================================ ville universitaire
def pavillon(ch, R, L, P, nom=None):
    """Pavillon universitaire : brique, bandeaux de pierre, portique à colonnes, corniche de cuivre."""
    rng = ch.rng
    et = rng.randint(3, 5)
    top = 63 + 4 * et
    mur = S(rng.choice(['bricks', 'bricks', 'mud_bricks', 'stone_bricks', 'red_terracotta']))
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, top, P - 1, mur)
    R.vide(1, 64, 1, L - 2, top, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('polished_andesite'))
    for e in range(1, et + 1):
        R.fill(1, 63 + 4 * e, 1, L - 2, 63 + 4 * e, P - 2, S('oak_planks'))
        R.fill(0, 63 + 4 * e, 0, L - 1, 63 + 4 * e, 0, S('smooth_sandstone'))
        R.fill(0, 63 + 4 * e, P - 1, L - 1, 63 + 4 * e, P - 1, S('smooth_sandstone'))
    for e in range(et):
        y = 65 + 4 * e
        for a in range(2, L - 2, 2):
            for b in (0, P - 1):
                R.fill(a, y, b, a, y + 1, b, S('glass_pane'))
        for b in range(2, P - 2, 3):
            for a in (0, L - 1):
                R.fill(a, y, b, a, y + 1, b, S('glass_pane'))
        # salle de cours : rangées de pupitres
        for b in range(3, P - 3, 2):
            R.fill(2, y - 1, b, L - 4, y - 1, b, R.S('spruce_stairs', facing='north', half='bottom'))
    cu = rng.choice(['cut_copper', 'exposed_cut_copper', 'weathered_cut_copper', 'oxidized_cut_copper'])
    R.fill(-1, top + 1, -1, L, top + 1, P, S(cu))
    R.fill(0, top + 2, 0, L - 1, top + 2, P - 1, S(cu.replace('cut_copper', 'cut_copper_slab'), type='bottom'))
    # portique
    pa = L // 2
    for a in (pa - 4, pa - 2, pa + 2, pa + 4):
        R.fill(a, 64, P + 2, a, 70, P + 2, S('quartz_pillar', axis='y'))
    R.fill(pa - 5, 71, P, pa + 5, 71, P + 3, S('smooth_quartz'))
    R.fill(pa - 3, 72, P, pa + 3, 72, P + 3, S('smooth_quartz_slab', type='bottom'))
    R.fill(pa - 5, 63, P, pa + 5, 63, P + 3, S('polished_diorite'))
    ZM.porte_double(R, pa - 1, 64, P - 1, 'north', 'dark_oak')
    echelle(R, L - 2, 2, 64, top - 1, mur)
    ch.coffre(R, 2, 64, 2, 'south', SI.LOOT_VILLE)
    nom = nom or 'Pavillon ' + rng.choice(['Marie-Victorin', 'Lionel-Groulx', 'Jean-Brillant', 'Roger-Gaudry',
                                           'Laval', 'De Koninck', 'Desjardins', 'Vachon', 'Pouliot', 'Casault'])
    x, z = R.xz(pa, P + 4)
    ch.panneau(x, 64, z, ['UNIVERSITÉ', nom[:15], nom[15:30], ''], rotation=0)
    ch.lieu(R, L, P, 'universite', nom)


def bibliotheque_u(ch, R, L, P):
    rng = ch.rng
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 75, P - 1, S('stone_bricks'))
    R.vide(1, 64, 1, L - 2, 74, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('dark_oak_planks'))
    for a in range(2, L - 2, 4):
        R.fill(a, 66, P - 1, a + 1, 73, P - 1, S('glass_pane'))
        R.fill(a, 66, 0, a + 1, 73, 0, S('glass_pane'))
    for b in range(3, P - 3, 3):
        R.fill(3, 64, b, L - 4, 66, b, S('bookshelf'))
        R.vide(L // 2 - 1, 64, b, L // 2 + 1, 66, b)
    R.fill(1, 69, 1, L - 2, 69, 3, S('dark_oak_planks'))
    R.fill(1, 70, 4, L - 2, 70, 4, S('dark_oak_fence'))
    # coupole
    cx, cb = L // 2, P // 2
    for k in range(5):
        R.fill(cx - 4 + k, 76 + k, cb - 4 + k, cx + 4 - k, 76 + k, cb + 4 - k, S('oxidized_copper'))
    ZM.porte_double(R, cx - 1, 64, P - 1, 'north', 'dark_oak')
    for k in range(3):
        ch.coffre(R, 2 + 4 * k, 64, P - 3, 'north', SI.LOOT_VILLE)
    x, z = R.xz(cx, P)
    ch.panneau(x, 70, z, ['BIBLIOTHÈQUE', 'des sciences', 'humaines', ''], mur=R.d('south'))
    ch.lieu(R, L, P, 'bibliotheque', 'Bibliothèque de l\'Université de ' + _nv(ch))


def labo_u(ch, R, L, P):
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    for e in range(3):
        y0 = 64 + 5 * e
        R.fill(0, y0, 0, L - 1, y0 + 4, P - 1, S('white_concrete'))
        R.vide(1, y0, 1, L - 2, y0 + 3, P - 2)
        R.fill(1, y0 - 1, 1, L - 2, y0 - 1, P - 2, S('smooth_quartz'))
        for a in range(2, L - 2):
            if a % 4:
                R.fill(a, y0 + 1, P - 1, a, y0 + 3, P - 1, S('light_blue_stained_glass_pane'))
        for a in range(3, L - 5, 6):
            R.fill(a, y0, 4, a + 3, y0, 4, S('smooth_quartz'))
            R.set(a + 1, y0 + 1, 4, S('brewing_stand', has_bottle_0=False, has_bottle_1=False, has_bottle_2=False))
            ch.coffre(R, a + 3, y0, 6, 'north', SI.LOOT_LABO)
        for k in range(5):
            R.set(L - 3, y0 + k, 8 + k, R.S('quartz_stairs', facing='south', half='bottom'))
            R.vide(L - 3, y0 + 4, 8 + k, L - 3, y0 + 4, 8 + k)
    R.fill(0, 79, 0, L - 1, 79, P - 1, S('smooth_stone_slab', type='bottom'))
    ZM.porte_double(R, L // 2 - 1, 64, P - 1, 'north', 'iron')
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 68, z, ['PAVILLON DE', 'VIROLOGIE', 'Partenaire :', 'NORDA Biotech'], mur=R.d('south'), couleur='blue')
    ch.lieu(R, L, P, 'labo_civil', 'Pavillon de virologie')


def tour_horloge(ch, x, z):
    m = ch.m
    m.fill(x - 2, 64, z - 2, x + 2, 88, z + 2, S('stone_bricks'))
    m.vide(x - 1, 64, z - 1, x + 1, 87, z + 1)
    for y in range(64, 88):
        m.set(x, y, z - 1, S('ladder', facing='south', waterlogged=False))
    m.vide(x, 64, z + 2, x, 65, z + 2)
    for (dx, dz) in ((0, -3), (0, 3), (-3, 0), (3, 0)):
        cx, cz = x + dx, z + dz
        for k in (-1, 0, 1):
            for y in (83, 84, 85):
                if dx:
                    m.set(cx, y, cz + k, S('white_concrete'))
                else:
                    m.set(cx + k, y, cz, S('white_concrete'))
        m.set(cx, 84, cz, S('black_concrete'))
        m.set(cx if dx else cx, 85, cz, S('black_concrete'))
    m.vide(x - 2, 89, z - 1, x + 2, 91, z + 1)
    m.vide(x - 1, 89, z - 2, x + 1, 91, z + 2)
    m.fill(x - 2, 89, z - 2, x - 2, 91, z - 2, S('stone_bricks'))
    m.fill(x + 2, 89, z - 2, x + 2, 91, z - 2, S('stone_bricks'))
    m.fill(x - 2, 89, z + 2, x - 2, 91, z + 2, S('stone_bricks'))
    m.fill(x + 2, 89, z + 2, x + 2, 91, z + 2, S('stone_bricks'))
    m.set(x, 90, z, S('bell', attachment='ceiling', facing='north', powered=False))
    m.fill(x - 2, 92, z - 2, x + 2, 92, z + 2, S('oxidized_cut_copper'))
    m.fill(x - 1, 93, z - 1, x + 1, 95, z + 1, S('oxidized_cut_copper'))
    m.fill(x, 96, z, x, 99, z, S('oxidized_cut_copper'))
    m.set(x, 100, z, S('lightning_rod', facing='up', powered=False, waterlogged=False))


def quad(ch, B, v):
    """Le quadrilatère : grande pelouse, allées en croix, ceinture d'arbres, statue du fondateur, tour de l'horloge,
    pavillons tout autour."""
    m, rng = ch.m, ch.rng
    x1, z1, x2, z2 = B
    P = 20
    perimetre(ch, B, P, lambda: (rng.choice((26, 30)), lambda c, R, L, P_: pavillon(c, R, L, P_)), marge=4)
    a1, b1, a2, b2 = x1 + P + 4, z1 + P + 4, x2 - P - 4, z2 - P - 4
    cx, cz = (a1 + a2) // 2, (b1 + b2) // 2
    allee = S('polished_andesite')
    m.fill(a1, 63, cz - 1, a2, 63, cz + 1, allee)
    m.fill(cx - 1, 63, b1, cx + 1, 63, b2, allee)
    n = max(a2 - a1, b2 - b1)
    for k in range(n):
        for (x, z) in ((a1 + k * (a2 - a1) // n, b1 + k * (b2 - b1) // n), (a2 - k * (a2 - a1) // n, b1 + k * (b2 - b1) // n)):
            m.fill(x - 1, 63, z, x + 1, 63, z, allee)
    for x in range(a1, a2 + 1, 9):
        for z in (b1, b2):
            try:
                RU.arbre_rue(ch.R0, x, z, rng, kind='erable')
            except Exception:
                pass
    for x in range(a1 + 6, a2 - 5, 12):
        RU.lampadaire_parc(ch.R0, x, cz + 3)
        RU.banc(ch.R0, x + 3, cz + 3, 'north')
    # statue du fondateur
    m.fill(cx - 2, 63, cz - 2, cx + 2, 64, cz + 2, S('polished_andesite'))
    m.fill(cx, 65, cz, cx, 66, cz, S('stone_bricks'))
    m.set(cx, 67, cz, S('chiseled_stone_bricks'))
    m.set(cx, 68, cz, S('skeleton_skull', rotation=0))
    ch.panneau(cx, 65, cz + 1, ['MGR', 'J.-B. LÉVIS', 'Fondateur', '1878'], mur='south')
    tour_horloge(ch, cx, b1 + 4)
    ch.lieux.append(('parc', 'Le quadrilatère de l\'Université', cx, cz, (a2 - a1) // 2, (b2 - b1) // 2))


# ============================================================================ ville de rivière
def maison_vieille(ch, R, L, P):
    rng = ch.rng
    BA.maison(ch, R, L, P, etages=2 if rng.random() < 0.6 else 1,
              mur=rng.choice(['stone_bricks', 'cobblestone', 'mossy_cobblestone', 'andesite', 'bricks', 'stone']),
              toit=rng.choice(['dark_oak', 'spruce', 'deepslate_tile', 'mangrove']))
    # lucarnes et cheminée
    R.fill(1, 72, P // 2, 1, 75, P // 2, S('bricks'))
    scene_maison(ch, R, L, P)


def capitainerie(ch, R, L, P):
    R.fill(0, 59, 0, L - 1, 63, P - 1, S('stone'))
    R.fill(0, 64, 0, L - 1, 69, P - 1, S('white_terracotta'))
    R.vide(1, 64, 1, L - 2, 68, P - 2)
    R.fill(1, 63, 1, L - 2, 63, P - 2, S('spruce_planks'))
    R.fill(0, 70, 0, L - 1, 70, P - 1, S('red_terracotta'))
    for a in range(2, L - 2, 3):
        R.fill(a, 65, P - 1, a, 66, P - 1, S('glass_pane'))
    # petite tour de guet vitrée
    R.fill(1, 71, 1, 5, 76, 5, S('white_terracotta'))
    R.fill(1, 74, 1, 5, 75, 5, S('glass'))
    R.vide(2, 71, 2, 4, 75, 4)
    R.fill(1, 77, 1, 5, 77, 5, S('red_terracotta'))
    ZM.porte(R, L // 2, 64, P - 1, 'north', 'spruce')
    ch.coffre(R, 2, 64, 2, 'south', SI.LOOT_VILLE)
    x, z = R.xz(L // 2, P)
    ch.panneau(x, 68, z, ['CAPITAINERIE', 'du Vieux-Port', '', ''], mur=R.d('south'))
    ch.lieu(R, L, P, 'port', 'Capitainerie du Vieux-Port')


def quais_port(ch, pv):
    """Le Vieux-Port : pontons de bois dans la rivière devant le quartier du port, bateaux amarrés ou coulés."""
    m, rng = ch.m, ch.rng
    rv = pv['riviere']
    D = pv['S'] // 2
    for q in pv['quartiers']:
        if q['genre'] != 'port':
            continue
        for x in range(max(-D + 8, q['x1'] + 6), min(D - 10, q['x2'] - 6), 15):
            zt, zbn, zc = _bande_eau(pv, x)
            sud = q['cz'] > zc
            z0, sens = (zbn, -1) if sud else (zt, 1)
            longueur = min(14, (zbn - zt) // 3)
            for k in range(longueur):
                z = z0 + sens * k
                m.fill(x, 62, z, x + 2, 62, z, S('spruce_planks'))
                if k % 3 == 0:
                    m.fill(x - 1, 55, z, x - 1, 63, z, S('spruce_fence'))
                    m.fill(x + 3, 55, z, x + 3, 63, z, S('spruce_fence'))
            m.vide(x, 63, z0 - sens * 1, x + 2, 64, z0 - sens * 1)
            # un bateau le long du ponton
            if rng.random() < 0.75:
                bx = x + 5
                coule = rng.random() < 0.35
                yb = 59 if coule else 61
                for k in range(2, 10):
                    z = z0 + sens * k
                    m.fill(bx, yb, z, bx + 2, yb, z, S('spruce_planks'))
                    m.set(bx, yb + 1, z, S('spruce_slab', type='bottom', waterlogged=coule))
                    m.set(bx + 2, yb + 1, z, S('spruce_slab', type='bottom', waterlogged=coule))
                m.set(bx + 1, yb + 1, z0 + sens * 9, S('spruce_planks'))
                if not coule:
                    m.fill(bx + 1, 62, z0 + sens * 5, bx + 1, 66, z0 + sens * 5, S('spruce_fence'))
                    m.fill(bx + 1, 64, z0 + sens * 4, bx + 1, 66, z0 + sens * 4, S('white_wool'))
                    ch.coffre(ch.R0, bx + 1, 62, z0 + sens * 7, 'north', SI.LOOT_VILLE, baril=True)
        ch.lieux.append(('port', 'Le Vieux-Port', q['cx'], q['cz'], (q['x2'] - q['x1']) // 2, (q['z2'] - q['z1']) // 2))


def paves(ch, pv):
    """Rues pavées de la Vieille-Ville (le bitume devient pavés de pierre)."""
    m = ch.m
    D = pv['S'] // 2
    carte = carte_quartiers(pv)
    vieux = np.array([q['genre'] == 'vieux' for q in pv['quartiers']])[carte]
    i_asph = m.id(ASPH)
    ids = [m.id(S(n)) for n in ('cobblestone', 'stone_bricks', 'andesite', 'polished_andesite', 'cobblestone',
                                 'mossy_cobblestone')]
    yl = 63 - m.y0
    a = m.a[yl]
    z0, x0 = -D - m.z0, -D - m.x0
    sub = a[z0:z0 + pv['S'], x0:x0 + pv['S']]
    rs = np.random.default_rng(7)
    k = rs.integers(0, len(ids), sub.shape)
    masque = vieux & (sub == i_asph)
    for i, nid in enumerate(ids):
        sub[masque & (k == i)] = nid


# ============================================================================ scènes posées (bible 34) : ce que les gens ont laissé
HEURE_ARRET = '4 h 12'      # toutes les horloges de la région se sont arrêtées au même moment (Jour 8)


def scene_maison(ch, R, L, P):
    """Une petite scène dans une maison sur trois : le dernier souper, la porte barricadée de l'intérieur, les valises
    prêtes, l'horloge arrêtée, la quarantaine sur la porte. Hasard à part : la ville ne change pas d'un bloc ailleurs."""
    if L < 7 or P < 7:
        return
    graine = ch.site.get('graine', sum(map(ord, ch.site.get('id', ''))))
    rng = ch.__dict__.setdefault('rng_scenes', random.Random(graine + 34))
    m = ch.m
    sort = getattr(ch, 'sort_courant', 'abandon')

    def libre(a, y, b):
        x, z = R.xz(a, b)
        return m.dedans(x, y, z) and m.est_air(x, y, z)

    def poser(a, y, b, st):
        if libre(a, y, b):
            R.set(a, y, b, st)
            return True
        return False
    r = rng.random()
    if r > 0.38:
        return
    pa = L // 2
    choix = rng.choice(['souper', 'barricade', 'valises', 'horloge', 'horloge', 'sang'] +
                       (['quarantaine', 'quarantaine'] if sort == 'quarantaine' else []) +
                       (['valises', 'valises'] if sort == 'evacuee' else []))
    if choix == 'souper':
        # le dernier souper : le gâteau entamé, les bocaux, les chaises repoussées
        R.set(pa, 65, P // 2, S('cake', bites=rng.randint(1, 5)))
        poser(2, 65, 1, S('supplementaries:jar'))
        poser(3, 65, 1, S('candle', candles=2, lit=False, waterlogged=False))
    elif choix == 'barricade':
        # ils se sont enfermés : planches derrière la porte, un mot pour ceux qui viendraient
        for a in (pa - 1, pa, pa + 1):
            for y in (64, 65):
                poser(a, y, P - 2, S('oak_planks'))
        x, z = R.xz(pa, P)
        ch.panneau(x, 66, z, ['NE PAS', 'OUVRIR', 'On est', 'là-dedans.'], mur=R.d('south'))
        if libre(1, 64, 2):
            ch.coffre(R, 1, 64, 2, 'south', SI.LOOT_MAISON)
    elif choix == 'valises':
        # partis à la hâte : sacs et valises près de la porte, jamais pris
        for a, b in ((pa - 2, P - 2), (pa + 2, P - 2), (pa - 2, P - 3)):
            poser(a, 64, b, S('supplementaries:sack', open='false'))
        poser(pa + 2, 64, P - 3, R.S('barrel', facing='up', open=True))
    elif choix == 'horloge':
        # l'horloge de la cuisine, arrêtée à la même minute que toutes les autres
        R.set(0, 66, P // 2, R.S('supplementaries:clock_block', facing='east', two_faced='false'))
        if libre(1, 67, P // 2):
            x, z = R.xz(1, P // 2)
            ch.panneau(x, 67, z, ['Arrêtée à', HEURE_ARRET, 'Jour 8', ''], mur=R.d('east'))
    elif choix == 'sang':
        # une traînée de sang de la porte au lit ; un mot griffonné
        b0 = P - 2
        for k in range(rng.randint(3, 6)):
            poser(pa + rng.choice((-1, 0, 0, 1)), 64, b0 - k, S('redstone_wire', east='none', west='none',
                                                                     north='side', south='side', power=0))
        if libre(1, 66, 1):
            x, z = R.xz(1, 1)
            ch.panneau(x, 66, z, ['AIDEZ-NOUS', '', 'Il a été', 'mordu.'], mur=R.d('south'))
    elif choix == 'quarantaine':
        # ruban jaune sur la façade, avis officiel
        for a in range(0, L):
            x, z = R.xz(a, P)
            if m.dedans(x, 65, z) and m.est_air(x, 65, z):
                m.set(x, 65, z, S('yellow_stained_glass_pane'))
        x, z = R.xz(pa + 2, P)
        ch.panneau(x, 66, z, ['QUARANTAINE', 'Ne pas entrer', 'Santé Québec', 'Jour 6'], mur=R.d('south'))


def chantier(ch, B):
    """Chantier : une tour en construction (ossature de béton, échafaudages), sa grue, sa clôture de chantier."""
    m, rng = ch.m, ch.rng
    x1, z1, x2, z2 = B
    m.fill(x1 + 2, 63, z1 + 2, x2 - 2, 63, z2 - 2, S('coarse_dirt'))
    L, P = min(26, x2 - x1 - 24), min(24, z2 - z1 - 10)
    ox, oz = x1 + 4, z1 + 4
    et = rng.randint(6, 10)
    for e in range(et + 1):
        y = 63 + 4 * e
        if e < et:
            m.fill(ox, y, oz, ox + L - 1, y, oz + P - 1, S('light_gray_concrete'))
        for (a, b) in ((0, 0), (L - 1, 0), (0, P - 1), (L - 1, P - 1), (L // 2, 0), (L // 2, P - 1), (0, P // 2),
                       (L - 1, P // 2)):
            if e < et:
                m.fill(ox + a, y + 1, oz + b, ox + a, y + 3, oz + b, S('gray_concrete'))
            else:
                m.fill(ox + a, y + 1, oz + b, ox + a, y + 1 + rng.randint(0, 3), oz + b, S('iron_bars'))
    # échafaudages sur la façade
    for y in range(64, 63 + 4 * et, 2):
        for a in range(0, L):
            if a % 3 == 0:
                m.set(ox + a, y, oz + P, S('scaffolding', bottom=False, distance=0, waterlogged=False))
    for k in range(4 * et):
        m.set(ox - 1, 64 + k, oz + 2, S('ladder', facing='west', waterlogged=False))
    VB.grue(ch, min(x2 - 8, ox + L + 8), oz + P // 2)
    # palissade de chantier
    for x in range(x1 + 1, x2):
        for z in (z1 + 1, z2 - 1):
            m.fill(x, 64, z, x, 65, z, S('white_concrete'))
    for z in range(z1 + 1, z2):
        for x in (x1 + 1, x2 - 1):
            m.fill(x, 64, z, x, 65, z, S('white_concrete'))
    m.vide((x1 + x2) // 2 - 2, 64, z2 - 1, (x1 + x2) // 2 + 2, 65, z2 - 1)
    ch.panneau((x1 + x2) // 2 + 3, 66, z2, ['CHANTIER', 'Tour ' + _nv(ch)[:10], 'Livraison', 'printemps'], mur='south')
    for _ in range(4):
        x, z = rng.randint(x1 + 4, x2 - 4), rng.randint(z1 + 4, z2 - 4)
        if m.est_air(x, 64, z):
            m.set(x, 64, z, rng.choice([S('smooth_stone_slab', type='bottom'), S('iron_bars'), S('barrel', facing='up',
                                                                                                  open=False)]))
    ch.lieux.append(('chantier', 'Chantier de construction', ox + L // 2, oz + P // 2, (x2 - x1) // 2, (z2 - z1) // 2))


# ============================================================================ recettes d'îlots (le rythme d'un quartier)
def recettes(ch, b, q, uniques, v):
    """Choisit et pose la recette d'un îlot. b : îlot ; q : quartier ; uniques : bâtiments déjà posés dans la ville."""
    rng = ch.rng
    ch.sort_courant = q['sort']
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
            scene_maison(c, R, L, P)
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
    if g in ('centre', 'affaires') and petit >= 54 and W >= 60 and unique('chantier'):
        chantier(ch, B)
        return
    if g in ('civique', 'centre', 'affaires') and petit >= 56 and unique('parking'):
        VB.parking_etage(ch, B)
        return
    if g in ('residentiel', 'banlieue', 'pauvre', 'logements') and petit >= 50 and unique('ecole_' + q['id']):
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
    # ---- ville de garnison
    if g == 'base':
        cloture_base(ch, b)
        Bi = (B[0] + 2, B[1] + 2, B[2] - 2, B[3] - 6)
        Wi, Hi = Bi[2] - Bi[0] + 1, Bi[3] - Bi[1] + 1
        if min(Wi, Hi) >= 44 and unique('qg'):
            qg(ch, lot(ch, Bi, 'south', Bi[0] + (Wi - 30) // 2, 30, 18), 30, 18)
            if Hi >= 70:
                heliport(ch, (Bi[0], Bi[1], Bi[2], Bi[3] - 24))
            return
        r = rng.random()
        if min(Wi, Hi) >= 40 and unique('heliport'):
            heliport(ch, Bi)
        elif r < 0.3:
            parc_vehicules(ch, Bi)
        elif r < 0.5 and min(Wi, Hi) >= 30 and unique('munitions'):
            depot_munitions(ch, Bi)
        elif r < 0.62 and min(Wi, Hi) >= 36 and unique('tir'):
            champ_tir(ch, Bi)
        elif r < 0.82 and Hi >= 30:
            for s_ in range(Bi[0] + 2, Bi[2] - 25, 30):
                hangar_mil(ch, ch.rep(s_, Bi[1] + 2, 'south'), 26, min(34, Hi - 6))
        else:
            perimetre(ch, Bi, 12, lambda: (rng.choice((22, 26)), lambda c, R, L, P: caserne_mil(c, R, L, P)),
                      cotes=('north', 'south'))
            VB.cour(ch, Bi, 12, 'centre')
        return
    if g == 'logements':
        mur, toit = rng.choice([('white_terracotta', 'dark_oak'), ('light_gray_concrete', 'spruce'),
                                ('smooth_sandstone', 'dark_oak'), ('white_concrete', 'deepslate_tile')])
        perimetre(ch, B, 10, lambda: (9, lambda c, R, L, P: (BA.maison(c, R, L, P, etages=1, mur=mur, toit=toit),
                                                              scene_maison(c, R, L, P))))
        cour_(10, 'banlieue')
        return
    # ---- ville universitaire
    if g == 'campus':
        if petit >= 76 and unique('quad'):
            quad(ch, B, v)
            return
        if petit >= 44 and W >= 44 and unique('bibliotheque'):
            bibliotheque_u(ch, lot(ch, B, 'south', B[0] + (W - 36) // 2, 36, 26), 36, 26)
            perimetre(ch, B, 18, lambda: (rng.choice((24, 28)), lambda c, R, L, P: pavillon(c, R, L, P)), cotes=('north',))
            return
        if petit >= 40 and W >= 40 and unique('labo_u'):
            labo_u(ch, lot(ch, B, 'north', B[0] + 4, 30, 22), 30, 22)
            perimetre(ch, B, 16, lambda: (rng.choice((24, 28)), lambda c, R, L, P: pavillon(c, R, L, P)), cotes=('south',))
            return
        if petit >= 56 and unique('stade_' + v['id']):
            stade(ch, B, 'du Rouge et Or')
            return
        if rng.random() < 0.65:
            perimetre(ch, B, 18, lambda: (rng.choice((24, 28, 32)), lambda c, R, L, P: pavillon(c, R, L, P)), marge=4)
            cour_(18, 'banlieue')
        else:
            perimetre(ch, B, 14, immeubles(5, 7, 0.0))
            cour_(14, 'banlieue')
        return
    # ---- ville de rivière
    if g == 'vieux':
        if petit >= 50 and unique('eglise_vieux'):
            Re = lot(ch, B, 'north', B[0] + W // 2 - 8, 17, 27)
            BA.eglise(ch, Re, 17, 27)
            ch.lieu(Re, 17, 27, 'eglise', 'Basilique Saint-Jacques')
            VB.place(ch, (B[0], B[1] + 30, B[2], B[3]), 'du Marché')
            return
        perimetre(ch, B, 10, lambda: (rng.choice((7, 8, 9)), lambda c, R, L, P: maison_vieille(c, R, L, P)))
        cour_(10, 'banlieue')
        return
    if g == 'port':
        if petit >= 30 and W >= 30 and unique('capitainerie'):
            capitainerie(ch, lot(ch, B, 'north', B[0] + 4, 16, 12), 16, 12)
            perimetre(ch, B, 16, lambda: (rng.choice((20, 24)), lambda c, R, L, P: VB.entrepot(c, R, L, P)),
                      cotes=('south',))
            return
        perimetre(ch, B, 16, lambda: (rng.choice((20, 24)), lambda c, R, L, P: VB.entrepot(c, R, L, P)),
                  cotes=('north', 'south'))
        VB.conteneurs(ch, (B[0] + 4, B[1] + 20, B[2] - 4, B[3] - 20), max(2, W * H // 900))
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
    if s == 'brulee':
        # cendres au sol (Supplementaries)
        for _ in range(n * 40):
            x, z = rng.randint(x1, x2), rng.randint(z1, z2)
            if libre(x, z):
                m.set(x, 64, z, S('supplementaries:ash', layers=str(rng.randint(1, 3))))
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
                # mât et drapeau de la faction (Supplementaries)
                m.fill(x, 64, z, x, 67, z, S('spruce_fence', waterlogged=False))
                if m.est_air(x + 1, 67, z):
                    m.set(x + 1, 67, z, S('supplementaries:flag_green'))
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
    if pv.get('aerienne'):
        autoroute_aerienne(ch, pv, v)
    if pv.get('riviere'):
        quais_port(ch, pv)
    if any(q['genre'] == 'vieux' for q in pv['quartiers']):
        paves(ch, pv)
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
    if 'y' in v:
        return v['y']
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
                s = {'id': '%s_t%d%d' % (v['id'], i, j), 'type': 'ville_tuile', 'nom': v['nom'],
                     'x': v['x'] + (i - (n - 1) / 2) * TUILE, 'z': v['z'] + (j - (n - 1) / 2) * TUILE,
                     'larg': TUILE, 'prof': TUILE, 'y': y, 'ville': v['id'], 'ti': i, 'tj': j, 'bible': True}
                if TYPES[v['type']].get('riviere'):
                    s['garder_riviere'] = True    # terrain : on n'assèche pas la rivière autour de la ville
                out.append(s)
    for s in out:
        s['x'], s['z'] = int(s['x']), int(s['z'])
    return out


def routes_du_plan():
    """Les routes qui relient chaque ville au réseau, puis l'autoroute 20 -> [(nom, genre, points)]."""
    out = []
    for v in VILLES:
        if not v.get('sortie'):
            continue
        D = v['n'] * TUILE // 2
        cote, pts, nom = v['sortie'][:3]
        dec = v['sortie'][3] if len(v['sortie']) > 3 else 0
        dep = {'est': (v['x'] + D, v['z'] + dec), 'ouest': (v['x'] - D, v['z'] + dec),
               'nord': (v['x'] + dec, v['z'] - D), 'sud': (v['x'] + dec, v['z'] + D)}[cote]
        out.append((nom, 'route', [dep] + pts))
    for nom, pts in AUTOROUTES:
        out.append((nom, 'autoroute', pts))
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
