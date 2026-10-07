# -*- coding: utf-8 -*-
"""plan : la région de Saint-Aurèle (10 000 x 10 000 blocs, x et z de -5000 à +5000).

                     NORD : les Laurentides (montagnes, forêt boréale, lacs, chalets, émetteur CKZA)
        Base Bravo  ·  Val-des-Pins                         NORDA Biotech · carrière
   ═══════ Autoroute 40 ════════ SAINT-AURÈLE (0,0) ══════════ parc industriel ═══════
        barrage + centrale ≈≈≈≈≈≈≈ rivière Blanche ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈
                     Rivière-Blanche (village)          Sainte-Brigitte
                     SUD : terres agricoles (fermes), marais
La route 117 traverse la carte du nord au sud en passant par Saint-Aurèle.
Tout est déterministe (graine) : le plan est identique à chaque exécution.
"""
import math
import random

GRAINE = 1250
LIMITE = 5000            # la carte va de -LIMITE à +LIMITE (10 000 blocs)
MER = 62                 # niveau de l'eau (lacs, rivière)


def _riviere(rng):
    """Rivière Blanche : d'ouest en est, méandres. Points (x, z, largeur)."""
    pts = []
    for x in range(-LIMITE - 200, LIMITE + 241, 40):
        z = 850 + 260 * math.sin(x / 900.0) + 120 * math.sin(x / 310.0 + 1.3) + 0.06 * x
        larg = 20 + 26 * (x + LIMITE) / (2 * LIMITE)
        # réservoir en amont du barrage (x ≈ -2600) : la rivière s'élargit en lac
        if -3450 < x < -2620:
            larg += 150 * math.sin(math.pi * (x + 3450) / 830.0)
        pts.append((float(x), float(z), float(larg)))
    return pts


def z_riviere(x, riv):
    for i in range(len(riv) - 1):
        (x1, z1, _), (x2, z2, _) = riv[i], riv[i + 1]
        if x1 <= x <= x2:
            t = (x - x1) / (x2 - x1)
            return z1 + (z2 - z1) * t
    return riv[-1][1]


LACS = [
    # (nom, x, z, rayon)
    ('Lac-aux-Loups', -1250, -2650, 260), ('Lac Tremblant', 1500, -3150, 330), ('Lac des Érables', -2850, -1750, 190),
    ('Lac Noir', 3350, -2050, 210), ('Lac à la Truite', -600, -4300, 220), ('Lac Caché', 3900, -4100, 240),
    ('Lac Saint-Aurèle', 620, -760, 95), ('Lac du Marais', -3550, 2850, 230), ('Étang des Castors', 3850, 3250, 150),
    ('Lac Vert', -4200, -3300, 200), ('Lac Long', 2300, -4500, 170),
]


def _route(nom, genre, pts, rng=None, ondule=0.0):
    """genre : autoroute (14 de large), route (7), rang (5, gravier), rail (3, ballast). Densifie tous les ~24 blocs."""
    larg = {'autoroute': 14, 'route': 7, 'rang': 5, 'rail': 3}[genre]
    dense = []
    for i in range(len(pts) - 1):
        (x1, z1), (x2, z2) = pts[i], pts[i + 1]
        d = math.hypot(x2 - x1, z2 - z1)
        n = max(1, int(d // 24))
        for k in range(n):
            t = k / n
            x, z = x1 + (x2 - x1) * t, z1 + (z2 - z1) * t
            if rng and ondule and 0 < k:
                nx, nz = -(z2 - z1) / d, (x2 - x1) / d
                o = ondule * math.sin(t * math.pi) * math.sin(k * 0.7 + i)
                x, z = x + nx * o, z + nz * o
            dense.append((x, z))
    dense.append(pts[-1])
    return {'nom': nom, 'genre': genre, 'largeur': larg, 'points': dense}


def construire(graine=GRAINE):
    rng = random.Random(graine)
    riv = _riviere(rng)
    sites = []

    def site(ident, genre, nom, x, z, larg, prof, **kw):
        d = {'id': ident, 'type': genre, 'nom': nom, 'x': int(x), 'z': int(z), 'larg': int(larg), 'prof': int(prof)}
        d.update(kw)
        sites.append(d)
        return d

    # ---------------------------------------------------------------- lieux principaux
    site('saint_aurele', 'ruines', 'Saint-Aurèle', 0, 0, 300, 300, y=64)
    site('arrivee', 'arrivee', "L'autobus du Jour 8", 640, 250, 48, 48)
    site('base_bravo', 'militaire', 'Base Bravo (Forces armées)', -2750, 120, 200, 170)
    site('norda', 'norda', 'NORDA Biotech — campus de Saint-Aurèle', 2650, -760, 170, 150)
    xb = -2600
    site('barrage', 'barrage', 'Barrage de la Rivière-Blanche', xb, z_riviere(xb, riv), 110, 150, aplanir=False)
    site('parc_industriel', 'industriel', 'Parc industriel Laurentien', 1650, 470, 210, 130)
    site('val_des_pins', 'village', 'Val-des-Pins', -1950, -1150, 200, 200, graine=11)
    site('riviere_blanche', 'village', 'Rivière-Blanche', -350, 1650, 260, 220, graine=12)
    site('sainte_brigitte', 'village', 'Sainte-Brigitte', 2350, 2050, 220, 200, graine=13)
    site('ckza', 'emetteur', 'Émetteur CKZA 98,5 (mont Gagnon)', -700, -3650, 60, 60)
    site('carriere', 'carriere', 'Carrière Laurentide', 3650, -380, 140, 140)
    site('motel', 'motel', 'Motel du Voyageur', 3050, 330, 70, 50)
    for i, x in enumerate((-3650, -1250, 1850, 4050)):
        site('station_%d' % (i + 1), 'station', 'Station-service de l\'autoroute 40', x, 330, 48, 40)
    # checkpoints militaires (escouade Bravo-3 de Vega)
    site('checkpoint_ouest', 'checkpoint', 'Barrage militaire ouest', -900, 300, 30, 30)
    site('checkpoint_nord', 'checkpoint', 'Barrage militaire nord', 0, -900, 30, 30)

    # ---------------------------------------------------------------- fermes (sud), chalets (nord), camps de chasse
    def libre(x, z, r, lacs=True):
        for s in sites:
            if abs(s['x'] - x) < (s['larg'] / 2 + r) and abs(s['z'] - z) < (s['prof'] / 2 + r):
                return False
        if abs(z - z_riviere(x, riv)) < 140:
            return False
        if lacs:
            for (_, lx, lz, lr) in LACS:
                if math.hypot(x - lx, z - lz) < lr + 60:
                    return False
        return True

    n = 0
    essais = 0
    while n < 18 and essais < 2000:
        essais += 1
        x, z = rng.randint(-4600, 4600), rng.randint(1500, 4600)
        if libre(x, z, 160):
            n += 1
            site('ferme_%d' % n, 'ferme', 'Ferme %s' % rng.choice(['Tremblay', 'Gagnon', 'Roy', 'Côté', 'Bouchard', 'Gauthier',
                                                                   'Morin', 'Lavoie', 'Fortin', 'Gagné', 'Ouellet', 'Pelletier']),
                 x, z, 90, 80, graine=100 + n)
    n = 0
    for (lnom, lx, lz, lr) in LACS:
        if lz > -1400:
            continue
        for k in range(2):
            a = rng.random() * 2 * math.pi
            x, z = lx + math.cos(a) * (lr + 45), lz + math.sin(a) * (lr + 45)
            if libre(x, z, 30, lacs=False):
                n += 1
                site('chalet_%d' % n, 'chalet', 'Chalet du %s' % lnom, x, z, 22, 20, graine=200 + n, lac=lnom)
    n = 0
    essais = 0
    while n < 22 and essais < 3000:
        essais += 1
        x, z = rng.randint(-4700, 4700), rng.randint(-4700, 1200)
        if libre(x, z, 120):
            n += 1
            site('camp_chasse_%d' % n, 'camp_chasse', 'Camp de chasse', x, z, 20, 18, graine=300 + n)

    # refuges abandonnés : petites caches de survivants un peu partout (numérotées comme sur la carte de la milice)
    # (générateur aléatoire à part : ajouter les refuges ne change ni les routes ni les autres lieux)
    rr = random.Random(graine + 99)
    n = 0
    essais = 0
    while n < 20 and essais < 4000:
        essais += 1
        x, z = rr.randint(-4700, 4700), rr.randint(-4700, 4700)
        if libre(x, z, 140):
            n += 1
            site('refuge_%d' % n, 'refuge', 'Refuge %d' % (n + rr.randint(0, 3) * 20), x, z, 14, 14, graine=400 + n)

    # cimetière de Saint-Aurèle (les tombes des joueurs y sont gravées : za_p88)
    site('cimetiere', 'cimetiere', 'Cimetière de Saint-Aurèle', 190, -260, 46, 46)

    # ---------------------------------------------------------------- grands lieux de la bible (Partie 3, points 28-31, 36)
    # Positions voulues, déplacées en spirale (sans hasard) si la place est prise : rien d'autre ne bouge sur la carte.
    def loin_eau(x, z, larg, prof):
        for dx in (-larg / 2, 0, larg / 2):
            for dz in (-prof / 2, 0, prof / 2):
                if abs(z + dz - z_riviere(x + dx, riv)) < 70:
                    return False
        for (_, lx, lz, lr) in LACS:
            if math.hypot(x - lx, z - lz) < lr + max(larg, prof) / 2 + 30:
                return False
        return True

    def poser_libre(ident, genre, nom, x, z, larg, prof, eau=False, **kw):
        r = max(larg, prof) / 2 + 30
        for k in range(60):
            a = k * 0.9
            d = 0 if k == 0 else 40 + 22 * k
            xx, zz = int(x + math.cos(a) * d), int(z + math.sin(a) * d)
            if abs(xx) > LIMITE - larg or abs(zz) > LIMITE - prof:
                continue
            if eau:
                ok = all(abs(s_['x'] - xx) >= s_['larg'] / 2 + r or abs(s_['z'] - zz) >= s_['prof'] / 2 + r for s_ in sites)
            else:
                ok = libre(xx, zz, r) and loin_eau(xx, zz, larg, prof)
            if ok:
                # « bible » : ajoutés après coup ; les tirages des épaves les ignorent pour ne rien déplacer
                return site(ident, genre, nom, xx, zz, larg, prof, bible=True, **kw)
        return None

    poser_libre('aeroport', 'aeroport', 'Aéroport régional des Laurentides', 3900, 1550, 340, 150)
    poser_libre('centre_achat', 'centre_achat', "Carrefour Laurentides", 1050, 500, 120, 90)
    poser_libre('arena', 'arena', 'Aréna Gilles-Tremblay', -480, -500, 90, 70)
    poser_libre('prison', 'prison', 'Établissement de détention de Saint-Aurèle', -3700, -900, 150, 150)
    poser_libre('universite', 'universite', 'Université du Québec — campus des Laurentides', 1350, -1350, 170, 120)
    poser_libre('hotel', 'hotel', 'Hôtel des Laurentides', -1750, -2300, 50, 40)
    poser_libre('port', 'port', 'Port de Saint-Aurèle', 760, int(z_riviere(760, riv)) - 48, 60, 40, eau=True)
    gares = [poser_libre('gare_val', 'gare', 'Gare de Val-des-Pins', -1950, -980, 70, 30),
             poser_libre('gare_sa', 'gare', 'Gare de Saint-Aurèle', -330, -300, 70, 30),
             poser_libre('gare_brigitte', 'gare', 'Gare de Sainte-Brigitte', 2350, 1880, 70, 30)]

    # ---------------------------------------------------------------- les villes (ville.py : ville -> quartiers -> îlots
    # -> lots), découpées en fenêtres de 240 ; emplacements libres et plats vérifiés ; « bible » : rien d'autre ne bouge
    import ville
    sites.extend(ville.sites_du_plan())

    # ---------------------------------------------------------------- routes
    routes = []
    a40 = [(-LIMITE - 100, 300)]
    for x in range(-4600, LIMITE + 101, 800):
        a40.append((x, 300 + (60 if (x // 800) % 2 else -40) * (0 if abs(x) < 900 else 1)))
    a40[-1] = (LIMITE + 100, 300)
    routes.append(_route('Autoroute 40', 'autoroute', a40))
    r117 = [(0, -LIMITE - 100), (-150, -3900), (-420, -3000), (-120, -2000), (0, -1100), (0, -160),
            (0, 160), (40, 700), (-60, 1300), (-120, 2400), (80, 3600), (0, LIMITE + 100)]
    routes.append(_route('Route 117', 'route', r117, rng, 30))
    # rue Principale de Saint-Aurèle prolongée vers l'est et l'ouest (la ville est centrée en 0,0)
    routes.append(_route('Chemin du Lac', 'route', [(160, 2), (420, -300), (560, -640)], rng, 12))
    routes.append(_route('Rang Saint-Aurèle', 'route', [(-160, 2), (-700, 60), (-1300, -400), (-1850, -1050)], rng, 25))

    def relier(s, cible_pts, genre='rang', ondule=18):
        """Relie un site au point de route le plus proche (liste de points)."""
        best = min(cible_pts, key=lambda p: math.hypot(p[0] - s['x'], p[1] - s['z']))
        if math.hypot(best[0] - s['x'], best[1] - s['z']) < 30:
            return
        routes.append(_route('Chemin de %s' % s['nom'], genre, [(s['x'], s['z']), best], rng, ondule))

    # les sites de bord de route se calent sur la route réelle (côté nord ou sud)
    def sur_route(pts, v, axe):
        best = min(pts, key=lambda p: abs(p[axe] - v))
        return best[1 - axe]
    for s in sites:
        if s['type'] in ('station', 'motel'):
            s['z'] = int(sur_route(routes[0]['points'], s['x'], 0) + 12 + s['prof'] // 2)
        elif s['id'] == 'arrivee':
            s['z'] = int(sur_route(routes[0]['points'], s['x'], 0) - 12 - s['prof'] // 2)
        elif s['id'] == 'checkpoint_ouest':
            s['z'] = int(sur_route(routes[0]['points'], s['x'], 0))
        elif s['id'] == 'checkpoint_nord':
            s['x'] = int(sur_route(routes[1]['points'], s['z'], 1))

    # ---------------------------------------------------------------- la ligne de train (36) : segments droits nord-sud
    # et est-ouest (les rails de Minecraft ne font pas de diagonale), à travers les trois gares
    g = [x for x in gares if x]
    if len(g) >= 2:
        rail = [(g[0]['x'] - 45, g[0]['z']), (g[0]['x'] + 45, g[0]['z'])]
        coudes = {0: -1140, 1: 500}
        for i in range(1, len(g)):
            mx = coudes.get(i - 1, (rail[-1][0] + g[i]['x']) // 2)
            rail += [(mx, rail[-1][1]), (mx, g[i]['z']), (g[i]['x'] - 45, g[i]['z']), (g[i]['x'] + 45, g[i]['z'])]
        r = _route('Ligne Laurentienne', 'rail', rail)
        routes.append(r)

    # sorties des villes vers le réseau (ajoutées en dernier : rien ne bouge)
    for nom, pts in ville.routes_du_plan():
        routes.append(_route(nom, 'route', pts))

    principaux = routes[0]['points'] + routes[1]['points']
    for s in sites:
        if s['type'] in ('ruines', 'arrivee', 'station', 'checkpoint', 'motel', 'ville_tuile'):
            continue
        genre = 'route' if s['type'] in ('militaire', 'norda', 'barrage', 'industriel', 'village') else 'rang'
        if s['type'] in ('camp_chasse', 'refuge'):
            continue
        relier(s, principaux + sum((r['points'] for r in routes[2:4]), []), genre)
    return {'graine': graine, 'limite': LIMITE, 'mer': MER, 'riviere': riv, 'lacs': LACS, 'routes': routes, 'sites': sites,
            'breches': breches(routes, riv), 'quartiers': ville.quartiers_du_plan()}


def breches(routes, riv):
    """Ponts détruits (86) : là où la route 117, la voie ferrée et un chemin sur trois franchissent la rivière, le tablier
    est arraché sur ~16 blocs. Passages obligés : les hordes (graphe) et les convois doivent faire le détour."""
    out = []
    for r in routes:
        nom = r['nom']
        detruit = nom in ('Route 117', 'Ligne Laurentienne') or (nom.startswith('Chemin') and sum(map(ord, nom)) % 3 == 0)
        if not detruit:
            continue
        pts = r['points']
        for (x1, z1), (x2, z2) in zip(pts, pts[1:]):
            f1, f2 = z1 - z_riviere(x1, riv), z2 - z_riviere(x2, riv)
            if f1 == f2 or (f1 > 0) == (f2 > 0):
                continue
            t = f1 / (f1 - f2)
            out.append({'x': int(x1 + (x2 - x1) * t), 'z': int(z1 + (z2 - z1) * t), 'r': 8, 'route': nom})
    return out


if __name__ == '__main__':
    import json
    p = construire()
    print(json.dumps({'sites': len(p['sites']), 'routes': len(p['routes']),
                      'types': sorted({s['type'] for s in p['sites']})}, ensure_ascii=False))
