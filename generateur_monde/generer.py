# -*- coding: utf-8 -*-
"""generer : produit le monde complet de 10 000 x 10 000 (régions -10..9) + les données pour ZAMonde et Skript.

Usage (serveur ARRÊTÉ, depuis la racine du serveur) :
    python3 generateur_monde/generer.py                     # tout : world/region, placements.yml, données Skript
    python3 generateur_monde/generer.py --regions=-1,-1/0,0 # quelques régions seulement (test)
    python3 generateur_monde/generer.py --donnees           # seulement placements.yml + za_p73_sites_donnees.sk
Options : --sortie <dossier des .mca> (défaut world/region) · --processus N (défaut : nombre de cœurs) · --forcer
Une région déjà écrite est sautée (reprise après interruption), sauf avec --forcer.
"""
import argparse
import multiprocessing as mp
import os
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)

import plan as P  # noqa: E402

_ETAT = {}


def _init(vanille=False):
    import flore
    import monde
    import sites
    monde.VANILLE_SEULEMENT = vanille
    pl = P.construire()
    _ETAT['plan'] = pl
    _ETAT['gab'] = flore.gabarits(pl['graine'])
    _ETAT['sites'] = sites
    import signalisation
    _ETAT['panneaux'] = signalisation.panneaux(pl)


def _une(args):
    rx, rz, dossier = args
    import monde as M
    t = time.time()
    try:
        M.generer(_ETAT['plan'], rx, rz, dossier, _ETAT['sites'], _ETAT['gab'], _ETAT['panneaux'])
    except Exception as e:  # une région ratée ne doit pas arrêter les autres
        import traceback
        traceback.print_exc()
        return rx, rz, None, str(e)
    return rx, rz, time.time() - t, None


def regions_du_monde():
    n = -(-P.LIMITE // 512)  # 5000 -> 10 régions de chaque côté
    return [(rx, rz) for rz in range(-n, n) for rx in range(-n, n)]


# ---------------------------------------------------------------- données
def ecrire_placements(pl):
    """Fusionne les entrées ruines/arrivee dans plugins/ZAMonde/placements.yml (les autres structures sont gardées)."""
    import sites
    chemin = os.path.join(RACINE, 'plugins', 'ZAMonde', 'placements.yml')
    neuf = sites.placements(pl)
    nos = {l[:-1] for l in neuf.splitlines() if l and not l.startswith((' ', '#'))}
    garde = []
    if os.path.isfile(chemin):
        bloc = None
        for l in open(chemin, encoding='utf-8').read().splitlines():
            if l and not l.startswith((' ', '#')):
                bloc = l.split(':')[0].strip().strip("'\"")
            if bloc is None or bloc not in nos:
                if not l.startswith('# Généré par generateur_monde'):
                    garde.append(l)
    texte = neuf + ('\n'.join(garde) + '\n' if any(g.strip() for g in garde) else '')
    open(chemin, 'w', encoding='utf-8').write(texte)
    return chemin


ZOMBIES = {
    'militaire': 'ZA_Soldat_Infecte,ZA_Soldat_Infecte,ZA_Armored,ZA_Shielded',
    'norda': 'ZA_Medecin_Infecte,ZA_Patient_Infecte,ZA_Spitter,ZA_Observer',
    'barrage': 'ZA_Ouvrier_Infecte,ZA_Ouvrier_Infecte,ZA_Ouvrier_Brule',
    'industriel': 'ZA_Ouvrier_Infecte,ZA_Ouvrier_Brule,ZA_Brute',
    'village': 'ZA_Citoyen_Infecte,ZA_Citoyen_Infecte,ZA_Shambler,ZA_Child,ZA_Pompier_Infecte',
    'ferme': 'ZA_Citoyen_Infecte,ZA_Shambler,ZA_Crawler',
    'station': 'ZA_Pompier_Infecte,ZA_Citoyen_Infecte,ZA_Ouvrier_Brule',
    'motel': 'ZA_Citoyen_Infecte,ZA_FakeDead,ZA_Stalker',
    'checkpoint': 'ZA_Soldat_Infecte,ZA_Policier_Infecte,ZA_Armored',
    'emetteur': 'ZA_Ouvrier_Infecte,ZA_Screamer',
    'carriere': 'ZA_Ouvrier_Infecte,ZA_Brute',
    'chalet': 'ZA_Citoyen_Infecte,ZA_Stalker',
    'camp_chasse': 'ZA_Stalker,ZA_Crawler',
    'arrivee': 'ZA_Soldat_Infecte,ZA_Citoyen_Infecte',
}


def ecrire_skript(pl):
    """za_p73_sites_donnees.sk : liste des sites (généré, ne pas modifier à la main)."""
    import terrain as T
    import sites
    lignes = []
    for s in pl['sites']:
        if s['type'] == 'ruines':
            continue
        y = T.y_site(s) + 1
        nom = s['nom'].replace('"', "'").replace('%', '%%').replace('|', '/')
        lignes.append('%s|%s|%s|%d|%d|%d|%d|%d|%s' % (s['id'], s['type'], nom, s['x'], y, s['z'],
                                                     s['larg'] // 2 + 8, s['prof'] // 2 + 8, ZOMBIES.get(s['type'], '')))
    ruine = next(s for s in pl['sites'] if s['type'] == 'ruines')
    st = sites.structure_de(ruine, pl)
    bx, by, bz = sites.base_de(ruine, st)
    out = ['# =====================================================================',
           '#  ZombieApocalypse - DONNÉES DU MONDE GÉNÉRÉ (généré par generateur_monde/generer.py : NE PAS MODIFIER)',
           '#  id|type|nom|x|y|z|demi-largeur|demi-profondeur|zombies — lu par za_p73_sites.sk',
           '# =====================================================================',
           '',
           'function za_sites_base_ruines() :: text:',
           '    return "%d;%d;%d"' % (bx, by, bz),
           '',
           'function za_sites_donnees() :: texts:']
    for l in lignes:
        out.append('    add "%s" to {_r::*}' % l)
    out.append('    return {_r::*}')
    chemin = os.path.join(RACINE, 'plugins', 'Skript', 'scripts', 'za_p73_sites_donnees.sk')
    open(chemin, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    return chemin


# ---------------------------------------------------------------- lanceur
def main():
    ap = argparse.ArgumentParser(description='Génère le monde de Saint-Aurèle (10 000 x 10 000).')
    ap.add_argument('--sortie', default=os.path.join(RACINE, 'world', 'region'))
    ap.add_argument('--processus', type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument('--regions', help='liste rx,rz séparés par / (écrire --regions=-1,-1/0,0 ; défaut : tout le monde)')
    ap.add_argument('--donnees', action='store_true', help='seulement placements.yml et les données Skript')
    ap.add_argument('--forcer', action='store_true', help='réécrire les régions déjà présentes')
    ap.add_argument('--vanille', action='store_true', help='blocs 100 %% vanilla (test avec un serveur vanilla, pas pour le vrai monde)')
    a = ap.parse_args()
    if a.vanille:
        os.environ['ZA_VANILLE'] = '1'

    pl = P.construire()
    print('placements :', ecrire_placements(pl))
    print('Skript     :', ecrire_skript(pl))
    if a.donnees:
        return

    os.makedirs(a.sortie, exist_ok=True)
    if a.regions:
        liste = [tuple(int(v) for v in r.split(',')) for r in a.regions.split('/') if r]
    else:
        liste = regions_du_monde()
    if not a.forcer:
        liste = [(rx, rz) for (rx, rz) in liste
                 if not os.path.isfile(os.path.join(a.sortie, 'r.%d.%d.mca' % (rx, rz)))]
    n = len(liste)
    print('%d régions à générer dans %s avec %d processus (~8 s et ~1 Go de mémoire par processus)'
          % (n, a.sortie, a.processus))
    t0 = time.time()
    fait = 0
    erreurs = []
    with mp.Pool(a.processus, initializer=_init, initargs=(a.vanille,)) as pool:
        for rx, rz, dt, err in pool.imap_unordered(_une, [(rx, rz, a.sortie) for (rx, rz) in liste]):
            fait += 1
            if err:
                erreurs.append((rx, rz, err))
                print('  r.%d.%d : ERREUR %s' % (rx, rz, err))
                continue
            reste = (time.time() - t0) / fait * (n - fait)
            print('  r.%d.%d.mca  %.1f s   [%d/%d, reste ~%d min]' % (rx, rz, dt, fait, n, reste // 60), flush=True)
    print('Terminé en %d min. %d erreur(s).' % ((time.time() - t0) // 60, len(erreurs)))
    if erreurs:
        print('Relancer la même commande : seules les régions manquantes seront refaites.')
        sys.exit(1)


if __name__ == '__main__':
    main()
