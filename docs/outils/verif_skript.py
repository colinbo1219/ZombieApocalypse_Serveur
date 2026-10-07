#!/usr/bin/env python3
# Vérification statique légère des scripts Skript (pas de serveur) :
# indentation (multiples de 4, pas de tabulation), guillemets fermés, % appariés dans les chaînes,
# ligne terminée par ':' suivie d'un bloc indenté, fonctions appelées mais jamais définies.
# Usage : python3 docs/outils/verif_skript.py plugins/Skript/scripts/*.sk
import re, sys

def chaines(ligne):
    """Découpe une ligne en (code, [chaînes]) ; les "" dans une chaîne sont des guillemets échappés."""
    code, ch, i, dans, cur = [], [], 0, False, ''
    while i < len(ligne):
        c = ligne[i]
        if dans:
            if c == '"':
                if i + 1 < len(ligne) and ligne[i + 1] == '"':
                    cur += '"'; i += 2; continue
                dans = False; ch.append(cur); cur = ''
            else:
                cur += c
        else:
            if c == '"':
                dans = True
            elif c == '#' and (i == 0 or ligne[i - 1] in ' \t'):
                break
            else:
                code.append(c)
        i += 1
    return ''.join(code), ch, dans

AVERTISSEMENTS = []


def verifier(fichiers):
    erreurs, defs, appels = [], set(), {}
    commandes, fonctions = {}, {}
    for f in fichiers:
        lignes = open(f, encoding='utf-8').read().split('\n')
        prec_bloc, prec_ind = False, 0
        fonction_retour = False
        args_cmd = []       # types des arguments de la commande en cours
        boucles = []        # (indentation, boucle sur une variable liste ?)
        for n, l in enumerate(lignes, 1):
            if '\t' in l[:len(l) - len(l.lstrip())]:
                erreurs.append(f'{f}:{n}: tabulation dans l\'indentation')
            s = l.strip()
            if not s or s.startswith('#'):
                continue
            ind = len(l) - len(l.lstrip(' '))
            if ind % 4:
                erreurs.append(f'{f}:{n}: indentation non multiple de 4 ({ind})')
            if prec_bloc and ind <= prec_ind:
                erreurs.append(f'{f}:{n}: bloc vide après une ligne terminée par « : »')
            code, ch, ouvert = chaines(l)
            if ouvert:
                erreurs.append(f'{f}:{n}: guillemet non fermé')
            for c in ch:
                c2 = c.replace('%%', '')
                # expressions imbriquées (%{_a::%{_b}%}%) : on compte simplement la parité
                if c2.count('%') % 2:
                    erreurs.append(f'{f}:{n}: nombre impair de % dans « {c[:60]} »')
            cs = code.rstrip()
            prec_bloc = cs.endswith(':') and not cs.startswith('#')
            prec_ind = ind
            # pièges vus sur le vrai serveur (Skript 2.9.5)
            while boucles and boucles[-1][0] >= ind:
                boucles.pop()
            if re.search(r'loop-index-\d', l):
                erreurs.append(f'{f}:{n}: « loop-index-N » n\'existe pas (Skript : « There\'s no loop that matches ») ; '
                               f'boucler sur « indices of {{_x::*}} » et lire loop-value-N')
            elif 'loop-index' in code and sum(1 for b in boucles if b[1]) >= 2:
                AVERTISSEMENTS.append(f'{f}:{n}: « loop-index » dans des boucles imbriquées sur des listes : ambigu, '
                                      f'préférer « loop indices of ... »')
            if re.search(r'\bpush\b.*\btowards\b', code):
                erreurs.append(f'{f}:{n}: « push ... towards » n\'est pas compris par Skript 2.9.5 ; '
                               f'calculer le vecteur et « add vector(...) to velocity of ... »')
            if ind == 0:
                args_cmd = re.findall(r'<([\w ]+)>', s) if s.startswith('command ') else []
            for mo in re.finditer(r'\barg[- ](\d)\s+is\s+(?:not\s+)?"', l):
                k = int(mo.group(1)) - 1
                if k < len(args_cmd) and args_cmd[k].strip() in ('number', 'integer', 'num', 'int'):
                    erreurs.append(f'{f}:{n}: arg-{k + 1} est un <{args_cmd[k]}> comparé à du texte '
                                   f'(« Can\'t compare a number with a text ») : déclarer <text> et utiliser '
                                   f'(arg-{k + 1} parsed as number) ? 0 là où il sert de nombre')
            ml = re.match(r'loop (.*):$', s)
            if ml:
                boucles.append((ind, bool(re.search(r'\{[^}]*::\*\}', ml.group(1))) and not ml.group(1).startswith('indices')))
            mc = re.match(r'command /([\w-]+)', s) if ind == 0 else None
            if mc:
                nom = mc.group(1).lower()
                if nom in commandes:
                    erreurs.append(f'{f}:{n}: commande /{nom} déjà définie ({commandes[nom]})')
                commandes.setdefault(nom, f'{f}:{n}')
            m = re.match(r'function (\w+)\(', s)
            if m:
                if ind == 0 and m.group(1) in fonctions:
                    erreurs.append(f'{f}:{n}: fonction {m.group(1)} déjà définie ({fonctions[m.group(1)]})')
                if ind == 0:
                    fonctions.setdefault(m.group(1), f'{f}:{n}')
                defs.add(m.group(1))
                fonction_retour = ind == 0 and '::' in s.split(')')[-1]
            elif ind == 0:
                fonction_retour = False
            if fonction_retour and re.match(r'wait ', s):
                erreurs.append(f'{f}:{n}: « wait » dans une fonction qui renvoie une valeur')
            for a in re.findall(r'\b(za_\w+)\(', code):
                appels.setdefault(a, f'{f}:{n}')
    # « delete {za::x::*} » efface tout un espace de noms : dangereux si un autre script y range ses données
    usages = {}
    for f in fichiers:
        for m in re.finditer(r'\{za::([a-z0-9_]+)::', open(f, encoding='utf-8').read()):
            usages.setdefault(m.group(1), set()).add(f)
    for f in fichiers:
        for n, l in enumerate(open(f, encoding='utf-8').read().split('\n'), 1):
            m = re.search(r'delete \{za::([a-z0-9_]+)::\*\}', l)
            if m and len(usages.get(m.group(1), ())) > 1:
                autres = sorted(x.split('/')[-1] for x in usages[m.group(1)] if x != f)
                AVERTISSEMENTS.append(f'{f}:{n}: « delete {{za::{m.group(1)}::*}} » touche aussi {", ".join(autres)} (voulu ?)')
    for a, ou in sorted(appels.items()):
        if a not in defs:
            erreurs.append(f'{ou}: fonction {a} appelée mais jamais définie')
    return erreurs

if __name__ == '__main__':
    e = verifier(sys.argv[1:])
    for a in AVERTISSEMENTS:
        print('AVERTISSEMENT ' + a)
    print('\n'.join(e) if e else 'OK : aucune anomalie détectée')
    sys.exit(1 if e else 0)
