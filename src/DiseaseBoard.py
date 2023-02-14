#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from random import random, randrange
from typing import NewType, Any

BoardState = NewType("BoardState", np.ndarray)


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
    def __init__(self, size: int, cluster_nbr: int) -> None:

        self._length: int = size
        self._width: int = size

        self._cluster_nbr: int = cluster_nbr

        self._immunity_rate: float = 0.2

        self._death_rate: float = 0.03
        self._death_delay: int = 6

        self._hospitalized_rate: float = 0.2
        self._hospitalized_delay: int = 2

        self._quarantine_rate: float = 0.2
        self._diagnosis_delay: int = 2

        # Par défaut, R0 = 3, et il y a 8 cases adjacentes
        self._contagion_rate: float = 1 / 8
        self._contagion_delay: int = 3

        # No social Distancing by default
        self._socialDistancingDelay: int = -1
        self._socialDistancingContagionRate: float = 0

        self._state_db: list[BoardState] = []
        self._contamination_dates = np.zeros((self._length, self._width), dtype=int)
        self._current_round: int = 0
        self._counter: list = []

        self.reset()

    #########################
    # Gestion des attributs #
    #########################

    @property
    def immunity_rate(self) -> float:
        return self._immunity_rate

    @immunity_rate.setter
    def immunity_rate(self, taux_immunite) -> None:
        self._immunity_rate = taux_immunite

    @property
    def mortality_rate(self) -> float:
        return self._death_rate

    @mortality_rate.setter
    def mortality_rate(self, taux_mortalite) -> None:
        self._death_rate = taux_mortalite

    @property
    def mortality_delay(self) -> int:
        return self._death_delay

    @mortality_delay.setter
    def mortality_delay(self, delai_mortalite) -> None:
        self._death_delay = delai_mortalite

    @property
    def contagion_rate(self) -> float:
        return self._contagion_rate

    @contagion_rate.setter
    def contagion_rate(self, proba_transmission) -> None:
        self._contagion_rate = proba_transmission

    @property
    def quarantine_rate(self) -> float:
        return self._quarantine_rate

    @quarantine_rate.setter
    def quarantine_rate(self, taux_quarantaine) -> None:
        self._quarantine_rate = taux_quarantaine

    @property
    def diagnosis_delay(self) -> int:
        return self._diagnosis_delay

    @diagnosis_delay.setter
    def diagnosis_delay(self, delai_quarantaine) -> None:
        self._diagnosis_delay = delai_quarantaine

    @property
    def deceased_delay(self) -> int:
        return self._death_delay

    @deceased_delay.setter
    def deceased_delay(self, death_delay) -> None:
        self._death_delay = death_delay

    @property
    def contagion_delay(self) -> int:
        return self._contagion_delay

    @contagion_delay.setter
    def contagion_delay(self, delai_contagion) -> None:
        self._contagion_delay = delai_contagion

    @property
    def hospitalized_rate(self) -> float:
        return self._hospitalized_rate

    @hospitalized_rate.setter
    def hospitalized_rate(self, hospitalized_rate) -> None:
        self._hospitalized_rate = hospitalized_rate

    @property
    def hospitalized_delay(self) -> int:
        return self._hospitalized_delay

    @hospitalized_delay.setter
    def hospitalized_delay(self, hospitalized_delay) -> None:
        self._hospitalized_delay = hospitalized_delay

    @property
    def cluster_nbr(self) -> int:
        return self._cluster_nbr

    @cluster_nbr.setter
    def cluster_nbr(self, nb_clusters) -> None:
        self._cluster_nbr = nb_clusters

    @property
    def deceased_nbr(self) -> int:
        return self._counter[STATE["DECEASED"]][-1]

    @property
    def deceased_data(self) -> list:
        return self._counter[STATE["DECEASED"]]

    @property
    def infected_data(self) -> list:
        return self._counter[STATE["INFECTED"]]

    @property
    def quarantined_data(self) -> list:
        return self._counter[STATE["QUARANTINE"]]

    @property
    def hospitalized_data(self) -> list:
        return self._counter[STATE["HOSPITALIZED"]]

    @property
    def sick_nbr(self) -> int:
        states = ["INFECTED", "HOSPITALIZED", "QUARANTINE"]
        return sum([self._counter[STATE[state]][-1] for state in states])

    @property
    def diagnosed_nbr(self) -> int:
        return self._counter[STATE["HOSPITALIZED"]][-1] + self._counter[STATE["QUARANTINE"]][-1]

    @property
    def hospitalized_nbr(self) -> int:
        return self._counter[STATE["HOSPITALIZED"]][-1]

    @property
    def quarantined_nbr(self) -> int:
        return self._counter[STATE["QUARANTINE"]][-1]

    @property
    def R0(self) -> float:
        return self._contagion_rate * self._contagion_delay

    @property
    def current_round(self) -> int:
        return self._current_round

    @property
    def population(self) -> int:
        return self._width * self._length

    @property
    def social_distancing_delay(self) -> int:
        return self._socialDistancingDelay

    @social_distancing_delay.setter
    def social_distancing_delay(self, new_delay) -> None:
        self._socialDistancingDelay = new_delay

    @property
    def social_distancing_contagion_rate(self) -> float:
        return self._socialDistancingContagionRate

    @social_distancing_contagion_rate.setter
    def social_distancing_contagion_rate(self, new_rate) -> None:
        self._socialDistancingContagionRate = new_rate

    ###################################
    # Fin de la gestion des attributs #
    ###################################

    def init_board(self) -> None:
        etat0: BoardState = BoardState(np.zeros((self._length, self._width), dtype=int))
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

    def reset(self) -> None:
        self._counter = []
        for n in range(len(STATE.items())):
            self._counter.append([])
            self._counter[n].append(0)

        self.init_board()

        self._current_round = 0

    def next_round(self) -> BoardState:
        """
        Create next round state

        :return: next round state
        """
        neighbours = []
        current_state: BoardState = self._state_db[-1]
        state = current_state.copy()

        # social distancing effect
        if self._current_round == self._socialDistancingDelay:
            self._contagion_rate = self._socialDistancingContagionRate

        # We initialize the next round data with the same data as previous round
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

    def last_board(self) -> BoardState:
        return self._state_db[-1]
