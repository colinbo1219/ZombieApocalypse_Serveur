# -*- coding: utf-8 -*-
"""apercu : carte PNG de toute la région (1 pixel = pas blocs), pour vérifier le plan et le relief."""
import sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import plan as PL, terrain as T

def carte(chemin, pas=10, etiquettes=True):
    p = PL.construire()
    L = p['limite']
    xs = np.arange(-L, L, pas, dtype=np.float64)
    img = np.zeros((len(xs), len(xs), 3), np.uint8)
    t0 = time.time()
    for i in range(0, len(xs), 100):
        Z, X = np.meshgrid(xs[i:i + 100], xs, indexing='ij')
        c = T.champ(p, X, Z)
        h = c['h']
        col = np.zeros(h.shape + (3,), np.float64)
        base = {0: (110, 170, 70), 1: (60, 130, 50), 2: (90, 150, 70), 3: (50, 100, 60), 4: (35, 85, 50), 5: (200, 210, 210),
                6: (240, 240, 245), 7: (60, 110, 200), 8: (80, 110, 70), 9: (130, 180, 80), 10: (80, 145, 70)}
        for k, v in base.items():
            col[c['biome'] == k] = v
        ombre = 0.65 + 0.35 * np.clip((h - 50) / 110, 0, 1)
        col = col * ombre[..., None]
        eau = c['eau'] > -999
        col[eau] = (50, 90, 190)
        col[c['route'] == 1] = (40, 40, 40)
        col[c['route'] == 2] = (90, 90, 90)
        col[c['route'] == 3] = (150, 130, 100)
        col[c['pont']] = (200, 60, 60)
        col[c['site'] > 0] = col[c['site'] > 0] * 0.5 + np.array((255, 200, 0)) * 0.5
        img[i:i + 100] = np.clip(col, 0, 255).astype(np.uint8)
    im = Image.fromarray(img)
    if etiquettes:
        dr = ImageDraw.Draw(im)
        try:
            police = ImageFont.truetype('DejaVuSans.ttf', 12)
        except OSError:
            try:
                police = ImageFont.load_default(12)   # Pillow >= 10.1 : police avec accents
            except TypeError:
                police = ImageFont.load_default()
        for s in p['sites']:
            if s['type'] in ('camp_chasse', 'chalet', 'ferme'):
                continue
            x, z = (s['x'] + L) / pas, (s['z'] + L) / pas
            dr.text((x + 4, z - 6), s['nom'][:34], fill=(255, 255, 255), font=police, stroke_width=2, stroke_fill=(0, 0, 0))
    im.save(chemin)
    print('carte %s en %.0fs' % (chemin, time.time() - t0))

if __name__ == '__main__':
    carte(sys.argv[1] if len(sys.argv) > 1 else 'carte.png', int(sys.argv[2]) if len(sys.argv) > 2 else 10)
