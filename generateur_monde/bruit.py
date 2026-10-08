# -*- coding: utf-8 -*-
"""bruit : bruits de valeur 2D/3D déterministes et vectorisés (numpy), sans dépendance externe.
Même graine + mêmes coordonnées = même valeur, quel que soit le découpage en régions (pas de couture)."""
import numpy as np

_M1 = np.uint64(0x9E3779B97F4A7C15)
_M2 = np.uint64(0xBF58476D1CE4E5B9)
_M3 = np.uint64(0x94D049BB133111EB)


def _melange(h):
    with np.errstate(over='ignore'):
        h = (h ^ (h >> np.uint64(30))) * _M2
        h = (h ^ (h >> np.uint64(27))) * _M3
        h = h ^ (h >> np.uint64(31))
    return h


def hachage(ix, iz, graine, iy=None):
    """Entiers (tableaux) -> uint64 pseudo-aléatoire."""
    with np.errstate(over='ignore'):
        h = np.asarray(ix, np.int64).astype(np.uint64) * _M1
        h = _melange(h ^ (np.asarray(iz, np.int64).astype(np.uint64) + np.uint64(int(graine) & 0xFFFFFFFFFFFFFFFF) * _M2))
        if iy is not None:
            h = _melange(h ^ (np.asarray(iy, np.int64).astype(np.uint64) * _M3))
    return h


def aleatoire(ix, iz, graine, iy=None):
    """Flottant uniforme [0, 1) par point entier."""
    return (hachage(ix, iz, graine, iy) >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def _lisse(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def valeur(x, z, freq, graine):
    """Bruit de valeur 2D dans [-1, 1]. x, z : tableaux (mêmes formes)."""
    fx = np.asarray(x, np.float64) * freq
    fz = np.asarray(z, np.float64) * freq
    ix = np.floor(fx).astype(np.int64)
    iz = np.floor(fz).astype(np.int64)
    tx = _lisse(fx - ix)
    tz = _lisse(fz - iz)
    a = aleatoire(ix, iz, graine)
    b = aleatoire(ix + 1, iz, graine)
    c = aleatoire(ix, iz + 1, graine)
    d = aleatoire(ix + 1, iz + 1, graine)
    v = (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz
    return v * 2 - 1


def fbm(x, z, freq, graine, octaves=4, gain=0.5, lacunarite=2.0):
    """Somme d'octaves normalisée dans ~[-1, 1]."""
    s = 0.0
    amp = 1.0
    tot = 0.0
    f = freq
    for o in range(octaves):
        s = s + amp * valeur(x, z, f, graine + 101 * o)
        tot += amp
        amp *= gain
        f *= lacunarite
    return s / tot


def crete(x, z, freq, graine, octaves=4):
    """Bruit de crêtes (montagnes) dans [0, 1]."""
    s = 0.0
    amp = 1.0
    tot = 0.0
    f = freq
    for o in range(octaves):
        r = 1 - np.abs(valeur(x, z, f, graine + 131 * o))
        s = s + amp * r * r
        tot += amp
        amp *= 0.5
        f *= 2.0
    return s / tot


def lisse_pas(a, b, v):
    """smoothstep de a à b (a peut être > b)."""
    t = np.clip((np.asarray(v, np.float64) - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)
