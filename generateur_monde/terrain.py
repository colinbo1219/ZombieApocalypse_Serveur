# -*- coding: utf-8 -*-
"""terrain : relief, eau, biomes, routes et emprises des sites, calculés sur des grilles de colonnes (x, z).

champ(plan, X, Z) -> dict de tableaux de même forme que X :
  h        : hauteur du dernier bloc solide (int)
  eau      : niveau de l'eau (int) ou -999 s'il n'y a pas d'eau au-dessus de h
  biome    : indice dans BIOMES
  route    : 0 = rien, 1 = autoroute, 2 = route, 3 = rang (gravier), 4 = accotement ; route_y : hauteur de la chaussée
  pont     : vrai là où une route passe au-dessus de l'eau (tablier à route_y)
  site     : indice du site (dans plan['sites']) + 1, 0 = aucun
  pente    : pente locale (blocs / bloc)
Tout est une fonction pure des coordonnées : les régions se raccordent sans couture.
"""
import math

import numpy as np

import bruit as B

BIOMES = ['minecraft:plains', 'minecraft:forest', 'minecraft:birch_forest', 'minecraft:taiga',
          'minecraft:old_growth_spruce_taiga', 'minecraft:grove', 'minecraft:snowy_slopes', 'minecraft:river',
          'minecraft:swamp', 'minecraft:meadow', 'minecraft:old_growth_birch_forest']
BI = {b.split(':')[1]: i for i, b in enumerate(BIOMES)}
G = 1250


# ============================================================================ relief de base
def base(X, Z):
    """Relief naturel avant rivière, lacs, sites et routes."""
    h = 72 + 12 * B.fbm(X, Z, 1 / 700, G, 4) + 5 * B.fbm(X, Z, 1 / 160, G + 7, 3)
    # Laurentides au nord : lisière irrégulière
    lis = -1400 + 500 * B.fbm(X, Z, 1 / 1500, G + 3, 2)
    m = B.lisse_pas(lis, lis - 1800, Z)
    rid = B.crete(X, Z, 1 / 520, G + 11, 4)
    h = h + m * (22 + 105 * rid)
    # plaines agricoles au sud
    p = B.lisse_pas(1300, 2700, Z) * (1 - m)
    h = h * (1 - 0.72 * p) + (66 + 3 * B.fbm(X, Z, 1 / 300, G + 13, 2)) * 0.72 * p
    # cuvette douce autour de Saint-Aurèle
    d = np.hypot(X, Z)
    c = B.lisse_pas(1100, 350, d)
    h = h * (1 - 0.8 * c) + 66 * 0.8 * c
    return h, m, p


def niveau_lac(lac):
    _, lx, lz, lr = lac
    h, _, _ = base(np.array([float(lx)]), np.array([float(lz)]))
    return int(max(62, min(150, round(float(h[0]) - 4))))


# ============================================================================ distances à des polylignes
def distance_polyligne(X, Z, pts, marge):
    """-> (distance min, abscisse curviligne au point le plus proche, largeur interpolée si pts a 3 composantes)"""
    P = np.asarray(pts, np.float64)
    xmin, xmax, zmin, zmax = X.min() - marge, X.max() + marge, Z.min() - marge, Z.max() + marge
    dmin = np.full(X.shape, 1e9)
    smin = np.zeros(X.shape)
    lmin = np.zeros(X.shape)
    cum = np.concatenate([[0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])
    for i in range(len(P) - 1):
        x1, z1, x2, z2 = P[i, 0], P[i, 1], P[i + 1, 0], P[i + 1, 1]
        if max(x1, x2) < xmin or min(x1, x2) > xmax or max(z1, z2) < zmin or min(z1, z2) > zmax:
            continue
        dx, dz = x2 - x1, z2 - z1
        L2 = dx * dx + dz * dz or 1e-9
        t = np.clip(((X - x1) * dx + (Z - z1) * dz) / L2, 0, 1)
        d = np.hypot(X - (x1 + t * dx), Z - (z1 + t * dz))
        m = d < dmin
        if m.any():
            dmin = np.where(m, d, dmin)
            smin = np.where(m, cum[i] + t * math.sqrt(L2), smin)
            if P.shape[1] > 2:
                lmin = np.where(m, P[i, 2] + (P[i + 1, 2] - P[i, 2]) * t, lmin)
    return dmin, smin, lmin


# ============================================================================ sites et profils de routes (mis en cache)
_CACHE = {}


def y_site(s):
    if 'y' in s:
        return s['y']
    k = ('site', s['id'])
    if k not in _CACHE:
        xs = np.linspace(s['x'] - s['larg'] / 2, s['x'] + s['larg'] / 2, 7)
        zs = np.linspace(s['z'] - s['prof'] / 2, s['z'] + s['prof'] / 2, 7)
        X, Z = np.meshgrid(xs, zs)
        h, _, _ = base(X, Z)
        _CACHE[k] = int(max(64, round(float(np.median(h)))))
    return _CACHE[k]


def profil_route(plan, r):
    """Hauteur de chaussée le long de la route (tous les 4 blocs), lissée ; ponts au-dessus de l'eau."""
    k = ('route', r['nom'])
    if k in _CACHE:
        return _CACHE[k]
    P = np.asarray(r['points'], np.float64)
    cum = np.concatenate([[0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])
    s = np.arange(0, cum[-1] + 4, 4.0)
    xs = np.interp(s, cum, P[:, 0])
    zs = np.interp(s, cum, P[:, 1])
    c = champ(plan, xs, zs, routes=False)
    h = c['h'].astype(np.float64)
    eau = c['eau'] > -999
    # sur l'eau : tablier au-dessus du niveau de l'eau
    h = np.where(eau, np.maximum(c['eau'] + 4, h), h)
    # lissage (moyenne glissante ~60 blocs), pente limitée à 1/5
    k15 = 15
    pad = np.pad(h, k15, mode='edge')
    lisse = np.convolve(pad, np.ones(2 * k15 + 1) / (2 * k15 + 1), mode='same')[k15:-k15]
    y = np.round(lisse)
    for i in range(1, len(y)):
        y[i] = min(max(y[i], y[i - 1] - 0.8), y[i - 1] + 0.8)
    for i in range(len(y) - 2, -1, -1):
        y[i] = min(max(y[i], y[i + 1] - 0.8), y[i + 1] + 0.8)
    y = np.maximum(y, 63)
    _CACHE[k] = (s, np.round(y), eau)
    return _CACHE[k]


# ============================================================================ le champ complet
def champ(plan, X, Z, routes=True):
    X = np.asarray(X, np.float64)
    Z = np.asarray(Z, np.float64)
    h, m, p = base(X, Z)
    eau = np.full(X.shape, -999.0)
    marge = 400
    # ---------------------------------------------------------------- rivière Blanche
    d, _, w = distance_polyligne(X, Z, plan['riviere'], marge)
    v = B.lisse_pas(w + 160, w + 6, d)
    h = h - (h - 64.5) * v * 0.9 * (1 - m)
    lit = d < w
    prof = 3 + 8 * (1 - np.clip(d / np.maximum(w, 1), 0, 1) ** 2)
    h = np.where(lit, np.minimum(h, plan['mer'] - prof), h)
    eau = np.where(lit, plan['mer'], eau)
    riv = lit
    # ---------------------------------------------------------------- lacs (niveau propre à chaque lac)
    for lac in plan['lacs']:
        _, lx, lz, lr = lac
        if np.hypot(np.clip(lx, X.min(), X.max()) - lx, np.clip(lz, Z.min(), Z.max()) - lz) > lr * 1.5 + 120:
            continue
        niv = niveau_lac(lac)
        r = lr * (1 + 0.28 * B.fbm(X, Z, 1 / 140, G + 17 + int(lx), 3))
        dl = np.hypot(X - lx, Z - lz)
        rive = B.lisse_pas(r + 90, r, dl)
        h = h - (h - (niv + 2)) * rive * 0.85
        dedans = dl < r
        prof = 2 + 11 * (1 - np.clip(dl / r, 0, 1) ** 2)
        h = np.where(dedans, np.minimum(h, niv - prof), h)
        eau = np.where(dedans, niv, eau)
    # ---------------------------------------------------------------- sites : terrain aplani
    site = np.zeros(X.shape, np.int32)
    for i, s in enumerate(plan['sites']):
        demi_l, demi_p = s['larg'] / 2 + 3, s['prof'] / 2 + 3
        if abs(np.clip(s['x'], X.min(), X.max()) - s['x']) > demi_l + 60 or abs(np.clip(s['z'], Z.min(), Z.max()) - s['z']) > demi_p + 60:
            continue
        dx = np.maximum(np.abs(X - s['x']) - demi_l, 0)
        dz = np.maximum(np.abs(Z - s['z']) - demi_p, 0)
        dr = np.hypot(dx, dz)
        dedans = dr == 0
        site = np.where(dedans, i + 1, site)
        if s.get('aplanir', True):
            ys = y_site(s)
            wgt = B.lisse_pas(48, 0, dr)
            h = h * (1 - wgt) + ys * wgt
            h = np.where(dedans, ys, h)
            eau = np.where(dedans, -999, eau)
    # ---------------------------------------------------------------- routes
    route = np.zeros(X.shape, np.int8)
    route_y = np.zeros(X.shape)
    route_d = np.zeros(X.shape)       # distance à l'axe de la route (marquage)
    route_s = np.zeros(X.shape)       # abscisse le long de la route (pointillés, piliers)
    route_l = np.zeros(X.shape)       # demi-largeur de la route
    pont = np.zeros(X.shape, bool)
    if routes:
        code = {'autoroute': 1, 'route': 2, 'rang': 3}
        best = np.full(X.shape, 1e9)
        for r in plan['routes']:
            dr, sr, _ = distance_polyligne(X, Z, r['points'], 80)
            if not (dr < r['largeur'] / 2 + 12).any():
                continue
            s_p, y_p, eau_p = profil_route(plan, r)
            ry = np.interp(sr, s_p, y_p)
            demi = r['largeur'] / 2
            proche = dr < demi + 12
            # talus : la route impose sa hauteur sur ~8 blocs de chaque côté (hors eau)
            wgt = B.lisse_pas(demi + 9, demi, dr)
            sur_eau = eau > -999
            h = np.where(proche & ~sur_eau, h * (1 - wgt) + ry * wgt, h)
            chaussee = (dr <= demi) & (dr < best)
            best = np.where(chaussee, dr, best)
            route = np.where(chaussee, code[r['genre']], route)
            route_d = np.where(chaussee, dr, route_d)
            route_s = np.where(chaussee, sr, route_s)
            route_l = np.where(chaussee, demi, route_l)
            route = np.where((dr > demi) & (dr <= demi + 1.5) & (route == 0) & (r['genre'] != 'rang'), 4, route)
            route_y = np.where(chaussee | ((route == 4) & (dr <= demi + 1.5)), ry, route_y)
            pont = np.where(chaussee & sur_eau, True, pont)
            pont = np.where(chaussee & ~sur_eau, False, pont)
            h = np.where(chaussee & ~sur_eau, ry, h)
    hi = np.floor(h).astype(np.int32)
    # ---------------------------------------------------------------- biomes
    t = B.fbm(X, Z, 1 / 800, G + 23, 3)
    bio = np.full(X.shape, BI['forest'], np.uint8)
    bio = np.where(t < -0.22, BI['taiga'], bio)
    bio = np.where(t > 0.30, BI['birch_forest'], bio)
    bio = np.where(t > 0.55, BI['old_growth_birch_forest'], bio)
    # lisières bruitées (pas de frontière en ligne droite)
    pn = p + 0.38 * B.fbm(X, Z, 1 / 650, G + 31, 3)
    mn = m + 0.3 * B.fbm(X, Z, 1 / 600, G + 37, 3)
    bio = np.where(pn > 0.5, np.where(B.fbm(X, Z, 1 / 400, G + 29, 2) > 0.35, BI['meadow'], BI['plains']), bio)
    bio = np.where(mn > 0.3, np.where(t < 0.1, BI['old_growth_spruce_taiga'], BI['taiga']), bio)
    bio = np.where((mn > 0.45) & (hi > 150 + 6 * t), BI['grove'], bio)
    bio = np.where((m > 0.5) & (hi > 172 + 5 * t), BI['snowy_slopes'], bio)
    marais = np.hypot(X + 3550, Z - 2850) < 430 * (1 + 0.3 * B.fbm(X, Z, 1 / 200, G + 41, 2))
    bio = np.where(marais & (hi < 69), BI['swamp'], bio)
    bio = np.where(eau > -999, BI['river'], bio)
    eau_i = np.where(eau > hi, np.round(eau).astype(np.int32), -999)
    return {'h': hi, 'eau': eau_i, 'biome': bio, 'route': route, 'route_y': np.round(route_y).astype(np.int32),
            'pont': pont & (eau_i > -999), 'site': site, 'riviere': riv, 'm': m, 'p': p,
            'route_d': route_d, 'route_s': route_s, 'route_l': route_l}
