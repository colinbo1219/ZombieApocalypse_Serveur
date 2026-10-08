# -*- coding: utf-8 -*-
"""flore : arbres (gabarits) et végétation basse. Feuilles persistantes (pas de disparition au chargement)."""
import random

import numpy as np


def _f(bois):
    return 'minecraft:%s_leaves[distance=1,persistent=true,waterlogged=false]' % bois


def _t(bois, axe='y'):
    return 'minecraft:%s_log[axis=%s]' % (bois, axe)


def epinette(r, h=None, gros=False):
    h = h or r.randint(8, 13)
    b = []
    tr = [(0, 0), (1, 0), (0, 1), (1, 1)] if gros else [(0, 0)]
    for y in range(h):
        for (dx, dz) in tr:
            b.append((dx, y, dz, _t('spruce')))
    rayon_max = 3 if gros else 2
    for y in range(3 if not gros else 5, h + 1):
        k = (h - y)
        rr = min(rayon_max, 1 + (k // 3) % (rayon_max + 1)) if k > 1 else (1 if k == 1 else 0)
        for dx in range(-rr, rr + 1 + (1 if gros else 0)):
            for dz in range(-rr, rr + 1 + (1 if gros else 0)):
                if abs(dx) + abs(dz) <= rr + (1 if gros else 0) and not ((dx, dz) in tr and y < h):
                    b.append((dx, y, dz, _f('spruce')))
    b.append((0, h + 1, 0, _f('spruce')))
    return b


def feuillu(r, bois='oak', h=None, rayon=None):
    h = h or r.randint(5, 7)
    rayon = rayon or r.choice((2, 2, 3))
    b = [(0, y, 0, _t(bois)) for y in range(h)]
    for y in range(h - rayon, h + 2):
        dy = y - (h - 1)
        for dx in range(-rayon, rayon + 1):
            for dz in range(-rayon, rayon + 1):
                if dx * dx + dz * dz + dy * dy * 1.5 <= rayon * rayon + 1 and (dx, dz) != (0, 0) or (y >= h and (dx, dz) == (0, 0)):
                    if r.random() > 0.08:
                        b.append((dx, y, dz, _f(bois)))
    return b


def bouleau(r):
    return feuillu(r, 'birch', r.randint(6, 8), 2)


def buisson(r, bois='oak'):
    b = [(0, 0, 0, _t(bois))]
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            for dy in (0, 1):
                if (dx, dy, dz) != (0, 0, 0) and r.random() < 0.75:
                    b.append((dx, dy, dz, _f(bois)))
    return b


def souche(r):
    axe = r.choice(('x', 'z'))
    n = r.randint(3, 5)
    return [(i if axe == 'x' else 0, 0, i if axe == 'z' else 0, _t(r.choice(('spruce', 'birch', 'oak')), axe)) for i in range(n)]


def gabarits(graine=1250):
    """Quelques variantes par espèce : {espece: [liste de (dx,dy,dz,état)]}"""
    r = random.Random(graine)
    return {
        'epinette': [epinette(r) for _ in range(8)],
        'grande_epinette': [epinette(r, r.randint(16, 24), True) for _ in range(4)],
        'chene': [feuillu(r, 'oak') for _ in range(6)],
        'bouleau': [bouleau(r) for _ in range(6)],
        'buisson': [buisson(r) for _ in range(3)] + [buisson(r, 'spruce') for _ in range(2)],
        'souche': [souche(r) for _ in range(4)],
    }


# densité d'arbres (probabilité par cellule de 4x4) et mélange d'espèces par biome
MELANGE = {
    'forest': (0.42, [('chene', 5), ('bouleau', 3), ('epinette', 2), ('buisson', 1), ('souche', 0.3)]),
    'birch_forest': (0.45, [('bouleau', 8), ('chene', 1), ('buisson', 1), ('souche', 0.3)]),
    'old_growth_birch_forest': (0.5, [('bouleau', 9), ('buisson', 1)]),
    'taiga': (0.5, [('epinette', 9), ('bouleau', 1), ('buisson', 1), ('souche', 0.4)]),
    'old_growth_spruce_taiga': (0.55, [('grande_epinette', 3), ('epinette', 6), ('souche', 0.5)]),
    'grove': (0.28, [('epinette', 1)]),
    'plains': (0.03, [('chene', 3), ('buisson', 2), ('bouleau', 1)]),
    'meadow': (0.02, [('chene', 1), ('buisson', 1)]),
    'swamp': (0.18, [('chene', 3), ('buisson', 2)]),
}

FLEURS = ['minecraft:dandelion', 'minecraft:poppy', 'minecraft:oxeye_daisy', 'minecraft:cornflower', 'minecraft:azure_bluet',
          'minecraft:lily_of_the_valley']
