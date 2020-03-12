#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from random import random, randrange

# Couleur associée à l'état
STATE = {
    "SAIN":0,
    "MALADE":1,
    "IMMUN": 2,
    "QUARANTAINE": 3,
    "DECEDE": 4
}

class diseaseBoard:
    def __init__(self, size, tour, nb_clusters):

        self._longueur = size
        self._largeur  = size

        self._nb_clusters = nb_clusters

        self._nb_tour  = tour
        self._tour_actuel = 0

        self._taux_immunite = 0.2

        self._taux_mortalite = 0.03
        self._delai_mortalite = 6

        self._delai_retablissement = 3

        self._delai_quarantaine = 2
        self._taux_quarantaine  = 0.2

        # Par défaut, R0 = 3, et il y a 8 cases adjacentes
        self._proba_contag = 1 / 8

        self._etat_db = []
        self._date_contamination = np.zeros((self._longueur, self._largeur), dtype=int)

        self.init_board()

    def setTauxImmunite(self, taux_immunite):
        self._taux_immunite = taux_immunite
        # Nécessité de refaire la map
        self.init_board()

    def setProbaContag(self, proba_contag):
        self._proba_contag = proba_contag

    def setTauxQuarantaine(self, taux_quarantaine):
        self._taux_quarantaine = taux_quarantaine

    def setDelaiQuarantaine(self, delai_quarantaine):
        self._delai_quarantaine = delai_quarantaine

    def setDelaiRetablissement(self, delai_retablissement):
        self._delai_retablissement = delai_retablissement

    def init_board(self):
        etat0 = np.zeros((self._longueur, self._largeur), dtype=int)
        etat0[0:self._longueur, 0:self._largeur] = STATE["SAIN"]

        # Creation de la population immunisée
        for x in range(self._longueur):
            for y in range(self._largeur):
                if random() < self._taux_immunite:
                    etat0[x, y] = STATE["IMMUN"]

        for i in range(self._nb_clusters):
            x0 = randrange(self._longueur)
            y0 = randrange(self._largeur)
            etat0[x0, y0] = STATE["MALADE"]
            self._date_contamination[x0, y0] = -1

            self._etat_db.append(etat0)

    def reset(self, nb_tours):
        self._etat_db = []
        self._date_contamination = np.zeros((self._longueur, self._largeur), dtype=int)
        self._nb_tour = nb_tours

        self.init_board()

    def prochain_tour(self):
        etat_actuel = self._etat_db[-1]
        etat = etat_actuel.copy()

        for x in range(self._longueur):
            for y in range (self._largeur):
                if etat_actuel[x,y] == STATE["QUARANTAINE"] or etat_actuel[x,y] == STATE["MALADE"]:
                    if self._tour_actuel - self._date_contamination[x, y] == self._delai_retablissement:
                        etat[x,y] = STATE["IMMUN"]
                        continue # Nécessité de faire continue car le test STATE["MْALADE"] se fait sur etat_actuel

                    if self._tour_actuel - self._date_contamination[x, y] == self._delai_mortalite:
                        if random() <= self._taux_mortalite:
                            etat[x,y] = STATE["DECEDE"]
                            continue

                if etat_actuel[x,y] == STATE["MALADE"]:
                    if self._tour_actuel - self._date_contamination[x, y] == self._delai_quarantaine:
                        if random() <= self._taux_quarantaine:
                            etat[x,y] = STATE["QUARANTAINE"]

                    #
                    # Contamination des voisins
                    #

                    # Case "coin", où l'on a 3 voisins
                    if x == 0 and y == 0:
                        neighbours = [[0,1], [1,1], [1,0]]
                    if x == (self._longueur - 1) and y == 0:
                        neighbours = [[x - 1 ,0], [x - 1,1], [x,1]]
                    if x == 0 and y == (self._largeur - 1):
                        neighbours = [[0, y - 1], [1, y - 1], [1, y]]
                    if x == (self._longueur - 1) and y == (self._largeur - 1):
                        neighbours = [[x - 1, y], [x - 1, y - 1], [x, y - 1]]

                    # Case "bord" mais pas coin, où l'on 5 voisins
                    if x == 0 and not (y == 0 or y == (self._largeur - 1)):
                        neighbours = [[0, y - 1], [0, y + 1], [1, y - 1], [1, y], [1, y + 1]]
                    if x == (self._longueur - 1) and not (y == 0 or y == (self._largeur - 1)):
                        neighbours = [[x, y - 1], [x, y + 1], [x - 1, y - 1], [x - 1, y], [x - 1, y + 1]]
                    if not (x == 0 or x == (self._longueur - 1)) and y == 0:
                        neighbours = [[x - 1, 0], [x + 1, 0], [x - 1, 1], [x, 1], [x + 1, 1]]
                    if not (x == 0 or x == (self._longueur - 1)) and y == (self._largeur - 1):
                        neighbours = [[x - 1, y], [x + 1, y], [x - 1, y - 1], [x, y - 1], [x + 1, y - 1]]

                    # Autres cas : 8 cases
                    if x > 0 and x < (self._longueur - 1) and y > 0 and y < (self._largeur - 1):
                        neighbours = [[x - 1, y - 1], [x - 1, y], [x - 1, y + 1],
                                      [x, y -1], [x, y + 1],
                                      [x + 1, y - 1], [x + 1, y], [x + 1, y + 1]]

                    for nb in neighbours:
                        if etat_actuel[nb[0], nb[1]] == STATE["SAIN"]:
                            if random() < self._proba_contag:
                                etat[nb[0], nb[1]] = STATE["MALADE"]
                                self._date_contamination[nb[0], nb[1]] = self._tour_actuel

        self._etat_db.append(etat)
        self._tour_actuel = self._tour_actuel + 1

        return etat

    def dernier_etat(self):
        return self._etat_db[-1]

    def loop(self):
        for x in range(0, self._nb_tour):
            self.prochain_tour()

    def nb_mort(self):
        nb_decede = 0
        for x in range(self._longueur):
            for y in range(self._largeur):
                if self._etat_db[-1][x,y] == STATE["DECEDE"]:
                    nb_decede = nb_decede + 1

        return nb_decede

# if __name__ == '__main__':
#     db = diseaseBoard(20, 15, 0.2)
#     db.loop()
#
#     print("--\n  Bilan : {:,} sur {:,}" . format(db.nb_mort(), 200 * 200))

# #
# # Modèle
# #
#
# # Dimension du monde
# LONGUEUR = 200
# LARGEUR = 200
# NOMBRE_TOUR = 50
#
#
#
# #
# # Paramètres
# #
#
# # Circulation de l'épidémie
#
# DENSITE_IMMUNITE     = 0.2
#
# # Taux de transmission du virus (R0)
#
# R0                  = 3
# PROBA_CONTAG         = R0 / 8
#
# # Parametre de mortalité
# TAUX_MORTALITE       = 0.03
# DELAI_MORTALITE      = 6
#
# # Retablissement si pas mortalité
# DELAI_RETABLISSEMENT = 7
#
# # Délai moyen de mise en quarantaine (obligatoirement inférieur au décès)
# # La quarantaine peut être soi un isolement à domicile soit dans un hopital
# #
# DELAI_QUARANTAINE    = 4
# TAUX_QUARANTAINE     = 0.0
#
# def initialiser_monde(p_immu):
#     etat0 = np.zeros((LONGUEUR, LARGEUR), dtype=int)
#     etat0[0:LONGUEUR, 0:LARGEUR] = STATE["SAIN"]
#
#     # Creation de la population immunisée
#     for x in range(LONGUEUR):
#         for y in range(LARGEUR):
#             if random() < p_immu:
#                 etat0[x,y] = STATE["IMMUN"]
#
#     return etat0
#
# def prochain_tour(etat, p_conta, num_tour):
#     nv_etat = etat.copy()
#
#     for x in range(LONGUEUR):
#         for y in range (LARGEUR):
#             if nv_etat[x,y] == STATE["QUARANTAINE"]:
#                 if num_tour - dateContamination[x, y] == DELAI_RETABLISSEMENT:
#                     nv_etat[x,y] = STATE["IMMUN"]
#
#             if nv_etat[x,y] == STATE["MALADE"]:
#                 #
#                 # Décès ou rétablissement
#                 #
#
#                 if num_tour - dateContamination[x, y] == DELAI_MORTALITE:
#                     if random() <= TAUX_MORTALITE:
#                         nv_etat[x,y] = STATE["DECEDE"]
#                         continue
#
#                 if num_tour - dateContamination[x, y] == DELAI_RETABLISSEMENT:
#                     nv_etat[x,y] = STATE["IMMUN"]
#
#                 if num_tour - dateContamination[x, y] == DELAI_QUARANTAINE:
#                     if random() <= TAUX_QUARANTAINE:
#                         nv_etat[x,y] = STATE["QUARANTAINE"]
#
#                 #
#                 # Contamination des voisins
#                 #
#
#                 # Case "coin", où l'on a 3 voisins
#                 if x == 0 and y == 0:
#                     neighbours = [[0,1], [1,1], [1,0]]
#                 if x == (LONGUEUR - 1) and y == 0:
#                     neighbours = [[x - 1 ,0], [x - 1,1], [x,1]]
#                 if x == 0 and y == (LARGEUR - 1):
#                     neighbours = [[0, y - 1], [1, y - 1], [1, y]]
#                 if x == (LONGUEUR - 1) and y == (LARGEUR - 1):
#                     neighbours = [[x - 1, y], [x - 1, y - 1], [x, y - 1]]
#
#                 # Case "bord" mais pas coin, où l'on 5 voisins
#                 if x == 0 and not (y == 0 or y == (LARGEUR - 1)):
#                     neighbours = [[0, y - 1], [0, y + 1], [1, y - 1], [1, y], [1, y + 1]]
#                 if x == (LONGUEUR - 1) and not (y == 0 or y == (LARGEUR - 1)):
#                     neighbours = [[x, y - 1], [x, y + 1], [x - 1, y - 1], [x - 1, y], [x - 1, y + 1]]
#                 if not (x == 0 or x == (LONGUEUR - 1)) and y == 0:
#                     neighbours = [[x - 1, 0], [x + 1, 0], [x - 1, 1], [x, 1], [x + 1, 1]]
#                 if not (x == 0 or x == (LONGUEUR - 1)) and y == (LARGEUR - 1):
#                     neighbours = [[x - 1, y], [x + 1, y], [x - 1, y - 1], [x, y - 1], [x + 1, y - 1]]
#
#                 # Autres cas : 8 cases
#                 if x > 0 and x < (LONGUEUR - 1) and y > 0 and y < (LARGEUR - 1):
#                     neighbours = [[x - 1, y - 1], [x - 1, y], [x - 1, y + 1],
#                                   [x, y -1], [x, y + 1],
#                                   [x + 1, y - 1], [x + 1, y], [x + 1, y + 1]]
#
#                 for nb in neighbours:
#                     if nv_etat[nb[0], nb[1]] == STATE["SAIN"]:
#                         if random() < p_conta:
#                             nv_etat[nb[0], nb[1]] = STATE["MALADE"]
#                             dateContamination[nb[0], nb[1]] = num_tour
#
#     return nv_etat
#
# Boucle main
#

# if __name__ == '__main__':
#     etat_db = []
#     dateContamination = np.zeros((LONGUEUR, LARGEUR), dtype=int)
#     etat0 = initialiser_monde(DENSITE_IMMUNITE)
#
#     x0 = randrange(LARGEUR)
#     y0 = randrange(LONGUEUR)
#     etat0[x0, y0] = STATE["MALADE"]
#     dateContamination[x0, y0] = -1
#
#     etat_db.append(etat0)
#
#     for i in range(NOMBRE_TOUR):
#         nv_etat = prochain_tour(etat_db[-1], PROBA_CONTAG, i)
#         etat_db.append(nv_etat)
#     #    print (etat)
#
#     NbDecede = 0
#     for x in range(LONGUEUR):
#         for y in range(LARGEUR):
#             if etat_db[-1][x,y] == STATE["DECEDE"]:
#                 NbDecede = NbDecede + 1
#
#     print("--\n  Bilan : {:,} sur {:,}" . format(NbDecede, LONGUEUR * LARGEUR))
