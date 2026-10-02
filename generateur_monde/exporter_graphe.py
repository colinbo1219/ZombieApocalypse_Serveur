#!/usr/bin/env python3
"""Exporte le GRAPHE DU MONDE (bible F3) pour le moteur ZAMoteur : plugins/ZAMoteur/graphe.yml

  régions   : 100 cases de 1 000 x 1 000 blocs (r_i_j, i = colonne ouest->est, j = rangée nord->sud)
  lieux     : les sites du plan (id, type, nom, x, z, région)
  liens     : voisins (4 directions) avec un coût (route = facile) ; la rivière Blanche ajoute des liens
              à SENS UNIQUE vers l'aval (vers l'est) pour la contamination de l'eau (points 18 et 85)
  routes    : quelques points de route par région (les hordes migrent le long des routes, p33 / p76)

Usage : python3 exporter_graphe.py [sortie]   (défaut : ../plugins/ZAMoteur/graphe.yml)
Déterministe : même graine que le plan.
"""
import math
import os
import sys

import plan as P

TAILLE = 1000
N = 10


def reg(x, z):
    i = int((x + P.LIMITE) // TAILLE)
    j = int((z + P.LIMITE) // TAILLE)
    return min(N - 1, max(0, i)), min(N - 1, max(0, j))


def rid(i, j):
    return 'r_%d_%d' % (i, j)


def yq(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def main():
    sortie = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'plugins', 'ZAMoteur', 'graphe.yml')
    pl = P.construire()
    sites = pl['sites']
    # routes par région
    routes = {}
    for r in pl['routes']:
        for k, (x, z) in enumerate(r['points']):
            if k % 6:
                continue
            i, j = reg(x, z)
            routes.setdefault(rid(i, j), []).append((int(x), int(z), r['genre']))
    # rivière par région (ordre ouest -> est)
    riv_regs = []
    for (x, z, _l) in pl['riviere']:
        if abs(x) > P.LIMITE or abs(z) > P.LIMITE:
            continue
        i, j = reg(x, z)
        if not riv_regs or riv_regs[-1] != (i, j):
            riv_regs.append((i, j))
    riv_set = set(riv_regs)
    # nom de région : le lieu le plus important qui s'y trouve, sinon une description
    poids = {'ruines': 100, 'norda': 90, 'barrage': 85, 'militaire': 80, 'village': 70, 'industriel': 60,
             'carriere': 55, 'emetteur': 50, 'cimetiere': 45, 'arrivee': 40, 'ferme': 20, 'motel': 20,
             'station': 20, 'checkpoint': 25, 'refuge': 5, 'chalet': 5, 'camp_chasse': 5}
    noms = {}
    for s in sites:
        i, j = reg(s['x'], s['z'])
        k = rid(i, j)
        p = poids.get(s['type'], 10)
        if k not in noms or p > noms[k][0]:
            noms[k] = (p, s['nom'])
    lignes = ['# Graphe du monde (bible F3) — généré par generateur_monde/exporter_graphe.py : ne pas modifier à la main',
              'taille: %d' % TAILLE, 'n: %d' % N, 'limite: %d' % P.LIMITE, 'regions:']
    for j in range(N):
        for i in range(N):
            k = rid(i, j)
            cx = -P.LIMITE + i * TAILLE + TAILLE // 2
            cz = -P.LIMITE + j * TAILLE + TAILLE // 2
            nom = noms.get(k, (0, None))[1]
            if not nom:
                ns = 'nord' if j < 3 else ('sud' if j > 6 else 'centre')
                eo = 'ouest' if i < 3 else ('est' if i > 6 else '')
                nom = ('Terres du %s %s' % (ns, eo)).strip()
            lignes.append('  %s:' % k)
            lignes.append('    nom: %s' % yq(nom))
            lignes.append('    x: %d' % cx)
            lignes.append('    z: %d' % cz)
            lignes.append('    riviere: %s' % ('true' if (i, j) in riv_set else 'false'))
            pts = routes.get(k, [])[:12]
            lignes.append('    routes: [%s]' % ', '.join(yq('%d;%d;%s' % p) for p in pts))
    lignes.append('lieux:')
    for s in sites:
        i, j = reg(s['x'], s['z'])
        lignes.append('  %s:' % s['id'])
        lignes.append('    type: %s' % s['type'])
        lignes.append('    nom: %s' % yq(s['nom']))
        lignes.append('    x: %d' % int(s['x']))
        lignes.append('    z: %d' % int(s['z']))
        lignes.append('    region: %s' % rid(i, j))
    lignes.append('liens:')
    for j in range(N):
        for i in range(N):
            for (di, dj) in ((1, 0), (0, 1)):
                a, b = i + di, j + dj
                if a >= N or b >= N:
                    continue
                k1, k2 = rid(i, j), rid(a, b)
                route = bool(routes.get(k1)) and bool(routes.get(k2))
                cout = 1 if route else 3
                lignes.append('  - %s' % yq('%s;%s;%d;%s' % (k1, k2, cout, 'route' if route else 'terre')))
    # liens d'eau, vers l'aval seulement
    for a, b in zip(riv_regs, riv_regs[1:]):
        lignes.append('  - %s' % yq('%s;%s;1;riviere' % (rid(*a), rid(*b))))
    os.makedirs(os.path.dirname(os.path.abspath(sortie)), exist_ok=True)
    with open(sortie, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes) + '\n')
    print('OK', sortie, len(sites), 'lieux', len(riv_regs), 'régions sur la rivière')


if __name__ == '__main__':
    main()
