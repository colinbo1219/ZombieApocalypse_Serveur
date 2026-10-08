# -*- coding: utf-8 -*-
"""anvil : écriture directe des chunks Minecraft 1.20.1 (format Anvil, DataVersion 3465).

Un chunk est décrit par un tableau numpy de blocs [y][z][x] (indices dans une palette de chaînes « id[props] »),
un tableau de biomes [y/4][z/4][x/4] (indices dans une palette de biomes) et une liste d'entités de bloc.
Le serveur recalcule lui-même la lumière (isLightOn = 0) et les cartes de hauteur (absentes) au chargement.
"""
import io
import os
import struct
import zlib

import numpy as np

DATA_VERSION = 3465          # Minecraft 1.20.1
Y_MIN = -64
Y_MAX = 320                  # exclu
N_SECTIONS = (Y_MAX - Y_MIN) // 16

# ============================================================================ NBT (écriture binaire)
TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG, TAG_FLOAT, TAG_DOUBLE = 0, 1, 2, 3, 4, 5, 6
TAG_BYTE_ARRAY, TAG_STRING, TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = 7, 8, 9, 10, 11, 12


class Byte(int):
    pass


class Short(int):
    pass


class Long(int):
    pass


class Float(float):
    pass


class LongArray:
    """Tableau de longs signés (numpy int64 ou uint64 réinterprété)."""
    def __init__(self, a):
        self.a = np.asarray(a).astype('>i8', copy=False) if np.asarray(a).dtype != np.uint64 \
            else np.asarray(a).view(np.int64).astype('>i8')


class IntArray:
    def __init__(self, a):
        self.a = np.asarray(a, dtype='>i4')


class Liste:
    """Liste NBT typée : Liste(TAG_COMPOUND, [...])."""
    def __init__(self, tag, items):
        self.tag = tag
        self.items = list(items)


def _tag_de(v):
    if isinstance(v, Byte) or isinstance(v, bool):
        return TAG_BYTE
    if isinstance(v, Short):
        return TAG_SHORT
    if isinstance(v, Long):
        return TAG_LONG
    if isinstance(v, Float):
        return TAG_FLOAT
    if isinstance(v, int):
        return TAG_INT
    if isinstance(v, float):
        return TAG_DOUBLE
    if isinstance(v, str):
        return TAG_STRING
    if isinstance(v, Liste):
        return TAG_LIST
    if isinstance(v, dict):
        return TAG_COMPOUND
    if isinstance(v, LongArray):
        return TAG_LONG_ARRAY
    if isinstance(v, IntArray):
        return TAG_INT_ARRAY
    raise TypeError('type NBT inconnu : %r' % type(v))


def _str(b, s):
    e = s.encode('utf-8')   # (le « modified UTF-8 » de Java ne diffère que pour \0 et les emojis)
    b.write(struct.pack('>H', len(e)))
    b.write(e)


def _payload(b, tag, v):
    if tag == TAG_BYTE:
        b.write(struct.pack('>b', int(v)))
    elif tag == TAG_SHORT:
        b.write(struct.pack('>h', v))
    elif tag == TAG_INT:
        b.write(struct.pack('>i', v))
    elif tag == TAG_LONG:
        b.write(struct.pack('>q', v))
    elif tag == TAG_FLOAT:
        b.write(struct.pack('>f', v))
    elif tag == TAG_DOUBLE:
        b.write(struct.pack('>d', v))
    elif tag == TAG_STRING:
        _str(b, v)
    elif tag == TAG_LIST:
        b.write(struct.pack('>bi', v.tag if v.items else TAG_END, len(v.items)))
        for it in v.items:
            _payload(b, v.tag, it)
    elif tag == TAG_COMPOUND:
        for k, x in v.items():
            t = _tag_de(x)
            b.write(struct.pack('>b', t))
            _str(b, k)
            _payload(b, t, x)
        b.write(b'\x00')
    elif tag == TAG_LONG_ARRAY:
        b.write(struct.pack('>i', len(v.a)))
        b.write(v.a.tobytes())
    elif tag == TAG_INT_ARRAY:
        b.write(struct.pack('>i', len(v.a)))
        b.write(v.a.tobytes())


def nbt_octets(racine):
    b = io.BytesIO()
    b.write(struct.pack('>b', TAG_COMPOUND))
    _str(b, '')
    _payload(b, TAG_COMPOUND, racine)
    return b.getvalue()


# ============================================================================ palettes compactées
def empaqueter(indices, bits):
    """Indices (uint, taille 4096 ou 64) -> longs, sans chevauchement entre longs (format 1.16+)."""
    par_long = 64 // bits
    n = len(indices)
    nl = (n + par_long - 1) // par_long
    v = np.zeros(nl * par_long, np.uint64)
    v[:n] = indices.astype(np.uint64)
    v = v.reshape(nl, par_long)
    decal = (np.arange(par_long, dtype=np.uint64) * np.uint64(bits))
    return np.bitwise_or.reduce(v << decal, axis=1)


def etat_nbt(st):
    """'minecraft:x[a=b,c=d]' -> {'Name':..., 'Properties':{...}}"""
    if '[' in st:
        n, rest = st.split('[', 1)
        props = {}
        for kv in rest.rstrip(']').split(','):
            if kv:
                k, v = kv.split('=')
                props[k] = v
        return {'Name': n, 'Properties': props} if props else {'Name': n}
    return {'Name': st}


_ETATS_CACHE = {}


def _etat(st):
    r = _ETATS_CACHE.get(st)
    if r is None:
        r = _ETATS_CACHE[st] = etat_nbt(st)
    return r


def section_blocs(sec, palette):
    """sec : uint16 [16][16][16] (y,z,x) d'indices dans `palette` -> compound block_states."""
    u, inv = np.unique(sec, return_inverse=True)
    pal = Liste(TAG_COMPOUND, [_etat(palette[i]) for i in u])
    if len(u) == 1:
        return {'palette': pal}
    bits = max(4, int(np.ceil(np.log2(len(u)))))
    return {'palette': pal, 'data': LongArray(empaqueter(inv.reshape(-1), bits))}


def section_biomes(b, palette_b):
    """b : uint8 [4][4][4] (y,z,x) d'indices dans `palette_b` -> compound biomes."""
    u, inv = np.unique(b, return_inverse=True)
    pal = Liste(TAG_STRING, [palette_b[i] for i in u])
    if len(u) == 1:
        return {'palette': pal}
    bits = max(1, int(np.ceil(np.log2(len(u)))))
    return {'palette': pal, 'data': LongArray(empaqueter(inv.reshape(-1), bits))}


def chunk_nbt(cx, cz, blocs, palette, biomes, palette_b, entites_bloc=(), y0=Y_MIN):
    """blocs : uint16 [H][16][16] depuis y0 (multiple de 16) ; biomes : uint8 [N_SECTIONS*4][4][4] depuis Y_MIN."""
    H = blocs.shape[0]
    sections = []
    air = palette.index('minecraft:air') if 'minecraft:air' in palette else None
    for s in range(N_SECTIONS):
        ys = Y_MIN + s * 16
        a = ys - y0
        if 0 <= a and a + 16 <= H:
            sec = blocs[a:a + 16]
            bs = section_blocs(sec, palette)
        else:
            bs = {'palette': Liste(TAG_COMPOUND, [{'Name': 'minecraft:air'}])}
        sections.append({'Y': Byte(s + Y_MIN // 16), 'block_states': bs,
                         'biomes': section_biomes(biomes[s * 4:(s + 1) * 4], palette_b)})
    return {
        'DataVersion': DATA_VERSION,
        'xPos': cx, 'zPos': cz, 'yPos': Y_MIN // 16,
        'Status': 'minecraft:full',
        'LastUpdate': Long(0), 'InhabitedTime': Long(0),
        'isLightOn': Byte(0),
        'sections': Liste(TAG_COMPOUND, sections),
        'block_entities': Liste(TAG_COMPOUND, list(entites_bloc)),
        'structures': {'References': {}, 'starts': {}},
        'fluid_ticks': Liste(TAG_COMPOUND, []),
        'block_ticks': Liste(TAG_COMPOUND, []),
        'PostProcessing': Liste(TAG_LIST, [Liste(TAG_SHORT, []) for _ in range(N_SECTIONS)]),
    }


# ============================================================================ fichiers de région
class Region:
    """Fichier r.<rx>.<rz>.mca : 32 x 32 chunks. Les chunks sont ajoutés en octets compressés (zlib)."""

    def __init__(self, rx, rz):
        self.rx, self.rz = rx, rz
        self.chunks = {}

    def ajouter(self, cx, cz, racine):
        self.chunks[(cx & 31, cz & 31)] = zlib.compress(nbt_octets(racine), 6)

    def ecrire(self, chemin):
        entetes = bytearray(8192)
        corps = io.BytesIO()
        secteur = 2
        for (lx, lz), data in sorted(self.chunks.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            bloc = struct.pack('>IB', len(data) + 1, 2) + data
            n = (len(bloc) + 4095) // 4096
            if n > 255:
                raise ValueError('chunk trop gros (%d secteurs)' % n)
            i = 4 * (lx + lz * 32)
            entetes[i:i + 4] = struct.pack('>I', (secteur << 8) | n)
            corps.write(bloc)
            corps.write(b'\x00' * (n * 4096 - len(bloc)))
            secteur += n
        # écriture atomique : une région interrompue ne laisse pas de fichier tronqué
        with open(chemin + '.tmp', 'wb') as f:
            f.write(entetes)
            f.write(corps.getvalue())
        os.replace(chemin + '.tmp', chemin)


# ============================================================================ relecture (contrôle)
def lire_nbt(data):
    b = io.BytesIO(data)

    def rd(fmt):
        s = struct.calcsize(fmt)
        return struct.unpack(fmt, b.read(s))

    def rstr():
        (n,) = rd('>H')
        return b.read(n).decode('utf-8', 'replace')

    def payload(t):
        if t == TAG_BYTE:
            return rd('>b')[0]
        if t == TAG_SHORT:
            return rd('>h')[0]
        if t == TAG_INT:
            return rd('>i')[0]
        if t == TAG_LONG:
            return rd('>q')[0]
        if t == TAG_FLOAT:
            return rd('>f')[0]
        if t == TAG_DOUBLE:
            return rd('>d')[0]
        if t == TAG_BYTE_ARRAY:
            (n,) = rd('>i')
            return b.read(n)
        if t == TAG_STRING:
            return rstr()
        if t == TAG_LIST:
            et, n = rd('>bi')
            return [payload(et) for _ in range(n)]
        if t == TAG_COMPOUND:
            d = {}
            while True:
                (et,) = rd('>b')
                if et == TAG_END:
                    return d
                k = rstr()
                d[k] = payload(et)
        if t == TAG_INT_ARRAY:
            (n,) = rd('>i')
            return np.frombuffer(b.read(4 * n), '>i4')
        if t == TAG_LONG_ARRAY:
            (n,) = rd('>i')
            return np.frombuffer(b.read(8 * n), '>i8')
        raise ValueError('tag %d' % t)

    (t,) = rd('>b')
    rstr()
    return payload(t)


def lire_region(chemin):
    """-> {(lx,lz): racine NBT}"""
    with open(chemin, 'rb') as f:
        d = f.read()
    res = {}
    for i in range(1024):
        (loc,) = struct.unpack('>I', d[4 * i:4 * i + 4])
        if loc == 0:
            continue
        off = (loc >> 8) * 4096
        (lng, comp) = struct.unpack('>IB', d[off:off + 5])
        brut = d[off + 5:off + 4 + lng]
        brut = zlib.decompress(brut) if comp == 2 else brut
        res[(i % 32, i // 32)] = lire_nbt(brut)
    return res
