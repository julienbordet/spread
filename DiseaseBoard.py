#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from random import random, randrange

# Couleur associée à l'état
STATE = {
    "HEALTHY": 0,
    "SICK": 1,
    "IMMUNE": 2,
    "QUARANTINE": 3,
    "DECEASED": 4
}


class DiseaseBoard:
    def __init__(self, size, round_nbr, cluster_nbr):

        self._length = size
        self._width = size

        self._cluster_nbr = cluster_nbr

        self._round_nbr = round_nbr
        self._current_round = 0

        self._immunity_rate = 0.2

        self._death_rate = 0.03
        self._death_delay = 6

        self._quarantine_rate = 0.2
        self._quarantine_delay = 2

        # Par défaut, R0 = 3, et il y a 8 cases adjacentes
        self._contagion_rate = 1 / 8
        self._contagion_delay = 3

        self._state_db = []
        self._contamination_dates = np.zeros((self._length, self._width), dtype=int)

        self.initBoard()

    #########################
    # Gestion des attributs #
    #########################

    @property
    def immunityRate(self):
        return self._immunity_rate

    @immunityRate.setter
    def immunityRate(self, taux_immunite):
        self._immunity_rate = taux_immunite

    @property
    def mortalityRate(self):
        return self._death_rate

    @mortalityRate.setter
    def mortalityRate(self, taux_mortalite):
        self._death_rate = taux_mortalite

    @property
    def mortalityDelay(self):
        return self._death_delay

    @mortalityDelay.setter
    def mortalityDelay(self, delai_mortalite):
        self._death_delay = delai_mortalite

    @property
    def contagionRate(self):
        return self._contagion_rate

    @contagionRate.setter
    def contagionRate(self, proba_transmission):
        self._contagion_rate = proba_transmission

    @property
    def quarantineRate(self):
        return self._quarantine_rate

    @quarantineRate.setter
    def quarantineRate(self, taux_quarantaine):
        self._quarantine_rate = taux_quarantaine

    @property
    def quarantineDelay(self):
        return self._quarantine_delay

    @quarantineDelay.setter
    def quarantineDelay(self, delai_quarantaine):
        self._quarantine_delay = delai_quarantaine

    @property
    def contagionDelay(self):
        return self._contagion_delay

    @contagionDelay.setter
    def contagionDelay(self, delai_contagion):
        self._contagion_delay = delai_contagion

    @property
    def R0(self):
        return (self._contagion_rate * self._contagion_delay)

    @property
    def clusterNbr(self):
        return self._cluster_nbr

    @clusterNbr.setter
    def clusterNbr(self, nb_clusters):
        self._cluster_nbr = nb_clusters

    ###################################
    # Fin de la gestion des attributs #
    ###################################

    def initBoard(self):
        etat0 = np.zeros((self._length, self._width), dtype=int)
        etat0[0:self._length, 0:self._width] = STATE["HEALTHY"]

        # Creation de la population immunisée
        for x in range(self._length):
            for y in range(self._width):
                if random() < self._immunity_rate:
                    etat0[x, y] = STATE["IMMUNE"]

        for i in range(self._cluster_nbr):
            x0 = randrange(self._length)
            y0 = randrange(self._width)
            etat0[x0, y0] = STATE["SICK"]
            self._contamination_dates[x0, y0] = -1

            self._state_db.append(etat0)

    def reset(self, nb_tours):
        self._state_db = []
        self._contamination_dates = np.zeros((self._length, self._width), dtype=int)
        self._round_nbr = nb_tours
        self._current_round = 0

        self.initBoard()

    def nextRound(self):
        neighbours = []
        current_state = self._state_db[-1]
        state = current_state.copy()

        for x in range(self._length):
            for y in range(self._width):
                if current_state[x, y] == STATE["QUARANTINE"] or current_state[x, y] == STATE["SICK"]:
                    if self._current_round - self._contamination_dates[x, y] == self._contagion_delay:
                        state[x, y] = STATE["IMMUNE"]
                        continue  # Nécessité de faire continue car le test STATE["MْALADE"] se fait sur current_state

                    if self._current_round - self._contamination_dates[x, y] == self._death_delay:
                        if random() <= self._death_rate:
                            state[x, y] = STATE["DECEASED"]
                            continue

                if current_state[x, y] == STATE["SICK"]:
                    if self._current_round - self._contamination_dates[x, y] == self._quarantine_delay:
                        if random() <= self._quarantine_rate:
                            state[x, y] = STATE["QUARANTINE"]
                            continue

                    #
                    # Contamination des voisins
                    #

                    # Case "coin", où l'on a 3 voisins
                    if x == 0 and y == 0:
                        neighbours = [[0, 1], [1, 1], [1, 0]]
                    if x == (self._length - 1) and y == 0:
                        neighbours = [[x - 1, 0], [x - 1, 1], [x, 1]]
                    if x == 0 and y == (self._width - 1):
                        neighbours = [[0, y - 1], [1, y - 1], [1, y]]
                    if x == (self._length - 1) and y == (self._width - 1):
                        neighbours = [[x - 1, y], [x - 1, y - 1], [x, y - 1]]

                    # Case "bord" mais pas coin, où l'on 5 voisins
                    if x == 0 and not (y == 0 or y == (self._width - 1)):
                        neighbours = [[0, y - 1], [0, y + 1], [1, y - 1], [1, y], [1, y + 1]]
                    if x == (self._length - 1) and not (y == 0 or y == (self._width - 1)):
                        neighbours = [[x, y - 1], [x, y + 1], [x - 1, y - 1], [x - 1, y], [x - 1, y + 1]]
                    if not (x == 0 or x == (self._length - 1)) and y == 0:
                        neighbours = [[x - 1, 0], [x + 1, 0], [x - 1, 1], [x, 1], [x + 1, 1]]
                    if not (x == 0 or x == (self._length - 1)) and y == (self._width - 1):
                        neighbours = [[x - 1, y], [x + 1, y], [x - 1, y - 1], [x, y - 1], [x + 1, y - 1]]

                    # Autres cas : 8 cases
                    if 0 < x < (self._length - 1) and 0 < y < (self._width - 1):
                        neighbours = [[x - 1, y - 1], [x - 1, y], [x - 1, y + 1],
                                      [x, y - 1], [x, y + 1],
                                      [x + 1, y - 1], [x + 1, y], [x + 1, y + 1]]

                    for nb in neighbours:
                        if current_state[nb[0], nb[1]] == STATE["HEALTHY"]:
                            if random() < self._contagion_rate:
                                state[nb[0], nb[1]] = STATE["SICK"]
                                self._contamination_dates[nb[0], nb[1]] = self._current_round

        self._state_db.append(state)
        self._current_round = self._current_round + 1

        return state

    def lastBoard(self):
        return self._state_db[-1]

