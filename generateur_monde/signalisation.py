# -*- coding: utf-8 -*-
"""signalisation : panneaux routiers (sortie 117, entrée de Saint-Aurèle, chemin de chaque lieu).

Un panneau = poteau de 2 blocs + panneau mural accroché du côté de la route, face aux véhicules qui arrivent.
Les panneaux sont calculés une fois à partir du plan, puis posés région par région après la végétation.
"""
import math

DIRS = {'east': (1, 0), 'west': (-1, 0), 'south': (0, 1), 'north': (0, -1)}


def _face(fx, fz):
    if abs(fx) >= abs(fz):
        return 'east' if fx > 0 else 'west'
    return 'south' if fz > 0 else 'north'


def _km(d):
    if d < 950:
        return '%d m' % (round(d / 50) * 50)
    return ('%.1f km' % (d / 1000)).replace('.', ',')


def _couper(nom, n=15):
    """Nom sur 1 ou 2 lignes de panneau (~15 caractères)."""
    mots, lignes, cur = nom.split(), [], ''
    for m in mots:
        if cur and len(cur) + 1 + len(m) > n:
            lignes.append(cur)
            cur = m
        else:
            cur = (cur + ' ' + m).strip()
    lignes.append(cur)
    return lignes[:2]


def _longueur(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))


def _bord(route, i, sens, cote):
    """Point au bord de la route au point i. sens = +1/-1 (sens de circulation le long des points),
    cote = 'droite' (côté de circulation au Québec) ou 'gauche'. Renvoie (x, z, face du panneau)."""
    pts = route['points']
    a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
    dx, dz = (b[0] - a[0]) * sens, (b[1] - a[1]) * sens
    d = math.hypot(dx, dz) or 1
    dx, dz = dx / d, dz / d
    # droite du conducteur (x vers l'est, z vers le sud) : (-dz, dx)
    nx, nz = (-dz, dx) if cote == 'droite' else (dz, -dx)
    off = route['largeur'] / 2 + 2
    x, z = pts[i][0] + nx * off, pts[i][1] + nz * off
    return int(round(x)), int(round(z)), _face(-dx, -dz)


def _indice(route, x, z):
    pts = route['points']
    return min(range(len(pts)), key=lambda k: (pts[k][0] - x) ** 2 + (pts[k][1] - z) ** 2)


def panneaux(plan):
    routes = {r['nom']: r for r in plan['routes']}
    a40, r117 = routes['Autoroute 40'], routes['Route 117']
    sites = {s['id']: s for s in plan['sites']}
    out = []

    def ajout(x, z, face, lignes, couleur='black', lumineux=False, bois='spruce'):
        for _ in range(4):
            proche = [q for q in out if abs(q['x'] - x) < 3 and abs(q['z'] - z) < 3]
            if not proche:
                break
            if any(q['lignes'][:2] == list(lignes)[:2] for q in proche):
                return          # deux lieux du même nom au même embranchement (chalets d'un lac)
            fx, fz = DIRS[face]
            x, z = x + 3 * abs(fz), z + 3 * abs(fx)     # décalé le long de la route
        out.append({'x': x, 'z': z, 'face': face, 'lignes': (list(lignes) + [''] * 4)[:4],
                    'couleur': couleur, 'lumineux': lumineux, 'bois': bois})

    # --- autoroute 40 : sortie 117 annoncée dans les deux sens (vert, texte blanc lumineux)
    jx = r117['points'][_indice(r117, 0, 300)][0]
    for sens, dx in ((1, -250), (-1, 250)):
        i = _indice(a40, jx + dx, 300)
        x, z, f = _bord(a40, i, sens, 'droite')
        ajout(x, z, f, ['SORTIE 117', 'Saint-Aurèle', 'Rivière-Blanche', _km(250)], 'white', True, 'warped')

    # --- à côté de l'autobus du Jour 8 : la seule indication vers la ville (vers l'ouest)
    bus = sites.get('arrivee')
    if bus:
        i = _indice(a40, bus['x'] - 40, 300)
        x, z, f = _bord(a40, i, -1, 'droite')
        ajout(x, z, f, ['SAINT-AURÈLE', 'Sortie 117', _km(abs(bus['x'] - 40 - jx)), 'tout droit'], 'white', True, 'warped')

    # --- route 117 : entrées de Saint-Aurèle (sud et nord) + avis de quarantaine
    for zc, sens in ((230, -1), (-230, 1)):
        i = _indice(r117, 0, zc)
        # les points de la 117 vont du nord au sud : sens -1 = vers le nord
        x, z, f = _bord(r117, i, sens, 'droite')
        ajout(x, z, f, ['Bienvenue à', 'SAINT-AURÈLE', 'Au cœur des', 'Laurentides'], 'black', False, 'birch')
        i2 = min(len(r117['points']) - 1, max(0, i - 2 * sens))
        x, z, f = _bord(r117, i2, sens, 'droite')
        ajout(x, z, f, ['QUARANTAINE', 'Accès interdit', 'Ordre du', 'gouvernement'], 'red', True, 'dark_oak')

    # --- chemin de chaque lieu : panneau à l'embranchement, tourné vers la route principale
    speciaux = {
        'militaire': ['BASE BRAVO', 'Zone militaire', 'ACCÈS INTERDIT'],
        'norda': ['NORDA Biotech', 'Campus de', 'recherche', 'Accès restreint'],
        'barrage': ['Barrage de la', 'Rivière-Blanche', 'Hydro'],
        'emetteur': ['CKZA 98,5', 'Émetteur du', 'mont Gagnon'],
    }
    for r in plan['routes']:
        if not r['nom'].startswith('Chemin de '):
            continue
        nom = r['nom'][len('Chemin de '):]
        s = next((s for s in plan['sites'] if s['nom'] == nom), None)
        if s is None:
            continue
        pts = r['points']           # du lieu vers la route principale
        k = max(0, len(pts) - 2)     # ~24 blocs avant l'embranchement
        x, z, f = _bord(r, k, -1, 'droite')     # conducteur qui quitte la route principale vers le lieu
        dist = _km(_longueur(pts[:k + 1]))
        if s['type'] in speciaux:
            lignes = speciaux[s['type']][:3] + [dist]
        else:
            lignes = _couper(nom)
            lignes = lignes + [''] * (3 - len(lignes)) + [dist] if len(lignes) < 3 else lignes + [dist]
        couleur = 'red' if s['type'] in ('militaire', 'norda') else 'black'
        ajout(x, z, f, lignes, couleur, s['type'] in ('militaire', 'norda'), 'spruce')
    return out


def poser(reg, liste):
    """Pose les panneaux de la liste qui tombent dans la région (après la végétation)."""
    import monde as M
    import sites as SI
    pal = reg.pal
    # blocs sur lesquels un poteau peut reposer
    mou = ('leaves', 'log', 'grass', 'fern', 'flower', 'dandelion', 'poppy', 'daisy', 'bluet', 'orchid', 'tulip',
           'snow', 'vine', 'bush', 'water', 'lily', 'sapling', 'lantern', 'sign')
    for p in liste:
        lx, lz = p['x'] - reg.x0, p['z'] - reg.z0
        fx, fz = DIRS[p['face']]
        sx, sz = p['x'] + fx, p['z'] + fz
        if not (0 <= lx < M.N and 0 <= lz < M.N and 0 <= sx - reg.x0 < M.N and 0 <= sz - reg.z0 < M.N):
            continue
        col = reg.b[:, lz, lx]
        y = None
        for ly in range(M.HY - 1, 0, -1):
            v = col[ly]
            if v and not any(m in pal.l[v] for m in mou):
                y = ly + M.Y0 + 1
                break
        if y is None:
            continue
        for dy in range(0, 5):
            reg.poser(p['x'], y + dy, p['z'], 'minecraft:air')
            reg.poser(sx, y + dy, sz, 'minecraft:air')
        poteau = 'minecraft:%s_fence[east=false,north=false,south=false,waterlogged=false,west=false]' % p['bois']
        planche = 'minecraft:%s_planks' % p['bois']
        if p['bois'] == 'warped':
            poteau, planche = 'minecraft:iron_bars[east=false,north=false,south=false,waterlogged=false,west=false]', \
                'minecraft:green_concrete'
        reg.poser(p['x'], y, p['z'], poteau)
        reg.poser(p['x'], y + 1, p['z'], planche)
        reg.poser(sx, y + 1, sz, 'minecraft:%s_wall_sign[facing=%s,waterlogged=false]' % (
            'oak' if p['bois'] == 'warped' else p['bois'], p['face']))
        reg.entite(sx, y + 1, sz, SI.entite_panneau({'front': p['lignes'], 'color': p['couleur'], 'glow': p['lumineux']}))
