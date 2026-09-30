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

def verifier(fichiers):
    erreurs, defs, appels = [], set(), {}
    for f in fichiers:
        lignes = open(f, encoding='utf-8').read().split('\n')
        prec_bloc, prec_ind = False, 0
        fonction_retour = False
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
            m = re.match(r'function (\w+)\(', s)
            if m:
                defs.add(m.group(1))
                fonction_retour = ind == 0 and '::' in s.split(')')[-1]
            elif ind == 0:
                fonction_retour = False
            if fonction_retour and re.match(r'wait ', s):
                erreurs.append(f'{f}:{n}: « wait » dans une fonction qui renvoie une valeur')
            for a in re.findall(r'\b(za_\w+)\(', code):
                appels.setdefault(a, f'{f}:{n}')
    for a, ou in sorted(appels.items()):
        if a not in defs:
            erreurs.append(f'{ou}: fonction {a} appelée mais jamais définie')
    return erreurs

if __name__ == '__main__':
    e = verifier(sys.argv[1:])
    print('\n'.join(e) if e else 'OK : aucune anomalie détectée')
    sys.exit(1 if e else 0)
