#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
from PyQt5.QtGui import (QColor, QPainter, QBrush, QPen, QPalette, QDoubleValidator, QIntValidator,
                         QCursor)
from PyQt5.QtWidgets import (QWidget, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLineEdit, QApplication)
from PyQt5.QtCore import (pyqtSignal, QSize, QPoint, Qt, QEvent, QLocale, QTimer)
import pyqtgraph as pg
import sys
import getopt
from typing import Optional, Union

from DiseaseBoard import DiseaseBoard

DEFAULT_BOARD_SIZE = 50
DEFAULT_TOUR = 5
STATE = {
    "SUSCEPTIBLE": 0,
    "INFECTED": 1,
    "IMMUNE": 2,
    "QUARANTINE": 3,
    "DECEASED": 4,
    "HOSPITALIZED": 5
}

STATE_NAME = [("Susceptible", "Susceptible"), ("Infecté", "Infected"),
              ("Immunisé", "Immune"), ("Quarantaine", "Quarantine"),
              ("Décédé", "Deceased"), ("Hospitalisé", "Hospitalized")]

STATUS_PLAYING = 1
STATUS_STOPPED = 0

IMMUNITY_RATE_PARAM = 0
CLUSTER_NB_PARAM = 1
TRANSMISSION_RATE_PARAM = 2
MORTALITY_RATE_PARAM = 3
MORTALITY_DELAY_PARAM = 4
CONTAGION_DELAY_PARAM = 5
QUARANTINE_RATE_PARAM = 6
DIAGNOSIS_DELAY_PARAM = 7
HOSPITALIZED_RATE_PARAM = 8
HOSPITALIZED_DELAY_PARAM = 9
SOCIALDISTANCING_RATE_PARAM = 10
SOCIALDISTANCING_DELAY_PARAM = 11

CONF_ELEMENTS = {
    IMMUNITY_RATE_PARAM: (("Tx Immunité", "Immunity Rate"), "double"),
    CLUSTER_NB_PARAM: (("Nb cluster", "Cluster Nbr"), "int"),
    TRANSMISSION_RATE_PARAM: (("Tx contagion", "Contagion Rate"), "double"),
    MORTALITY_RATE_PARAM: (("Tx mortalité", "Death Rate"), "double"),
    MORTALITY_DELAY_PARAM: (("Délai mortalité", "Death Delay"), "int"),
    CONTAGION_DELAY_PARAM: (("Délai contagion", "Contagion Delay"), "int"),
    QUARANTINE_RATE_PARAM: (("Tx diag / mise quarantaine", "Diagnosis / Quarantine Rate"), "double"),
    HOSPITALIZED_RATE_PARAM: (("Tx hospitalisation", "Hospitalization Rate"), "int"),
    HOSPITALIZED_DELAY_PARAM: (("Délai hospitalisation", "Hospitalization Delay"), "int"),
    DIAGNOSIS_DELAY_PARAM: (("Délai diagnostic", "Diagnosis Delay"), "int"),
    SOCIALDISTANCING_RATE_PARAM: (("Taux post soc. dist", "Post soc. dist rate"), "double"),
    SOCIALDISTANCING_DELAY_PARAM: (("Délai pour soc. dist", "Soc. dist delay"), "int")
}

spread_lang = int

LANG_FR: spread_lang = 0
LANG_US: spread_lang = 1

INFECTED_PLOT = 0
HOSPITALIZED_PLOT = 1
QUARANTINED_PLOT = 2
PLOT_NB = 3


class Pos(QWidget):
    expandable = pyqtSignal(int, int)
    clicked = pyqtSignal()
    ohno = pyqtSignal()

    # stores floating label list, as we might miss some leaveEvent, we need a way to hide them all
    activeLabelList: list = []

    def __init__(self, lang: spread_lang, *args, **kwargs) -> None:
        super(Pos, self).__init__(*args, **kwargs)

        self.setFixedSize(QSize(10, 10))

        self.lang: spread_lang = lang

        self.floatingLabel: QLabel = QLabel()
        self.floatingLabel.setWindowFlags(Qt.FramelessWindowHint)
        self.floatingLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

    def redraw(self, state) -> None:
        self._state = state
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = event.rect()

        outer: Optional[Union[QColor, Qt.GlobalColor]] = None
        inner: Optional[Union[QColor, Qt.GlobalColor]] = None

        if self._state == STATE["SUSCEPTIBLE"]:
            blueColor: QColor = QColor(210, 210, 255)
            outer, inner = blueColor, blueColor
        elif self._state == STATE["INFECTED"]:
            outer, inner = Qt.darkRed, Qt.red
        elif self._state == STATE["DECEASED"]:
            outer, inner = Qt.black, Qt.black
        elif self._state == STATE["QUARANTINE"]:
            outer, inner = Qt.darkYellow, Qt.yellow
        elif self._state == STATE["IMMUNE"]:
            outer, inner = Qt.gray, Qt.lightGray
        elif self._state == STATE["HOSPITALIZED"]:
            darkblueColor: QColor = QColor(100, 110, 200)
            outer, inner = darkblueColor, darkblueColor

        if outer is None or inner is None:
            raise ValueError("Invalid color")

        p.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(r)

    def click(self) -> None:
        pass
        return

        # self.clicked.emit()

    def mouseReleaseEvent(self, e) -> None:
        pass

    def enterEvent(self, event) -> None:
        if event.type() == QEvent.Enter and not self.floatingLabel.isVisible():
            self.cleanFloatingLabel()

            position: QPoint = QCursor.pos()
            position += QPoint(0, -20)  # Move the floating label up to improve its visibility
            labelText = STATE_NAME[self._state][self.lang]
            self.floatingLabel.setText(labelText)
            self.floatingLabel.move(position)

            self.floatingLabel.setVisible(True)
            self.floatingLabel.update()

            Pos.activeLabelList.append(self.floatingLabel)

    def leaveEvent(self, event) -> None:
        if event.type() == QEvent.Leave:
            self.cleanFloatingLabel()

    def cleanFloatingLabel(self) -> None:
        for i, label in enumerate(Pos.activeLabelList):
            label.setVisible(False)
            label.update()

        Pos.activeLabelList = []


class MainWindow(QMainWindow):
    def __init__(self, newboard_size, round_nbr, db, *args, **kwargs) -> None:
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("spread : disease spread simple model")

        self.lang: spread_lang

        self.qLocale = QLocale()
        if self.qLocale.name()[0:2] == "fr":
            self.lang = LANG_FR
        else:
            self.lang = LANG_US

        self.status = STATUS_STOPPED

        self.board_size = newboard_size
        self.diseaseBoard = db
        self.total_round_nbr = round_nbr

        # w est le Widget QT affiché dans la fenêtre
        w = QWidget(self)

        # hb : la bande horizontale supérieure de la fenêtre
        hb = QHBoxLayout()
        hb.addStretch(1)

        self.nb_toursLabel = QLabel()
        self.nb_toursLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.nb_toursLabel.setText("%03d" % 0)

        self._timer = QTimer()
        self._timer.timeout.connect(self.updateTimer)
        self._timer.start(100)  # in ms

        self.goButton = QPushButton("GO")
        self.goButton.setFixedSize(QSize(72, 32))
        self.goButton.setFlat(False)
        self.goButton.pressed.connect(self.goButtonPressed)

        self.nextButton = QPushButton("NEXT")
        self.nextButton.setFixedSize(QSize(72, 32))
        self.nextButton.setFlat(False)
        self.nextButton.pressed.connect(self.nextButtonPressed)

        self.resetButton = QPushButton("RESET")
        self.resetButton.setFixedSize(QSize(82, 32))
        self.resetButton.setFlat(False)
        self.resetButton.pressed.connect(self.resetButtonPressed)

        hb.addWidget(self.nb_toursLabel)
        hb.addWidget(self.goButton)
        hb.addWidget(self.nextButton)
        hb.addWidget(self.resetButton)

        # vb permet de mettre en place 2 lignes
        # La première ligne contient le hb ci-dessous (le header)
        # La seconde ligne contient un vboxlayout pour la configuration et un grid_layout pour le board
        vb = QVBoxLayout()
        vb.addLayout(hb)
        vb.addStretch(1)

        # Construction de la partie principale de la fenêtre
        # A l'aide d'un Hbox (main_layout), mise en place d'une barre à gauche pour la configuration (QGridLayout de
        # QLabel et de QLineEdit) puis à droite le board et enfin la zone de graphique

        #
        # Panneau de configuration à gauche
        #
        self.confgrid = self.setupConfGrid()

        #
        # Principal grid pour l'affichage du diseaseBoard
        #
        self.grid = QGridLayout()
        self.grid.setSpacing(1)

        # Nécessaire pour permettre à l'affichage du board de rester compact
        grid_layout = QVBoxLayout()
        grid_layout.addStretch(1)
        grid_layout.addLayout(self.grid)

        #
        # Zone pour afficher les graphiques
        #

        graph_layout = QHBoxLayout()
        graph_widget = pg.PlotWidget()
        graph_widget.setBackground(self.palette().color(QPalette.Window))
        graph_widget.setXRange(0, self.total_round_nbr, padding=0.0)
        graph_layout.addWidget(graph_widget)

        self.plots = [None] * PLOT_NB
        self.plots[INFECTED_PLOT] = graph_widget.plot([], [], pen=pg.mkPen(color=(255, 0, 0), width=3),
                                                      name="infected 'on the road'")
        self.plots[HOSPITALIZED_PLOT] = graph_widget.plot([], [], pen=pg.mkPen(color=(100, 110, 200),
                                                                               width=3),
                                                          name="hospitalized")
        self.plots[QUARANTINED_PLOT] = graph_widget.plot([], [],
                                                         pen=pg.mkPen(color=(255, 255, 0), width=3),
                                                         name="quarantined")
        graph_widget.addLegend()

        main_layout = QHBoxLayout()
        main_layout.addStretch(1)
        main_layout.addLayout(self.confgrid)
        main_layout.addLayout(grid_layout)
        main_layout.addLayout(graph_layout)
        vb.addLayout(main_layout)

        #
        # Footer configuration
        #

        footer_layout = QHBoxLayout()

        pop_label = QLabel("Pop = " + self.qLocale.toString(self.diseaseBoard.population))
        pop_label.setStyleSheet("color: grey")
        footer_layout.addWidget(pop_label)

        r0_label = QLabel("R0 = " + self.qLocale.toString(self.diseaseBoard.R0))
        r0_label.setStyleSheet("color: grey")
        self.r0_label = r0_label
        footer_layout.addWidget(r0_label)

        ratio_label = QLabel("#infected / #detected = 1")
        ratio_label.setStyleSheet("color: grey")
        self.ratio_label = ratio_label
        footer_layout.addWidget(ratio_label)

        deceased_label = QLabel("#Death = " + self.qLocale.toString(self.diseaseBoard.deceased_nbr))
        deceased_label.setStyleSheet("color: grey")
        self.deceased_label = deceased_label
        footer_layout.addWidget(deceased_label)

        infected_label = QLabel("#Sick = " + self.qLocale.toString(self.diseaseBoard.sick_nbr))
        infected_label.setStyleSheet("color: grey")
        self.infectedLabel = infected_label
        footer_layout.addWidget(infected_label)

        vb.addLayout(footer_layout)

        w.setLayout(vb)
        self.setCentralWidget(w)

        self.initMap(db.last_board())
        self.show()

    def setupConfGrid(self) -> QGridLayout:

        confgrid = QGridLayout()
        confgrid.setSpacing(1)

        for param, data in CONF_ELEMENTS.items():
            lbl = QLabel(data[0][self.lang])

            qle = QLineEdit()

            if param == IMMUNITY_RATE_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.immunity_rate, precision=2))
            if param == CLUSTER_NB_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.cluster_nbr))
            elif param == TRANSMISSION_RATE_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.contagion_rate, precision=2))
                qle.textChanged.connect(self.updateR0)
            elif param == MORTALITY_RATE_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.mortality_rate, precision=2))
            elif param == MORTALITY_DELAY_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.mortality_delay))
            elif param == CONTAGION_DELAY_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.contagion_delay))
                qle.textChanged.connect(self.updateR0)
            elif param == HOSPITALIZED_RATE_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.hospitalized_rate))
            elif param == HOSPITALIZED_DELAY_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.hospitalized_delay))
            elif param == QUARANTINE_RATE_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.quarantine_rate, precision=2))
            elif param == DIAGNOSIS_DELAY_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.diagnosis_delay))
            elif param == SOCIALDISTANCING_DELAY_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.social_distancing_delay))
            elif param == SOCIALDISTANCING_RATE_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.social_distancing_contagion_rate, precision=2))

            if data[1] == "double":
                qle.setValidator(QDoubleValidator(0.0, 1.0, 2))
            elif data[1] == "int":
                qle.setValidator(QIntValidator(0, self.total_round_nbr))

            qle.setAlignment(Qt.AlignRight)
            qle.setFixedWidth(40)

            confgrid.addWidget(lbl, param, 0)
            confgrid.addWidget(qle, param, 1)

        return confgrid

    def initMap(self, etat) -> None:
        # Add positions to the map
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                w = Pos(self.lang)
                self.grid.addWidget(w, x, y)
                w.redraw(etat[x, y])

    def updateMap(self, etat) -> None:
        # Add positions to the map
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                w = self.grid.itemAtPosition(x, y).widget()
                w.redraw(etat[x, y])

        infected_text = "#Sick = "
        infected_text += self.qLocale.toString(self.diseaseBoard.sick_nbr)
        infected_text += " (inc #Hospit. = "
        infected_text += self.qLocale.toString(self.diseaseBoard.hospitalized_nbr)
        infected_text += ")"

        self.infectedLabel.setText(infected_text)

        self.deceased_label.setText("#Deceased = " + self.qLocale.toString(self.diseaseBoard.deceased_nbr))

        self.deceased_label.setText("#Deceased = " + self.qLocale.toString(self.diseaseBoard.deceased_nbr))
        if self.diseaseBoard.diagnosed_nbr != 0:
            explanation = "#infected / #detected =" + self.qLocale.toString(
                self.diseaseBoard.sick_nbr / self.diseaseBoard.diagnosed_nbr)
            self.ratio_label.setText(explanation)
        else:
            self.ratio_label.setText("#infected / #detected = N/A")

        round_nbr = self.diseaseBoard.current_round
        self.plots[INFECTED_PLOT].setData(range(0, round_nbr + 1),
                                          self.diseaseBoard.infected_data)
        self.plots[HOSPITALIZED_PLOT].setData(range(0, round_nbr + 1),
                                              self.diseaseBoard.hospitalized_data)
        self.plots[QUARANTINED_PLOT].setData(range(0, round_nbr + 1),
                                             self.diseaseBoard.quarantined_data)

    def goButtonPressed(self) -> None:
        if self.diseaseBoard.current_round == 0:
            # Reconfiguration de la simulation
            self.diseaseBoard.contagion_rate = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(TRANSMISSION_RATE_PARAM, 1).widget().text())[0]
            self.diseaseBoard.mortality_rate = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(MORTALITY_RATE_PARAM, 1).widget().text())[0]
            self.diseaseBoard.contagion_delay = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(CONTAGION_DELAY_PARAM, 1).widget().text())[0]
            self.diseaseBoard.hospitalized_rate = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(HOSPITALIZED_RATE_PARAM, 1).widget().text())[0]
            self.diseaseBoard.hospitalized_delay = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(HOSPITALIZED_DELAY_PARAM, 1).widget().text())[0]
            self.diseaseBoard.mortality_delay = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(MORTALITY_DELAY_PARAM, 1).widget().text())[0]
            self.diseaseBoard.quarantine_rate = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(QUARANTINE_RATE_PARAM, 1).widget().text())[0]
            self.diseaseBoard.diagnosis_delay = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(DIAGNOSIS_DELAY_PARAM, 1).widget().text())[0]
            self.diseaseBoard.social_distancing_delay = self.qLocale.toInt(
                self.confgrid.itemAtPosition(SOCIALDISTANCING_DELAY_PARAM, 1).widget().text())[0]
            self.diseaseBoard.social_distancing_contagion_rate = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(SOCIALDISTANCING_RATE_PARAM, 1).widget().text())[0]

        if self.status == STATUS_STOPPED:
            self.status = STATUS_PLAYING
            self.goButton.setText("PAUSE")

            for i in range(self.confgrid.rowCount()):
                self.confgrid.itemAtPosition(i, 1).widget().setReadOnly(True)
                self.confgrid.itemAtPosition(i, 1).widget().setStyleSheet("color: grey; selection-color: grey")
                self.confgrid.itemAtPosition(i, 1).widget().repaint()

        else:
            self.status = STATUS_STOPPED
            self.goButton.setText("GO")
            for i in range(self.confgrid.rowCount()):
                self.confgrid.itemAtPosition(i, 1).widget().setReadOnly(False)
                self.confgrid.itemAtPosition(i, 1).widget().setStyleSheet("color: black; selection-color: black")
                self.confgrid.itemAtPosition(i, 1).widget().repaint()

    def nextButtonPressed(self) -> None:
        if self.diseaseBoard.current_round + 1 > self.total_round_nbr:
            self.status = STATUS_STOPPED
            return

        etat: np.ndarray = self.diseaseBoard.next_round()
        self.nb_toursLabel.setText("%03d" % self.diseaseBoard.current_round)
        self.updateMap(etat)
        self.updateR0()
        self.grid.update()

    def resetButtonPressed(self) -> None:
        self.diseaseBoard.immunity_rate = self.qLocale.toDouble(
            self.confgrid.itemAtPosition(IMMUNITY_RATE_PARAM, 1).widget().text())[0]

        self.diseaseBoard.cluster_nbr = self.qLocale.toInt(
            self.confgrid.itemAtPosition(CLUSTER_NB_PARAM, 1).widget().text())[0]

        self.diseaseBoard.reset()
        self.nb_toursLabel.setText("%03d" % 0)
        self.updateMap(self.diseaseBoard.last_board())
        self.updateR0()

        self.goButton.setText("GO")
        self.status = STATUS_STOPPED

    def updateTimer(self) -> None:
        if self.status == STATUS_PLAYING:

            if self.diseaseBoard.current_round + 1 > self.total_round_nbr or \
                    (self.diseaseBoard.sick_nbr == 0 and self.diseaseBoard.quarantined_nbr == 0):
                self.status = STATUS_STOPPED
                for i in range(self.confgrid.rowCount()):
                    self.confgrid.itemAtPosition(i, 1).widget().setReadOnly(False)
                    self.confgrid.itemAtPosition(i, 1).widget().setStyleSheet("color: black; selection-color: black")
                    self.confgrid.itemAtPosition(i, 1).widget().repaint()

                return

            self.nb_toursLabel.setText("%03d" % self.diseaseBoard.current_round)
            etat = self.diseaseBoard.next_round()
            self.updateMap(etat)
            self.updateR0()

    def updateR0(self) -> None:
        self.r0_label.setText("R0 = {:.3} ".format(self.diseaseBoard.R0))


def usage() -> None:
    print(
        """Usage: spread [options] round_number board_size cluster_number
            round_number: number of rounds for the simulation
            board_size: size of the board
            cluster_number: number of initial board disease clusters""")


if __name__ == '__main__':

    tours = 60
    board_size = 30
    nb_clusters = 3

    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'h')
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    for o, c in optlist:
        if o == '-h':
            usage()
            sys.exit()

    if len(sys.argv) >= 2:
        tours = int(sys.argv[1])

    if len(sys.argv) >= 3:
        board_size = int(sys.argv[2])

    if len(sys.argv) >= 4:
        nb_clusters = int(sys.argv[3])

    db = DiseaseBoard(board_size, tours, nb_clusters)
    db.immunity_rate = 0.0
    # Entre 2 et 3 personnes contaminées par malade, si on considère qu'à chaque tour (a peu près un jour), on
    # a l'occasion de contaminer environ 15 personnes, et ce pendant la durée de la contamination, considérée comme
    # égale au délai de rétablissement

    db.contagion_delay = 14
    db.contagion_rate = 2 / 13
    db.diagnosis_delay = 5
    db.hospitalized_delay = 5
    db.quarantine_rate = 0.5

    db.social_distancing_delay = -1
    db.social_distancing_contagion_rate = db.contagion_rate / 3

    app = QApplication([])
    window = MainWindow(board_size, tours, db)
    app.exec_()
