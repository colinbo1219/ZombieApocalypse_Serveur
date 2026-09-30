# -*- coding: utf-8 -*-
"""vue : rendu du dessus d'une région générée (bloc le plus haut), pour contrôle visuel."""
import numpy as np
from PIL import Image

COUL = {'grass_block': (95, 159, 53), 'dirt': (134, 96, 67), 'stone': (125, 125, 125), 'water': (50, 90, 190), 'sand': (219, 207, 163),
        'gravel': (136, 126, 126), 'spruce_leaves': (50, 85, 50), 'oak_leaves': (70, 130, 40), 'birch_leaves': (110, 150, 70),
        'spruce_log': (60, 45, 30), 'oak_log': (100, 80, 50), 'birch_log': (200, 200, 190), 'gray_concrete': (60, 60, 65),
        'white_concrete': (230, 230, 230), 'yellow_concrete': (230, 190, 40), 'snow': (245, 250, 250), 'snow_block': (245, 250, 250),
        'podzol': (90, 65, 30), 'grass': (100, 170, 60), 'fern': (80, 140, 60), 'dirt_path': (150, 120, 70), 'coarse_dirt': (120, 90, 60),
        'clay': (160, 165, 180), 'mud': (60, 55, 60), 'lily_pad': (30, 120, 40), 'andesite': (136, 136, 136), 'light_gray_concrete': (155, 155, 150)}

def rendu(reg, chemin, ombrage=True):
    b = reg.b
    haut = (b > 0)
    idx = b.shape[0] - 1 - np.argmax(haut[::-1], axis=0)
    top = np.take_along_axis(b, idx[None], 0)[0]
    img = np.zeros(top.shape + (3,), np.float64)
    for i, st in enumerate(reg.pal.l):
        n = st.split(':')[1].split('[')[0]
        c = COUL.get(n)
        if c is None:
            h = hash(n) & 0xFFFFFF
            c = (h & 255, (h >> 8) & 255, (h >> 16) & 255)
        img[top == i] = c
    if ombrage:
        gz, gx = np.gradient(idx.astype(float))
        img *= np.clip(1 + 0.08 * (gx - gz), 0.6, 1.3)[..., None]
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(chemin)
