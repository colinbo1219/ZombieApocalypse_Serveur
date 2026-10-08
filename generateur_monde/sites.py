# -*- coding: utf-8 -*-
"""sites : structures posées dans les régions (ruines de Saint-Aurèle, autobus du Jour 8, villages, base Bravo, NORDA...).

Une structure = tableau [y][z][x] d'indices de palette + panneaux + conteneurs, comme les .json.gz de ZAMonde.
Les structures générées ici réutilisent le générateur de la ville (ZA_sources/ville : états validés, meubles,
portes, véhicules) : il faut avoir extrait ZA_sources_build.zip à la racine du serveur.
"""
import base64
import gzip
import json
import math
import os
import random
import sys
import zlib

import numpy as np

import terrain as T

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
VILLE = os.path.join(RACINE, 'ZA_sources', 'ville')
ZAMONDE = os.path.join(RACINE, 'plugins', 'ZAMonde')
if VILLE not in sys.path:
    sys.path.insert(0, VILLE)

LOOT_MAISON = 'minecraft:chests/village/village_plains_house'
LOOT_VILLE = 'lostcities:chests/lostcitychest'          # table du datapack za_loot (reste valable sans Lost Cities)
LOOT_MILITAIRE = 'minecraft:chests/village/village_weaponsmith'
LOOT_LABO = 'minecraft:chests/abandoned_mineshaft'


class Structure:
    def __init__(self, nom, a, pal, ox, oy, oz, signs=(), containers=(), coffres=()):
        self.nom = nom
        self.a = a                      # uint16 [H][D][W]
        self.pal = pal
        self.ox, self.oy, self.oz = ox, oy, oz
        self.signs = list(signs)
        self.containers = list(containers)
        self.coffres = list(coffres)    # (x, y, z, table de butin) en coordonnées de la structure

    @staticmethod
    def depuis_fichier(chemin):
        d = json.load(gzip.open(chemin))
        W, H, D = d['size']
        raw = zlib.decompress(base64.b64decode(d['blocks']))
        a = np.frombuffer(raw, '<u2').reshape(H, D, W).copy()
        ox, oy, oz = d.get('offset', [0, 0, 0])
        return Structure(os.path.basename(chemin), a, d['palette'], ox, oy, oz, d.get('signs', []), d.get('containers', []))

    @staticmethod
    def depuis_monde(nom, m, coffres=()):
        m.compacter()
        return Structure(nom, m.a.copy(), list(m.pal), m.x0, m.y0, m.z0, m.signs, m.containers, coffres)


# ============================================================================ entités de bloc
def _json_txt(t):
    return json.dumps({'text': t}, ensure_ascii=False)


def entite_panneau(s):
    import anvil as A
    msgs = A.Liste(8, [_json_txt(l) for l in (list(s['front']) + [''] * 4)[:4]])
    vide = A.Liste(8, [_json_txt('')] * 4)
    return {'id': 'minecraft:sign', 'keepPacked': A.Byte(0), 'is_waxed': A.Byte(1),
            'front_text': {'messages': msgs, 'color': s.get('color', 'black'), 'has_glowing_text': A.Byte(1 if s.get('glow') else 0)},
            'back_text': {'messages': vide, 'color': 'black', 'has_glowing_text': A.Byte(0)}}


def entite_conteneur(bloc, c=None, butin=None):
    import anvil as A
    ident = 'minecraft:barrel' if 'barrel' in bloc else ('minecraft:trapped_chest' if 'trapped' in bloc else 'minecraft:chest')
    d = {'id': ident, 'keepPacked': A.Byte(0)}
    if butin:
        d['LootTable'] = butin
        d['LootTableSeed'] = A.Long(0)
    if c:
        items = []
        for it in c.get('items', []):
            e = {'Slot': A.Byte(it.get('slot', 0)), 'id': it['id'], 'Count': A.Byte(it.get('n', 1))}
            if it.get('name'):
                e['tag'] = {'display': {'Name': json.dumps({'text': it['name'], 'italic': False}, ensure_ascii=False)}}
            items.append(e)
        d['Items'] = A.Liste(10, items)
    return d


# ============================================================================ pose dans une région
_STRUCT = {}


def base_de(site, st):
    """Coordonnées de pose (bx, by, bz) : la structure est centrée sur le site, sol au niveau du terrain aplani."""
    ys = T.y_site(site)
    if site['type'] == 'ruines':
        # coordonnées de la ville : sol de marche à y=64, centre ~ (80, 80)
        return site['x'] - 80, ys - 63, site['z'] - 80
    W, D = st.a.shape[2], st.a.shape[1]
    # structures « posées » : x/z centrés, sol de marche à y=0 (ZAMonde) ou y=64 (générées ici, comme la ville)
    if site['type'] == 'arrivee':
        return site['x'], ys + 1, site['z']
    return site['x'] - (st.ox + W // 2), ys - 63, site['z'] - (st.oz + D // 2)


def structure_de(site, plan):
    k = site['id']
    if k in _STRUCT:
        return _STRUCT[k]
    st = None
    if site['type'] == 'ruines':
        st = Structure.depuis_fichier(os.path.join(ZAMONDE, 'ruines.json.gz'))
    elif site['type'] == 'arrivee':
        st = Structure.depuis_fichier(os.path.join(ZAMONDE, 'arrivee.json.gz'))
    else:
        import batisse
        fn = getattr(batisse, site['type'], None)
        if fn:
            st = fn(site, plan)
    _STRUCT[k] = st
    return st


def poser(reg):
    for i, s in enumerate(reg.plan['sites']):
        if not _chevauche(reg, s):
            continue
        st = structure_de(s, reg.plan)
        if st is None:
            continue
        bx, by, bz = base_de(s, st)
        _estamper(reg, st, bx, by, bz)


def _chevauche(reg, s):
    return (s['x'] + s['larg'] / 2 + 40 >= reg.x0 and s['x'] - s['larg'] / 2 - 40 < reg.x0 + 512 and
            s['z'] + s['prof'] / 2 + 40 >= reg.z0 and s['z'] - s['prof'] / 2 - 40 < reg.z0 + 512)


def _estamper(reg, st, bx, by, bz):
    import monde as M
    H, D, W = st.a.shape
    wx0, wy0, wz0 = bx + st.ox, by + st.oy, bz + st.oz
    # recouvrement avec la région
    x1, x2 = max(wx0, reg.x0), min(wx0 + W, reg.x0 + M.N)
    z1, z2 = max(wz0, reg.z0), min(wz0 + D, reg.z0 + M.N)
    y1, y2 = max(wy0, M.Y0), min(wy0 + H, M.Y0 + M.HY)
    if x1 >= x2 or z1 >= z2 or y1 >= y2:
        return
    vanille = M.VANILLE_SEULEMENT
    lut = np.array([reg.pal(p if not vanille or p.startswith('minecraft:') else 'minecraft:cobblestone') for p in st.pal], np.uint16)
    src = st.a[y1 - wy0:y2 - wy0, z1 - wz0:z2 - wz0, x1 - wx0:x2 - wx0]
    bloc = lut[src]
    cible = reg.b[y1 - M.Y0:y2 - M.Y0, z1 - reg.z0:z2 - reg.z0, x1 - reg.x0:x2 - reg.x0]
    vide = [i for i, p in enumerate(st.pal) if p == 'minecraft:structure_void']
    if vide:
        # « vide de structure » : on garde ce qui est déjà là (roche des souterrains)
        cible[...] = np.where(src == vide[0], cible, bloc)
    else:
        cible[...] = bloc
    # au-dessus de la structure : dégagé (pas de terrain qui dépasse), sauf structures enterrées
    if not getattr(st, 'garder', False):
        reg.b[y2 - M.Y0:, z1 - reg.z0:z2 - reg.z0, x1 - reg.x0:x2 - reg.x0] = 0
    # entités de bloc
    for s in st.signs:
        x, y, z = bx + s['x'], by + s['y'], bz + s['z']
        reg.entite(x, y, z, entite_panneau(s))
    faits = set()
    for c in st.containers:
        x, y, z = bx + c['x'], by + c['y'], bz + c['z']
        blocn = st.pal[st.a[c['y'] - st.oy, c['z'] - st.oz, c['x'] - st.ox]]
        reg.entite(x, y, z, entite_conteneur(blocn, c))
        faits.add((c['x'], c['y'], c['z']))
    for (cx, cy, cz, butin) in st.coffres:
        if (cx, cy, cz) in faits:
            continue
        blocn = st.pal[st.a[cy - st.oy, cz - st.oz, cx - st.ox]]
        if 'chest' in blocn or 'barrel' in blocn:
            reg.entite(bx + cx, by + cy, bz + cz, entite_conteneur(blocn, None, butin))


# ============================================================================ données pour ZAMonde et Skript
def placements(plan):
    """placements.yml de ZAMonde (POIs « ruines:… » et « arrivee:… ») pour le nouveau monde."""
    lignes = ['# Généré par generateur_monde : structures posées dans le monde « world »']
    for s in plan['sites']:
        if s['type'] not in ('ruines', 'arrivee'):
            continue
        st = structure_de(s, plan)
        bx, by, bz = base_de(s, st)
        lab = 'ruines' if s['type'] == 'ruines' else 'arrivee'
        lignes += ['%s:' % lab, '  monde: world', '  x: %d' % bx, '  y: %d' % by, '  z: %d' % bz]
    return '\n'.join(lignes) + '\n'
