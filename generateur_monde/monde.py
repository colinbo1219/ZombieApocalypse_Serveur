# -*- coding: utf-8 -*-
"""monde : génération d'une région Anvil complète (512 x 512 colonnes, y de -64 à 255).

Ordre : relief (terrain.champ) -> sous-sol, surface, eau -> minerais -> grottes -> routes et ponts
      -> sites (sites.poser) -> végétation -> découpage en chunks (anvil).
"""
import os
import random

import numpy as np

import anvil
import bruit as B
import flore
import terrain as T

Y0 = -64
HY = 320                     # y de -64 à 255
N = 512
MARGE = 16                   # marge de relief autour de la région (arbres qui débordent)

# ============================================================================ palette
class Palette:
    def __init__(self):
        self.l = ['minecraft:air']
        self.d = {'minecraft:air': 0}

    def __call__(self, st):
        i = self.d.get(st)
        if i is None:
            i = self.d[st] = len(self.l)
            self.l.append(st)
        return i


# minerais : (état, état deepslate, y min, y max, tentatives par chunk, taille)
MINERAIS = [
    ('minecraft:coal_ore', 'minecraft:deepslate_coal_ore', 0, 140, 18, 10),
    ('minecraft:iron_ore', 'minecraft:deepslate_iron_ore', -40, 80, 11, 8),
    ('minecraft:iron_ore', 'minecraft:deepslate_iron_ore', 90, 220, 6, 8),
    ('minecraft:copper_ore', 'minecraft:deepslate_copper_ore', -8, 96, 9, 11),
    ('minecraft:gold_ore', 'minecraft:deepslate_gold_ore', -64, 32, 4, 7),
    ('minecraft:redstone_ore[lit=false]', 'minecraft:deepslate_redstone_ore[lit=false]', -64, 16, 6, 7),
    ('minecraft:lapis_ore', 'minecraft:deepslate_lapis_ore', -48, 48, 2, 6),
    ('minecraft:diamond_ore', 'minecraft:deepslate_diamond_ore', -64, 12, 3, 5),
    ('minecraft:emerald_ore', 'minecraft:deepslate_emerald_ore', 60, 220, 2, 2),
    ('create:zinc_ore', 'create:deepslate_zinc_ore', -60, 70, 7, 10),
    ('immersiveengineering:ore_aluminum', 'immersiveengineering:deepslate_ore_aluminum', 36, 90, 4, 10),
    ('immersiveengineering:ore_lead', 'immersiveengineering:deepslate_ore_lead', -32, 40, 5, 8),
    ('immersiveengineering:ore_silver', 'immersiveengineering:deepslate_ore_silver', -64, 40, 4, 8),
    ('immersiveengineering:ore_nickel', 'immersiveengineering:deepslate_ore_nickel', -64, 24, 3, 6),
    ('immersiveengineering:ore_uranium', 'immersiveengineering:deepslate_ore_uranium', -64, -16, 2, 4),
    ('minecraft:granite', 'minecraft:tuff', -64, 90, 3, 30),
    ('minecraft:diorite', 'minecraft:tuff', -64, 90, 2, 30),
    ('minecraft:andesite', 'minecraft:tuff', -64, 90, 3, 30),
    ('minecraft:gravel', 'minecraft:gravel', -30, 80, 2, 24),
    ('minecraft:dirt', 'minecraft:dirt', 0, 90, 2, 24),
]

VANILLE_SEULEMENT = False     # --vanille : remplace les minerais moddés (tests avec le serveur vanilla)


def _rng(*cles):
    return np.random.default_rng([abs(int(c)) * 2 + (1 if int(c) < 0 else 0) for c in cles])


# ============================================================================ génération d'une région
class Region:
    def __init__(self, plan, rx, rz):
        self.plan = plan
        self.rx, self.rz = rx, rz
        self.x0, self.z0 = rx * N, rz * N
        self.pal = Palette()
        self.b = np.zeros((HY, N, N), np.uint16)
        self.entites = {}          # (cx, cz) -> liste de block entities (coordonnées absolues)
        xs = np.arange(self.x0 - MARGE, self.x0 + N + MARGE, dtype=np.float64)
        zs = np.arange(self.z0 - MARGE, self.z0 + N + MARGE, dtype=np.float64)
        Zg, Xg = np.meshgrid(zs, xs, indexing='ij')
        self.c = T.champ(plan, Xg, Zg)          # champs avec marge [z][x]
        s = slice(MARGE, MARGE + N)
        self.h = self.c['h'][s, s]
        self.eau = self.c['eau'][s, s]
        self.bio = self.c['biome'][s, s]

    # --- accès
    def ci(self, nom):
        return self.c[nom][MARGE:MARGE + N, MARGE:MARGE + N]

    def poser(self, x, y, z, st):
        """Pose un bloc (coordonnées absolues) s'il est dans la région."""
        lx, lz, ly = x - self.x0, z - self.z0, y - Y0
        if 0 <= lx < N and 0 <= lz < N and 0 <= ly < HY:
            self.b[ly, lz, lx] = self.pal(st)

    def entite(self, x, y, z, nbt):
        if 0 <= x - self.x0 < N and 0 <= z - self.z0 < N:
            d = dict(nbt)
            d.update({'x': int(x), 'y': int(y), 'z': int(z)})
            self.entites.setdefault((x >> 4, z >> 4), []).append(d)

    # ------------------------------------------------------------------ sous-sol, surface, eau
    def remplir(self):
        P = self.pal
        h, eau, bio = self.h, self.eau, self.bio
        X = np.arange(self.x0, self.x0 + N)[None, :].repeat(N, 0)
        Z = np.arange(self.z0, self.z0 + N)[:, None].repeat(N, 1)
        g = self.plan['graine']
        r = B.aleatoire(X, Z, g + 1)
        prof_terre = (3 + (r * 3).astype(np.int32))
        ds = (B.aleatoire(X, Z, g + 2) * 8 - 4).astype(np.int32)          # limite deepslate ~y=0
        # pente (pour la roche à nu)
        hp = self.c['h'].astype(np.float64)
        gy, gx = np.gradient(hp)
        pente = np.hypot(gx, gy)[MARGE:MARGE + N, MARGE:MARGE + N]
        BI = T.BI
        sous_eau = eau > -999
        profondeur = np.where(sous_eau, eau - h, 0)
        # bloc de surface et sous-couche (2D)
        haut = np.full(h.shape, P('minecraft:grass_block[snowy=false]'), np.uint16)
        dessous = np.full(h.shape, P('minecraft:dirt'), np.uint16)
        roche = (pente > 2.3) | (h > 190)
        haut = np.where(roche, P('minecraft:stone'), haut)
        dessous = np.where(roche, P('minecraft:stone'), dessous)
        neige = bio == BI['snowy_slopes']
        haut = np.where(neige & ~roche, P('minecraft:snow_block'), haut)
        haut = np.where((bio == BI['grove']) & ~roche, P('minecraft:grass_block[snowy=true]'), haut)
        podzol = (bio == BI['old_growth_spruce_taiga']) & (r < 0.35)
        haut = np.where(podzol & ~roche, P('minecraft:podzol[snowy=false]'), haut)
        # rives et fonds
        plage = (~sous_eau) & (h <= 64) & (self._pres_eau(3))
        haut = np.where(plage, P('minecraft:sand'), haut)
        dessous = np.where(plage, P('minecraft:sand'), dessous)
        fond = np.where(profondeur <= 3, P('minecraft:sand'), np.where(r < 0.6, P('minecraft:gravel'), P('minecraft:clay')))
        haut = np.where(sous_eau, fond, haut)
        dessous = np.where(sous_eau, np.where(profondeur <= 3, P('minecraft:sand'), P('minecraft:gravel')), dessous)
        haut = np.where(sous_eau & (bio == BI['swamp']), P('minecraft:mud'), haut)
        # remplissage 3D par tranches de 16 (mémoire)
        pierre, ardoise, bed, eaub = P('minecraft:stone'), P('minecraft:deepslate[axis=y]'), P('minecraft:bedrock'), P('minecraft:water[level=0]')
        for y0 in range(0, HY, 16):
            ys = (np.arange(y0, y0 + 16) + Y0)[:, None, None]
            sec = np.zeros((16, N, N), np.uint16)
            solide = ys <= h[None]
            sec[solide] = pierre
            sec = np.where(solide & (ys < ds[None]), ardoise, sec)
            sec = np.where(solide & (ys > h[None] - prof_terre[None]) & (ys < h[None]), dessous[None], sec)
            sec = np.where(ys == h[None], haut[None], sec)
            sec = np.where((ys > h[None]) & (ys <= eau[None]), eaub, sec)
            if y0 == 0:
                rb = B.aleatoire(X, Z, g + 3)
                sec[0] = bed
                for k, seuil in ((1, 0.8), (2, 0.6), (3, 0.3)):
                    sec[k] = np.where(rb < seuil, bed, sec[k])
            self.b[y0:y0 + 16] = sec
        self.pente = pente
        self.haut_id = haut

    def _pres_eau(self, r):
        e = self.c['eau'] > -999
        m = np.zeros(e.shape, bool)
        for dz in range(-r, r + 1):
            for dx in range(-r, r + 1):
                m |= np.roll(np.roll(e, dz, 0), dx, 1)
        return m[MARGE:MARGE + N, MARGE:MARGE + N]

    # ------------------------------------------------------------------ minerais et poches de roche
    def minerais(self):
        P = self.pal
        pierre, ardoise = P('minecraft:stone'), P('minecraft:deepslate[axis=y]')
        g = self.plan['graine']
        for i, (st, st_ds, ymin, ymax, n, taille) in enumerate(MINERAIS):
            if VANILLE_SEULEMENT and not st.startswith('minecraft:'):
                continue
            a, a_ds = P(st), P(st_ds)
            rng = _rng(g, 7, self.rx, self.rz, i)
            nb = n * 1024
            cx = rng.integers(0, N, nb)
            cz = rng.integers(0, N, nb)
            cy = rng.integers(ymin, ymax + 1, nb) - Y0
            k = max(1, taille)
            dx = rng.normal(0, max(0.6, taille ** (1 / 3) * 0.6), (nb, k)).round().astype(np.int64)
            dy = rng.normal(0, max(0.6, taille ** (1 / 3) * 0.5), (nb, k)).round().astype(np.int64)
            dz = rng.normal(0, max(0.6, taille ** (1 / 3) * 0.6), (nb, k)).round().astype(np.int64)
            X = (cx[:, None] + dx).ravel()
            Y = (cy[:, None] + dy).ravel()
            Z = (cz[:, None] + dz).ravel()
            ok = (X >= 0) & (X < N) & (Z >= 0) & (Z < N) & (Y >= 1) & (Y < HY)
            X, Y, Z = X[ok], Y[ok], Z[ok]
            cur = self.b[Y, Z, X]
            self.b[Y[cur == pierre], Z[cur == pierre], X[cur == pierre]] = a
            self.b[Y[cur == ardoise], Z[cur == ardoise], X[cur == ardoise]] = a_ds

    # ------------------------------------------------------------------ grottes (vers) et lave profonde
    def grottes(self):
        P = self.pal
        lave = P('minecraft:lava[level=0]')
        g = self.plan['graine']
        C = 192
        protege = self.h - 6                      # jamais à moins de 6 blocs de la surface
        eau_col = self.eau > -999
        for gx in range((self.x0 - 256) // C, (self.x0 + N + 256) // C + 1):
            for gz in range((self.z0 - 256) // C, (self.z0 + N + 256) // C + 1):
                r = random.Random((g * 1000003 + gx * 92821 + gz * 68917) & 0xFFFFFFFF)
                for _ in range(r.randint(1, 5)):
                    x = gx * C + r.random() * C
                    z = gz * C + r.random() * C
                    y = r.uniform(-54, 40)
                    lacet = r.random() * 6.283
                    tang = r.uniform(-0.3, 0.3)
                    pts = []
                    rayon = r.uniform(1.6, 3.4) if r.random() < 0.85 else r.uniform(4, 6)
                    for k in range(r.randint(60, 220)):
                        lacet += r.uniform(-0.25, 0.25)
                        tang = max(-0.6, min(0.6, tang + r.uniform(-0.12, 0.12)))
                        x += np.cos(lacet) * np.cos(tang) * 1.2
                        z += np.sin(lacet) * np.cos(tang) * 1.2
                        y += np.sin(tang) * 1.0
                        y = max(-58, min(60, y))
                        pts.append((x, y, z, rayon * (0.8 + 0.4 * np.sin(k * 0.21))))
                    self._creuser(pts, protege, eau_col, lave)

    def _creuser(self, pts, protege, eau_col, lave):
        P = np.asarray(pts)
        lx = P[:, 0] - self.x0
        lz = P[:, 2] - self.z0
        if lx.max() < -4 or lx.min() > N + 4 or lz.max() < -4 or lz.min() > N + 4:
            return
        R = int(np.ceil(P[:, 3].max()))
        o = np.arange(-R, R + 1)
        OX, OY, OZ = np.meshgrid(o, o, o, indexing='ij')
        OX, OY, OZ = OX.ravel(), OY.ravel(), OZ.ravel()
        d2 = OX ** 2 + OY ** 2 + OZ ** 2
        X = (np.round(lx)[:, None] + OX[None]).astype(np.int64)
        Y = (np.round(P[:, 1])[:, None] - Y0 + OY[None]).astype(np.int64)
        Z = (np.round(lz)[:, None] + OZ[None]).astype(np.int64)
        m = d2[None] <= (P[:, 3] ** 2)[:, None]
        X, Y, Z = X[m], Y[m], Z[m]
        ok = (X >= 0) & (X < N) & (Z >= 0) & (Z < N) & (Y >= 1) & (Y < HY)
        X, Y, Z = X[ok], Y[ok], Z[ok]
        ok = (Y + Y0 < protege[Z, X]) & ~eau_col[Z, X]
        X, Y, Z = X[ok], Y[ok], Z[ok]
        self.b[Y, Z, X] = np.where(Y + Y0 < -55, lave, 0).astype(np.uint16)

    # ------------------------------------------------------------------ routes et ponts
    def routes(self):
        P = self.pal
        route = self.ci('route')
        ry = self.ci('route_y')
        rd = self.ci('route_d')
        rs = self.ci('route_s')
        rl = self.ci('route_l')
        pont = self.ci('pont')
        gris, blanc, jaune = P('minecraft:gray_concrete'), P('minecraft:white_concrete'), P('minecraft:yellow_concrete')
        fissure = P('minecraft:andesite')
        g = self.plan['graine']
        X = np.arange(self.x0, self.x0 + N)[None, :].repeat(N, 0)
        Z = np.arange(self.z0, self.z0 + N)[:, None].repeat(N, 1)
        r = B.aleatoire(X, Z, g + 5)
        surf = np.zeros(route.shape, np.uint16)
        surf = np.where(route == 1, gris, surf)
        surf = np.where(route == 2, gris, surf)
        surf = np.where(route == 3, np.where(r < 0.5, P('minecraft:dirt_path'), np.where(r < 0.8, P('minecraft:gravel'), P('minecraft:coarse_dirt'))), surf)
        surf = np.where(route == 4, P('minecraft:gravel'), surf)
        # marquage : autoroute (lignes de voies pointillées, bords blancs, terre-plein jaune), route (ligne jaune)
        auto = route == 1
        surf = np.where(auto & (rd < 0.7), jaune, surf)
        surf = np.where(auto & (np.abs(rd - 3.5) < 0.5) & ((rs % 12) < 5), blanc, surf)
        surf = np.where(auto & (rd > rl - 1), blanc, surf)
        rte = route == 2
        surf = np.where(rte & (rd < 0.5) & ((rs % 10) < 6), jaune, surf)
        # usure : fissures et herbe dans le bitume (apocalypse)
        surf = np.where(((route == 1) | (route == 2)) & (r < 0.04) & (surf == gris), fissure, surf)
        herbe = ((route == 1) | (route == 2)) & (r > 0.985)
        zz, xx = np.nonzero(surf > 0)
        yy = ry[zz, xx] - Y0
        okk = (yy >= 1) & (yy < HY - 6)
        zz, xx, yy = zz[okk], xx[okk], yy[okk]
        sur_pont = pont[zz, xx]
        self.b[yy, zz, xx] = surf[zz, xx]
        for k in range(1, 5):
            self.b[yy + k, zz, xx] = 0                    # dégagement au-dessus de la chaussée
        zh, xh = np.nonzero(herbe)
        self.b[ry[zh, xh] + 1 - Y0, zh, xh] = P('minecraft:grass')
        # ponts : tablier en béton, garde-corps, piliers tous les 12 blocs jusqu'au fond
        zp, xp = zz[sur_pont], xx[sur_pont]
        yp = yy[sur_pont]
        self.b[yp - 1, zp, xp] = P('minecraft:light_gray_concrete')
        bord = rd[zp, xp] > rl[zp, xp] - 0.8
        self.b[yp[bord] + 1, zp[bord], xp[bord]] = P('minecraft:andesite_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]')
        pil = ((rs[zp, xp] % 12) < 1.2) & (np.abs(rd[zp, xp] - rl[zp, xp] * 0.5) < 1.2)
        for (z1, x1, y1) in zip(zp[pil], xp[pil], yp[pil]):
            fond = self.h[z1, x1] - Y0
            self.b[fond:y1 - 1, z1, x1] = P('minecraft:stone_bricks')

    # ------------------------------------------------------------------ végétation
    def vegetation(self, gab):
        P = self.pal
        g = self.plan['graine']
        c = self.c
        noms = [b.split(':')[1] for b in T.BIOMES]
        pre = {esp: [(np.array([t[0] for t in v]), np.array([t[1] for t in v]), np.array([t[2] for t in v]),
                      np.array([P(t[3]) for t in v], np.uint16)) for v in var] for esp, var in gab.items()}
        cell = 4
        gxs = np.arange((self.x0 - MARGE) // cell, (self.x0 + N + MARGE) // cell)
        gzs = np.arange((self.z0 - MARGE) // cell, (self.z0 + N + MARGE) // cell)
        GZ, GX = np.meshgrid(gzs, gxs, indexing='ij')
        tx = GX * cell + (B.aleatoire(GX, GZ, g + 51) * cell).astype(np.int64)
        tz = GZ * cell + (B.aleatoire(GX, GZ, g + 52) * cell).astype(np.int64)
        tir = B.aleatoire(GX, GZ, g + 53)
        choix = B.aleatoire(GX, GZ, g + 54)
        var = (B.aleatoire(GX, GZ, g + 55) * 1000).astype(np.int64)
        ix = tx - (self.x0 - MARGE)
        iz = tz - (self.z0 - MARGE)
        ok = (ix >= 0) & (ix < N + 2 * MARGE) & (iz >= 0) & (iz < N + 2 * MARGE)
        herbe_ids = {P('minecraft:grass_block[snowy=false]'), P('minecraft:grass_block[snowy=true]'), P('minecraft:podzol[snowy=false]')}
        for (a, b_, cx_, cz_, t_, ch, vv) in zip(ix[ok], iz[ok], tx[ok], tz[ok], tir[ok], choix[ok], var[ok]):
            bi = noms[c['biome'][b_, a]]
            if bi not in flore.MELANGE:
                continue
            dens, mel = flore.MELANGE[bi]
            if t_ >= dens:
                continue
            if c['eau'][b_, a] > -999 or c['route'][b_, a] or c['site'][b_, a] or c['h'][b_, a] > 188:
                continue
            # pas d'arbre à côté d'une route
            if c['route'][max(0, b_ - 3):b_ + 4, max(0, a - 3):a + 4].any():
                continue
            tot = sum(w for _, w in mel)
            k = ch * tot
            esp = mel[-1][0]
            for e, w in mel:
                if k < w:
                    esp = e
                    break
                k -= w
            gx_, gy_, gz_, ids = pre[esp][vv % len(pre[esp])]
            base = int(c['h'][b_, a]) + 1
            lx = cx_ - self.x0 + gx_
            lz = cz_ - self.z0 + gz_
            ly = base - Y0 + gy_
            m = (lx >= 0) & (lx < N) & (lz >= 0) & (lz < N) & (ly >= 0) & (ly < HY)
            if not m.any():
                continue
            if 0 <= cx_ - self.x0 < N and 0 <= cz_ - self.z0 < N and int(self.b[base - 1 - Y0, cz_ - self.z0, cx_ - self.x0]) not in herbe_ids:
                continue
            lx, lz, ly, idm = lx[m], lz[m], ly[m], ids[m]
            libre = self.b[ly, lz, lx] == 0
            self.b[ly[libre], lz[libre], lx[libre]] = idm[libre]
        # végétation basse
        h = self.h
        X = np.arange(self.x0, self.x0 + N)[None, :].repeat(N, 0)
        Z = np.arange(self.z0, self.z0 + N)[:, None].repeat(N, 1)
        r = B.aleatoire(X, Z, g + 61)
        r2 = B.aleatoire(X, Z, g + 62)
        yy = h + 1 - Y0
        okc = (yy < HY)
        dessus_libre = self.b[np.clip(yy, 0, HY - 1), np.arange(N)[:, None], np.arange(N)[None, :]] == 0
        sol = self.b[np.clip(yy - 1, 0, HY - 1), np.arange(N)[:, None], np.arange(N)[None, :]]
        herbe = (sol == P('minecraft:grass_block[snowy=false]')) & dessus_libre & okc & (self.ci('site') == 0) & (self.ci('route') == 0)
        bio = self.bio
        BI = T.BI
        plante = np.zeros(h.shape, np.uint16)
        taiga = (bio == BI['taiga']) | (bio == BI['old_growth_spruce_taiga'])
        plante = np.where(herbe & (r < 0.28), P('minecraft:grass'), plante)
        plante = np.where(herbe & taiga & (r < 0.18), P('minecraft:fern'), plante)
        plante = np.where(herbe & taiga & (r > 0.995), P('minecraft:sweet_berry_bush[age=3]'), plante)
        champs = (bio == BI['plains']) | (bio == BI['meadow']) | (bio == BI['forest'])
        idx_fleur = (r2 * len(flore.FLEURS)).astype(np.int64)
        fleurs = np.array([P(f) for f in flore.FLEURS], np.uint16)
        plante = np.where(herbe & champs & (r > 0.965), fleurs[idx_fleur], plante)
        plante = np.where(herbe & (bio == BI['meadow']) & (r > 0.9), fleurs[idx_fleur], plante)
        # neige sur les hauteurs
        neige_ok = dessus_libre & okc & ((bio == BI['grove']) | (bio == BI['snowy_slopes'])) & (self.ci('route') == 0)
        plante = np.where(neige_ok & (plante == 0), P('minecraft:snow[layers=1]'), plante)
        # nénuphars dans le marais
        zz, xx = np.nonzero(plante > 0)
        self.b[yy[zz, xx], zz, xx] = plante[zz, xx]
        lil = (self.eau > -999) & (bio == BI['swamp']) & (r < 0.06)
        zz, xx = np.nonzero(lil)
        ye = self.eau[zz, xx] + 1 - Y0
        okl = ye < HY
        self.b[ye[okl], zz[okl], xx[okl]] = P('minecraft:lily_pad')

    # ------------------------------------------------------------------ écriture
    def ecrire(self, chemin):
        R = anvil.Region(self.rx, self.rz)
        pal = self.pal.l
        # biomes : 4x4x4, identiques sur toute la hauteur
        bio4 = self.bio[2::4, 2::4]
        for lcz in range(32):
            for lcx in range(32):
                cx, cz = self.rx * 32 + lcx, self.rz * 32 + lcz
                blocs = self.b[:, lcz * 16:(lcz + 1) * 16, lcx * 16:(lcx + 1) * 16]
                bi = bio4[lcz * 4:(lcz + 1) * 4, lcx * 4:(lcx + 1) * 4]
                biomes = np.broadcast_to(bi[None], (anvil.N_SECTIONS * 4, 4, 4))
                ent = self.entites.get((cx, cz), [])
                R.ajouter(cx, cz, anvil.chunk_nbt(cx, cz, blocs, pal, biomes, T.BIOMES, ent, y0=Y0))
        R.ecrire(chemin)


def generer(plan, rx, rz, dossier, sites=None, gab=None):
    reg = Region(plan, rx, rz)
    reg.remplir()
    reg.minerais()
    reg.grottes()
    reg.routes()
    if sites:
        sites.poser(reg)
    reg.vegetation(gab or flore.gabarits(plan['graine']))
    chemin = os.path.join(dossier, 'r.%d.%d.mca' % (rx, rz))
    reg.ecrire(chemin)
    return chemin
