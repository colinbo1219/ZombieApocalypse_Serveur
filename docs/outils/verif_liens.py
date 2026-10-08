#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verif_liens : « un système n'est pas fini tant qu'il n'interagit pas avec les autres ».

Liste les types d'événements publiés dans la Chronique (moteur Java + za_mot_evt des scripts) qui ne déclenchent
aucune conséquence propre : ni règle de reactions.yml, ni règle de mémoire, ni traitement dans le moteur.
Ils alimentent quand même les rumeurs et Léa (selon leur importance), mais rien d'autre ne bouge.
Usage : python3 docs/outils/verif_liens.py   (depuis la racine du dépôt)
"""
import glob
import re

pub = {}
for f in glob.glob('moteur/src/za/moteur/**/*.java', recursive=True):
    for m in re.findall(r'new Evenement\("([a-z_0-9]+)"', open(f, encoding='utf-8').read()):
        pub.setdefault(m, set()).add(f.split('/')[-1])
for f in glob.glob('plugins/Skript/scripts/*.sk'):
    t = open(f, encoding='utf-8').read()
    for m in re.findall(r'za_mot_evt\("([a-z_0-9]+)"', t):
        pub.setdefault(m, set()).add(f.split('/')[-1])
reac = open('plugins/ZAMoteur/reactions.yml', encoding='utf-8').read()
si = set(re.findall(r'si:\s*([a-z_0-9]+)', reac))
java = ''.join(open(f, encoding='utf-8').read() for f in glob.glob('moteur/src/za/moteur/**/*.java', recursive=True))
cons = set(re.findall(r'case "([a-z_0-9]+)"', java)) | set(re.findall(r'\.equals\("([a-z_0-9]+)"\)', java))
cons |= set(re.findall(r'regle\("([a-z_0-9]+)"', java))
imp = [k for k in sorted(pub) if k not in si and k not in cons and not k.endswith('_')]
print('%d types publiés, %d sans conséquence propre :' % (len(pub), len(imp)))
for k in imp:
    print('  %-26s %s' % (k, ', '.join(sorted(pub[k]))))
