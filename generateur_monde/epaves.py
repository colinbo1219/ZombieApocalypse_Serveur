# -*- coding: utf-8 -*-
"""epaves : événements sur les routes, posés à la hauteur réelle de la chaussée.

  * carambolages : 8 à 14 voitures en travers des voies, certaines brûlées, portières ouvertes, débris ;
  * l'exode : bouchon de 200 blocs sur l'autoroute 40 en direction de Montréal (ouest), voitures abandonnées en file ;
  * convois militaires : camions verts, sacs de sable, caisses (butin militaire), panneau de l'armée.
Les positions sont calculées une fois depuis le plan (déterministes), chaque région pose ce qui tombe chez elle.
"""
import math
import random

import numpy as np

import terrain as T

COULEURS = ['red', 'blue', 'white', 'black', 'gray', 'light_gray', 'green', 'brown', 'cyan', 'yellow']


def _route(plan, nom):
    return next(r for r in plan['routes'] if r['nom'] == nom)


def _le_long(r, s):
    """Point et direction unitaire à l'abscisse curviligne s (en blocs) le long de la route."""
    P = r['points']
    acc = 0.0
    for i in range(len(P) - 1):
        (x1, z1), (x2, z2) = P[i], P[i + 1]
        d = math.hypot(x2 - x1, z2 - z1)
        if acc + d >= s or i == len(P) - 2:
            t = 0 if d == 0 else max(0.0, min(1.0, (s - acc) / d))
            return x1 + (x2 - x1) * t, z1 + (z2 - z1) * t, (x2 - x1) / (d or 1), (z2 - z1) / (d or 1)
        acc += d
    return P[-1][0], P[-1][1], 1.0, 0.0


def _longueur(r):
    P = r['points']
    return sum(math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]) for i in range(len(P) - 1))


def _cardinal(dx, dz):
    if abs(dx) >= abs(dz):
        return 'east' if dx > 0 else 'west'
    return 'south' if dz > 0 else 'north'


def _loin_des_sites(plan, x, z, marge=120):
    for s in plan['sites']:
        if abs(s['x'] - x) < s['larg'] / 2 + marge and abs(s['z'] - z) < s['prof'] / 2 + marge:
            return False
    return abs(x) < plan['limite'] - 150 and abs(z) < plan['limite'] - 150


def evenements(plan):
    """-> liste d'événements {type, nom, x, z, dx, dz, objets:[...]} (coordonnées absolues)."""
    rng = random.Random(plan['graine'] + 77)
    a40, r117 = _route(plan, 'Autoroute 40'), _route(plan, 'Route 117')
    out = []

    def carambolage(r, s, nom, voies):
        x, z, ux, uz = _le_long(r, s)
        nx, nz = -uz, ux
        objs = []
        for k in range(rng.randint(8, 14)):
            t = rng.uniform(-30, 30)
            o = rng.choice(voies) + rng.uniform(-1.0, 1.0)
            cx, cz = x + ux * t + nx * o, z + uz * t + nz * o
            # en travers : direction au hasard autour de celle de la route
            d = _cardinal(ux, uz) if rng.random() < 0.5 else rng.choice(['north', 'south', 'east', 'west'])
            kind = 'brulee' if rng.random() < 0.3 else rng.choice(['auto', 'auto', 'taxi'])
            objs.append(('voiture', round(cx), round(cz), d, rng.choice(COULEURS), kind, rng.random() < 0.5))
        for k in range(rng.randint(10, 20)):
            t, o = rng.uniform(-35, 35), rng.uniform(-7, 7)
            objs.append(('debris', round(x + ux * t + nx * o), round(z + uz * t + nz * o),
                         rng.choice(['gravel', 'andesite', 'coal_block', 'iron_bars', 'cobweb'])))
        # panneau d'avertissement 60 blocs avant, dans chaque sens
        for sg in (-1, 1):
            px, pz = x + ux * 60 * sg - nx * (r['largeur'] / 2 + 2) * sg, z + uz * 60 * sg - nz * (r['largeur'] / 2 + 2) * sg
            objs.append(('panneau', round(px), round(pz), _cardinal(ux * sg, uz * sg),
                         ['ACCIDENT', 'Voies bloquées', '', 'Contournez']))
        out.append({'type': 'carambolage', 'nom': nom, 'x': round(x), 'z': round(z), 'dx': 40, 'dz': 40, 'objets': objs})

    def exode(r, s, longueur):
        # la file vers l'ouest (points de la 40 d'ouest en est : on descend les abscisses)
        objs = []
        x0, z0, ux, uz = _le_long(r, s)
        nx, nz = -uz, ux
        k = 0.0
        while k < longueur:
            for o in (-5, -2):                        # voies en direction ouest (côté nord de la chaussée)
                if rng.random() < 0.8:
                    x, z, ux2, uz2 = _le_long(r, s - k - rng.uniform(0, 2))
                    cx, cz = x + (-uz2) * o, z + ux2 * o
                    kind = 'brulee' if rng.random() < 0.08 else rng.choice(['auto', 'auto', 'auto', 'taxi'])
                    objs.append(('voiture', round(cx), round(cz), _cardinal(-ux2, -uz2), rng.choice(COULEURS), kind,
                                 rng.random() < 0.6))
            k += rng.uniform(7, 10)
        xm, zm, _, _ = _le_long(r, s - longueur / 2)
        objs.append(('panneau', round(x0 + nx * 10), round(z0 + nz * 10), _cardinal(ux, uz),
                     ['MONTRÉAL', '← 190 km', 'ÉVACUATION', 'Voies ouest']))
        out.append({'type': 'exode', 'nom': "L'exode — bouchon de l'autoroute 40", 'x': round(xm), 'z': round(zm),
                    'dx': longueur // 2 + 10, 'dz': 25, 'objets': objs})

    def convoi(r, s, nom):
        x, z, ux, uz = _le_long(r, s)
        nx, nz = -uz, ux
        objs = []
        for k in range(4):
            t = -18 + k * 11 + rng.uniform(-1, 1)
            objs.append(('camion', round(x + ux * t + nx * 2), round(z + uz * t + nz * 2), _cardinal(ux, uz)))
            objs.append(('caisse', round(x + ux * (t - 4) + nx * 5), round(z + uz * (t - 4) + nz * 5)))
        for k in range(-3, 4):
            objs.append(('sac', round(x + ux * 26 + nx * k), round(z + uz * 26 + nz * k)))
        objs.append(('panneau', round(x + ux * 30 + nx * 6), round(z + uz * 30 + nz * 6), _cardinal(ux, uz),
                     ['FORCES ARMÉES', 'Convoi B-7', 'NE PAS', 'APPROCHER']))
        out.append({'type': 'convoi', 'nom': nom, 'x': round(x), 'z': round(z), 'dx': 40, 'dz': 40, 'objets': objs})

    L40 = _longueur(a40)
    # l'exode : entre Saint-Aurèle et l'ouest de la carte
    exode(a40, L40 * 0.40, 200)
    # carambolages sur la 40 et la 117, loin des lieux
    for (r, n, noms, voies) in ((a40, 6, "Carambolage de l'autoroute 40", (-5, -2, 2, 5)),
                                (r117, 3, 'Carambolage de la route 117', (-2, 2))):
        L = _longueur(r)
        faits, essais = 0, 0
        while faits < n and essais < 200:
            essais += 1
            s = rng.uniform(300, L - 300)
            x, z, _, _ = _le_long(r, s)
            if _loin_des_sites(plan, x, z) and all(math.hypot(x - e['x'], z - e['z']) > 600 for e in out):
                carambolage(r, s, noms, voies)
                faits += 1
    # convois militaires : sur la 40 à l'ouest (vers la base Bravo) et sur la 117 au nord
    for (r, frac, nom) in ((a40, 0.2, 'Convoi militaire abandonné (autoroute 40)'),
                           (r117, 0.3, 'Convoi militaire abandonné (route 117)'),
                           (a40, 0.75, 'Convoi militaire abandonné (autoroute 40 est)')):
        L = _longueur(r)
        for essai in range(40):
            s = L * frac + essai * 37
            x, z, _, _ = _le_long(r, s)
            if _loin_des_sites(plan, x, z, 80) and all(math.hypot(x - e['x'], z - e['z']) > 300 for e in out):
                convoi(r, s, nom)
                break
    return out


# ============================================================================ pose dans une région
class _Collecte:
    def __init__(self):
        self.blocs = []

    def set(self, x, y, z, st):
        self.blocs.append((x, y, z, st))


def _hauteur(plan, x, z, cache):
    k = (x, z)
    if k not in cache:
        c = T.champ(plan, np.array([[float(x)]]), np.array([[float(z)]]))
        cache[k] = int(c['route_y'][0, 0]) if c['route'][0, 0] else int(c['h'][0, 0])
    return cache[k]


def _camion(x, z, d, y):
    """Camion militaire 3 x 7 : cabine vert foncé, benne bâchée."""
    ux, uz = {'east': (1, 0), 'west': (-1, 0), 'south': (0, 1), 'north': (0, -1)}[d]
    nx, nz = -uz, ux
    b = []
    for a in range(-3, 4):
        for c in (-1, 0, 1):
            px, pz = x + ux * a + nx * c, z + uz * a + nz * c
            roue = a in (-2, 2) and c != 0
            b.append((px, y, pz, 'minecraft:black_concrete' if roue else 'minecraft:green_terracotta'))
            if a >= 2:
                b.append((px, y + 1, pz, 'minecraft:black_stained_glass' if a == 3 else 'minecraft:green_terracotta'))
            else:
                b.append((px, y + 1, pz, 'minecraft:green_wool'))
                b.append((px, y + 2, pz, 'minecraft:green_wool' if c != 0 or a in (-3, 1) else 'minecraft:air'))
    return b


def poser(reg, evts):
    import monde as M
    import sites as SI
    import za_rue as RU
    cache = {}
    x1, z1 = reg.x0 + M.N, reg.z0 + M.N

    def dedans(x, z, r=8):
        return reg.x0 - r <= x < x1 + r and reg.z0 - r <= z < z1 + r

    for e in evts:
        if not dedans(e['x'], e['z'], e['dx'] + 70):
            continue
        for o in e['objets']:
            kind, x, z = o[0], o[1], o[2]
            if not dedans(x, z):
                continue
            y = _hauteur(reg.plan, x, z, cache) + 1
            if kind == 'voiture':
                col = _Collecte()
                try:
                    RU.voiture(col, x, z, o[3], o[4], y, o[5], portes=o[6])
                except Exception:
                    continue
                for (bx, by, bz, st) in col.blocs:
                    reg.poser(bx, by, bz, st if isinstance(st, str) else str(st))
            elif kind == 'camion':
                for (bx, by, bz, st) in _camion(x, z, o[3], y):
                    reg.poser(bx, by, bz, st)
            elif kind == 'caisse':
                reg.poser(x, y, z, 'minecraft:barrel[facing=up,open=false]')
                reg.entite(x, y, z, SI.entite_conteneur('minecraft:barrel', None, SI.LOOT_MILITAIRE))
            elif kind == 'sac':
                reg.poser(x, y, z, 'minecraft:sandstone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]')
            elif kind == 'debris':
                if o[3] == 'cobweb' or o[3] == 'iron_bars':
                    reg.poser(x, y, z, 'minecraft:' + o[3] if o[3] == 'cobweb' else
                              'minecraft:iron_bars[east=false,north=false,south=false,waterlogged=false,west=false]')
                else:
                    reg.poser(x, y - 1, z, 'minecraft:' + o[3])
            elif kind == 'panneau':
                d = o[3]
                reg.poser(x, y, z, 'minecraft:spruce_fence[east=false,north=false,south=false,waterlogged=false,west=false]')
                reg.poser(x, y + 1, z, 'minecraft:orange_concrete')
                fx, fz = {'east': (1, 0), 'west': (-1, 0), 'south': (0, 1), 'north': (0, -1)}[d]
                reg.poser(x + fx, y + 1, z + fz, 'minecraft:spruce_wall_sign[facing=%s,waterlogged=false]' % d)
                reg.entite(x + fx, y + 1, z + fz, SI.entite_panneau({'front': o[4], 'color': 'black'}))
