#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from random import random, randrange

# Couleur associée à l'état
STATE = {
    "SUSCEPTIBLE": 0,
    "INFECTED": 1,
    "IMMUNE": 2,
    "QUARANTINE": 3,
    "HOSPITALIZED": 5,
    "DECEASED": 4
}


class DiseaseBoard:
    def __init__(self, size, round_nbr, cluster_nbr):

        self._length = size
        self._width = size

        self._cluster_nbr = cluster_nbr

        self._immunity_rate = 0.2

        self._death_rate = 0.03
        self._death_delay = 6

        self._hospitalized_rate = 0.2
        self._hospitalized_delay = 2

        self._quarantine_rate = 0.2
        self._diagnosis_delay = 2

        # Par défaut, R0 = 3, et il y a 8 cases adjacentes
        self._contagion_rate = 1 / 8
        self._contagion_delay = 3

        # No social Distancing by default
        self._socialDistancingDelay = -1
        self._socialDistancingContagionRate = 0

        self.reset()

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
    def diagnosisDelay(self):
        return self._diagnosis_delay

    @diagnosisDelay.setter
    def diagnosisDelay(self, delai_quarantaine):
        self._diagnosis_delay = delai_quarantaine

    @property
    def deceasedDelay(self):
        return self._death_delay

    @deceasedDelay.setter
    def deceasedDelay(self, death_delay):
        self._death_delay = death_delay

    @property
    def contagionDelay(self):
        return self._contagion_delay

    @contagionDelay.setter
    def contagionDelay(self, delai_contagion):
        self._contagion_delay = delai_contagion

    @property
    def hospitalizedRate(self):
        return self._hospitalized_rate

    @hospitalizedRate.setter
    def hospitalizedRate(self, hospitalized_rate):
        self._hospitalized_rate = hospitalized_rate

    @property
    def hospitalizedDelay(self):
        return self._hospitalized_delay

    @hospitalizedDelay.setter
    def hospitalizedDelay(self, hospitalized_delay):
        self._hospitalized_delay = hospitalized_delay

    @property
    def clusterNbr(self):
        return self._cluster_nbr

    @clusterNbr.setter
    def clusterNbr(self, nb_clusters):
        self._cluster_nbr = nb_clusters

    @property
    def deceasedNbr(self):
        return self._counter[STATE["DECEASED"]][-1]

    @property
    def deceasedData(self):
        return self._counter[STATE["DECEASED"]]

    @property
    def infectedData(self):
        return self._counter[STATE["INFECTED"]]

    @property
    def quarantinedData(self):
        return self._counter[STATE["QUARANTINE"]]

    @property
    def hospitalizedData(self):
        return self._counter[STATE["HOSPITALIZED"]]

    @property
    def sickNbr(self):
        return self._counter[STATE["INFECTED"]][-1] + self._counter[STATE["HOSPITALIZED"]][-1] + \
                self._counter[STATE["QUARANTINE"]][-1]

    @property
    def diagnosedNbr(self):
        return self._counter[STATE["HOSPITALIZED"]][-1] + self._counter[STATE["QUARANTINE"]][-1]

    @property
    def hospitalizedNbr(self):
        return self._counter[STATE["HOSPITALIZED"]][-1]

    @property
    def quarantinedNbr(self):
        return self._counter[STATE["QUARANTINE"]][-1]

    @property
    def R0(self):
        return (self._contagion_rate * self._contagion_delay)

    @property
    def currentRound(self):
        return self._current_round

    @property
    def population(self):
        return self._width * self._length

    @property
    def socialDistancingDelay(self):
        return self._socialDistancingDelay

    @socialDistancingDelay.setter
    def socialDistancingDelay(self, new_delay):
        self._socialDistancingDelay = new_delay

    @property
    def socialDistancingContagionRate(self):
        return self._socialDistancingContagionRate

    @socialDistancingContagionRate.setter
    def socialDistancingContagionRate(self, new_rate):
        self._socialDistancingContagionRate = new_rate

    ###################################
    # Fin de la gestion des attributs #
    ###################################

    def initBoard(self):
        etat0 = np.zeros((self._length, self._width), dtype=int)
        etat0[0:self._length, 0:self._width] = STATE["SUSCEPTIBLE"]

        # Creation de la population immunisée
        for x in range(self._length):
            for y in range(self._width):
                if random() < self._immunity_rate:
                    etat0[x, y] = STATE["IMMUNE"]

        for i in range(self._cluster_nbr):
            x0 = randrange(self._length)
            y0 = randrange(self._width)
            etat0[x0, y0] = STATE["INFECTED"]
            self._contamination_dates[x0, y0] = -1

            self._state_db.append(etat0)
            self._counter[STATE["INFECTED"]][0] += 1

    def reset(self):
        self._state_db = []
        self._contamination_dates = np.zeros((self._length, self._width), dtype=int)
        self._current_round = 0

        self._counter = []
        for n in range(len(STATE.items())):
            self._counter.append([])
            self._counter[n].append(0)

        self.initBoard()

    def nextRound(self):
        """
        Create next round state

        :return: next round state
        """
        neighbours = []
        current_state = self._state_db[-1]
        state = current_state.copy()

        # social distancing effect
        if self._current_round == self._socialDistancingDelay:
            self._contagion_rate = self._socialDistancingContagionRate

        # We init the next round data with the same data as previous round
        for n in range(len(STATE.items())):
            self._counter[n].append(self._counter[n][-1])

        for x in range(self._length):
            for y in range(self._width):
                if current_state[x, y] == STATE["QUARANTINE"]:
                    if self._current_round - self._contamination_dates[x, y] == self._contagion_delay:
                        state[x, y] = STATE["IMMUNE"]
                        self._counter[STATE["QUARANTINE"]][-1] -= 1
                        self._counter[STATE["IMMUNE"]][-1] += 1
                        continue

                    if self._current_round - self._contamination_dates[x, y] == self._hospitalized_delay:
                        if random() <= self._hospitalized_rate:
                            state[x, y] = STATE["HOSPITALIZED"]
                            self._counter[STATE["QUARANTINE"]][-1] -= 1
                            self._counter[STATE["HOSPITALIZED"]][-1] += 1
                            continue

                if current_state[x, y] == STATE["HOSPITALIZED"]:
                    if self._current_round - self._contamination_dates[x, y] == self._death_delay:
                        if random() <= self._death_rate / self._hospitalized_rate:
                            state[x, y] = STATE["DECEASED"]
                            self._counter[STATE["HOSPITALIZED"]][-1] -= 1
                            self._counter[STATE["DECEASED"]][-1] += 1
                            continue

                    if self._current_round - self._contamination_dates[x, y] == self._contagion_delay:
                        state[x, y] = STATE["IMMUNE"]
                        self._counter[STATE["HOSPITALIZED"]][-1] -= 1
                        self._counter[STATE["IMMUNE"]][-1] += 1
                        continue

                if current_state[x, y] == STATE["INFECTED"]:
                    if self._current_round - self._contamination_dates[x, y] == self._diagnosis_delay:
                        if random() <= self._quarantine_rate:
                            state[x, y] = STATE["QUARANTINE"]
                            self._counter[STATE["INFECTED"]][-1] -= 1
                            self._counter[STATE["QUARANTINE"]][-1] += 1
                            continue

                    if self._current_round - self._contamination_dates[x, y] == self._hospitalized_delay:
                        if random() <= self._hospitalized_rate:
                            state[x, y] = STATE["HOSPITALIZED"]
                            self._counter[STATE["INFECTED"]][-1] -= 1
                            self._counter[STATE["HOSPITALIZED"]][-1] += 1
                            continue

                    if self._current_round - self._contamination_dates[x, y] == self._contagion_delay:
                        state[x, y] = STATE["IMMUNE"]
                        self._counter[STATE["INFECTED"]][-1] -= 1
                        self._counter[STATE["IMMUNE"]][-1] += 1
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
                        if current_state[nb[0], nb[1]] == STATE["SUSCEPTIBLE"]:
                            if random() < self._contagion_rate:
                                self._contamination_dates[nb[0], nb[1]] = self._current_round

                                # Same person might have been infected at the same round by another person : the
                                # tests avoids double counting
                                if not state[nb[0], nb[1]] == STATE["INFECTED"]:
                                    state[nb[0], nb[1]] = STATE["INFECTED"]
                                    self._counter[STATE["INFECTED"]][-1] += 1

        self._state_db.append(state)
        self._current_round += 1

        return state

    def lastBoard(self):
        return self._state_db[-1]