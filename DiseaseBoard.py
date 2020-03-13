#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from random import random, randrange

# Couleur associée à l'état
STATE = {
    "SAIN": 0,
    "MALADE": 1,
    "IMMUN": 2,
    "QUARANTAINE": 3,
    "DECEDE": 4
}


class DiseaseBoard:
    def __init__(self, size, tour, nb_clusters):

        self._longueur = size
        self._largeur = size

        self._nb_clusters = nb_clusters

        self._nb_tour = tour
        self._tour_actuel = 0

        self._taux_immunite = 0.2

        self._taux_mortalite = 0.03
        self._delai_mortalite = 6

        self._delai_contagion = 3

        self._delai_quarantaine = 2
        self._taux_quarantaine = 0.2

        # Par défaut, R0 = 3, et il y a 8 cases adjacentes
        self._proba_transmission = 1 / 8

        self._etat_db = []
        self._date_contamination = np.zeros((self._longueur, self._largeur), dtype=int)

        self.init_board()

    #########################
    # Gestion des attributs #
    #########################

    @property
    def tauxImmunite(self):
        return self._taux_immunite

    @tauxImmunite.setter
    def tauxImmunite(self, taux_immunite):
        self._taux_immunite = taux_immunite

    @property
    def tauxMortalite(self):
        return self._taux_mortalite

    @tauxMortalite.setter
    def tauxMortalite(self, taux_mortalite):
        self._taux_mortalite = taux_mortalite

    @property
    def delaiMortalite(self):
        return self._delai_mortalite

    @delaiMortalite.setter
    def delaiMortalite(self, delai_mortalite):
        self._delai_mortalite = delai_mortalite

    @property
    def probaTransmission(self):
        return self._proba_transmission

    @probaTransmission.setter
    def probaTransmission(self, proba_transmission):
        self._proba_transmission = proba_transmission

    @property
    def tauxQuarantaine(self):
        return self._taux_quarantaine

    @tauxQuarantaine.setter
    def tauxQuarantaine(self, taux_quarantaine):
        self._taux_quarantaine = taux_quarantaine

    @property
    def delaiQuarantaine(self):
        return self._delai_quarantaine

    @delaiQuarantaine.setter
    def delaiQuarantaine(self, delai_quarantaine):
        self._delai_quarantaine = delai_quarantaine

    @property
    def delaiContagion(self):
        return self._delai_contagion

    @delaiContagion.setter
    def delaiContagion(self, delai_contagion):
        self._delai_contagion = delai_contagion

    @property
    def R0(self):
        return (self._proba_transmission * self._delai_contagion)

    ###################################
    # Fin de la gestion des attributs #
    ###################################

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
        self._tour_actuel = 0

        self.init_board()

    def prochain_tour(self):
        neighbours = []
        etat_actuel = self._etat_db[-1]
        etat = etat_actuel.copy()

        for x in range(self._longueur):
            for y in range(self._largeur):
                if etat_actuel[x, y] == STATE["QUARANTAINE"] or etat_actuel[x, y] == STATE["MALADE"]:
                    if self._tour_actuel - self._date_contamination[x, y] == self._delai_contagion:
                        etat[x, y] = STATE["IMMUN"]
                        continue  # Nécessité de faire continue car le test STATE["MْALADE"] se fait sur etat_actuel

                    if self._tour_actuel - self._date_contamination[x, y] == self._delai_mortalite:
                        if random() <= self._taux_mortalite:
                            etat[x, y] = STATE["DECEDE"]
                            continue

                if etat_actuel[x, y] == STATE["MALADE"]:
                    if self._tour_actuel - self._date_contamination[x, y] == self._delai_quarantaine:
                        if random() <= self._taux_quarantaine:
                            etat[x, y] = STATE["QUARANTAINE"]
                            continue

                    #
                    # Contamination des voisins
                    #

                    # Case "coin", où l'on a 3 voisins
                    if x == 0 and y == 0:
                        neighbours = [[0, 1], [1, 1], [1, 0]]
                    if x == (self._longueur - 1) and y == 0:
                        neighbours = [[x - 1, 0], [x - 1, 1], [x, 1]]
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
                    if 0 < x < (self._longueur - 1) and 0 < y < (self._largeur - 1):
                        neighbours = [[x - 1, y - 1], [x - 1, y], [x - 1, y + 1],
                                      [x, y - 1], [x, y + 1],
                                      [x + 1, y - 1], [x + 1, y], [x + 1, y + 1]]

                    for nb in neighbours:
                        if etat_actuel[nb[0], nb[1]] == STATE["SAIN"]:
                            if random() < self._proba_transmission:
                                etat[nb[0], nb[1]] = STATE["MALADE"]
                                self._date_contamination[nb[0], nb[1]] = self._tour_actuel

        self._etat_db.append(etat)
        self._tour_actuel = self._tour_actuel + 1

        return etat

    def dernier_etat(self):
        return self._etat_db[-1]

