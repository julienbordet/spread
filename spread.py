#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import getopt

from DiseaseBoard import DiseaseBoard

DEFAULT_BOARD_SIZE = 50
DEFAULT_TOUR = 5
STATE = {
    "SAIN": 0,
    "MALADE": 1,
    "IMMUN": 2,
    "QUARANTAINE": 3,
    "DECEDE": 4
}

STATUS_PLAYING = 1
STATUS_STOPPED = 0

IMMUNITY_RATE_PARAM = 0
CLUSTER_NB_PARAM = 1
TRANSMISSION_RATE_PARAM = 2
MORTALITY_RATE_PARAM = 3
MORTALITY_DELAY_PARAM = 4
CONTAGION_DELAY_PARAM = 5
QUARANTINE_RATE_PARAM = 6
QUARANTINE_DELAY_PARAM = 7

btns = {
    IMMUNITY_RATE_PARAM: (("Tx Immunité", "Immunity Rate"), "double"),
    CLUSTER_NB_PARAM: (("Nb cluster", "Cluster Nbr"), "int"),
    TRANSMISSION_RATE_PARAM: (("Tx contagion", "Contagion Rate"), "double"),
    MORTALITY_RATE_PARAM: (("Tx mortalité", "Death Rate"), "double"),
    MORTALITY_DELAY_PARAM: (("Délai mortalité", "Death Delay"), "int"),
    CONTAGION_DELAY_PARAM: (("Délai contagion", "Contagion Delay"), "int"),
    QUARANTINE_RATE_PARAM: (("Tx mise quarantaine", "Quarantine Rate"), "int"),
    QUARANTINE_DELAY_PARAM: (("Délai mise quarantaine", "Quarantine Delay"), "int")
}

LANG_FR = 0
LANG_US = 1

class Pos(QWidget):
    expandable = pyqtSignal(int, int)
    clicked = pyqtSignal()
    ohno = pyqtSignal()

    def __init__(self, x, y, *args, **kwargs):
        super(Pos, self).__init__(*args, **kwargs)

        self.setFixedSize(QSize(10, 10))

        self.x = x
        self.y = y

    def redraw(self, state):
        self._state = state
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = event.rect()

        if self._state == STATE["SAIN"]:
            color = self.palette().color(QPalette.Background)
            outer, inner = color, color
        elif self._state == STATE["MALADE"]:
            outer, inner = Qt.darkRed, Qt.red
        elif self._state == STATE["DECEDE"]:
            outer, inner = Qt.black, Qt.black
        elif self._state == STATE["QUARANTAINE"]:
            outer, inner = Qt.darkYellow, Qt.yellow
        elif self._state == STATE["IMMUN"]:
            outer, inner = Qt.gray, Qt.lightGray
        else:
            outer, inner = Qt.blue, Qt.blue

        p.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(r)

    def click(self):
        pass
        return

        # self.clicked.emit()

    def mouseReleaseEvent(self, e):
        pass


class MainWindow(QMainWindow):
    def __init__(self, newboard_size, nb_tours, dB, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("spread : disease spread simple model")

        self.qLocale = QLocale()
        if self.qLocale.name()[0:2] == "fr":
            self.lang = LANG_FR
        else:
            self.lang = LANG_US

        self.status = STATUS_STOPPED

        self.board_size = newboard_size
        self.diseaseBoard = dB
        self.nb_tours_init = nb_tours
        self.nb_tours = nb_tours

        # w est le Widge QT affiché dans la fenêtre
        w = QWidget()

        # hb : la bande horizontale supérieure de la fenêtre
        hb = QHBoxLayout()
        hb.addStretch(1)

        self.nb_toursLabel = QLabel()
        self.nb_toursLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.nb_toursLabel.setText("%03d" % self.nb_tours)

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
        # La seconde ligne contient un vboxlayout pour la configuration et un gridLayout pour le board
        vb = QVBoxLayout()
        vb.addLayout(hb)
        vb.addStretch(1)

        # Construction de la partie principale de la fenêtre
        # A l'aide d'un Hbox, mise en place d'une barre à gauche pour la configuration (QGridLayout de QLabel et de
        # QLineEdit) puis à droite le board

        mainLayout = QHBoxLayout()
        mainLayout.addStretch(1)

        self.confgrid = self.setupConfGrid()

        self.grid = QGridLayout()
        self.grid.setSpacing(1)

        # Nécessaire pour permettre à l'affichage du board de rester compact

        gridLayout = QVBoxLayout()
        gridLayout.addStretch(1)
        gridLayout.addLayout(self.grid)

        mainLayout.addLayout(self.confgrid)
        mainLayout.addLayout(gridLayout)
        vb.addLayout(mainLayout)

        footerLayout = QHBoxLayout()
        r0Label = QLabel("R0 = " + self.qLocale.toString(self.diseaseBoard.R0))
        r0Label.setStyleSheet("color: grey")
        self.r0Label = r0Label
        footerLayout.addWidget(r0Label)
        vb.addLayout(footerLayout)

        w.setLayout(vb)
        self.setCentralWidget(w)

        self.initMap(dB.lastBoard())
        self.show()

    def setupConfGrid(self):

        confgrid = QGridLayout()
        confgrid.setSpacing(1)

        for param, data in btns.items():
            lbl = QLabel(data[0][self.lang])

            qle = QLineEdit()

            if param == IMMUNITY_RATE_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.immunityRate, precision = 2))
            if param == CLUSTER_NB_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.clusterNbr))
            elif param == TRANSMISSION_RATE_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.contagionRate, precision = 2))
                qle.textChanged.connect(self.updateR0)
            elif param == MORTALITY_RATE_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.mortalityRate, precision=2))
            elif param == MORTALITY_DELAY_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.mortalityDelay))
            elif param == CONTAGION_DELAY_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.contagionDelay))
                qle.textChanged.connect(self.updateR0)
            elif param == QUARANTINE_RATE_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.quarantineRate, precision=2))
            elif param == QUARANTINE_DELAY_PARAM:
                qle.setText(self.qLocale.toString(self.diseaseBoard.quarantineDelay))

            if data[1] == "double":
                qle.setValidator(QDoubleValidator(0.0, 1.0, 2))

            qle.setAlignment(Qt.AlignRight)
            qle.setFixedWidth(40)

            confgrid.addWidget(lbl, param, 0)
            confgrid.addWidget(qle, param, 1)

        return confgrid

    def initMap(self, etat):
        # Add positions to the map
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                w = Pos(x, y)
                self.grid.addWidget(w, x, y)
                w.redraw(etat[x, y])

    def updateMap(self, etat):
        # Add positions to the map
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                w = self.grid.itemAtPosition(x, y).widget()
                w.redraw(etat[x, y])

    def goButtonPressed(self):
        if (self.nb_tours_init == self.nb_tours):
            # Reconfiguration de la simulation
            self.diseaseBoard.contagionRate = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(TRANSMISSION_RATE_PARAM, 1).widget().text())[0]
            self.diseaseBoard.mortalityRate = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(MORTALITY_RATE_PARAM, 1).widget().text())[0]
            self.diseaseBoard.contagionDelay = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(CONTAGION_DELAY_PARAM, 1).widget().text())[0]
            self.diseaseBoard.mortalityDelay = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(MORTALITY_DELAY_PARAM, 1).widget().text())[0]
            self.diseaseBoard.quarantineRate = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(QUARANTINE_RATE_PARAM, 1).widget().text())[0]
            self.diseaseBoard.quarantineDelay = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(QUARANTINE_DELAY_PARAM, 1).widget().text())[0]

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
                self.confgrid.itemAtPosition(i,1).widget().setReadOnly(False)
                self.confgrid.itemAtPosition(i, 1).widget().setStyleSheet("color: black; selection-color: black")
                self.confgrid.itemAtPosition(i, 1).widget().repaint()

    def nextButtonPressed(self):
        self.nb_tours = self.nb_tours - 1

        if self.nb_tours < 0:
            self.status = STATUS_STOPPED
            return

        self.nb_toursLabel.setText("%03d" % self.nb_tours)
        etat = self.diseaseBoard.nextRound()
        self.updateMap(etat)
        self.grid.update()

    def resetButtonPressed(self):
        self.diseaseBoard.immunityRate = self.qLocale.toDouble(
            self.confgrid.itemAtPosition(IMMUNITY_RATE_PARAM, 1).widget().text())[0]

        self.diseaseBoard.clusterNbr = self.qLocale.toInt(
            self.confgrid.itemAtPosition(CLUSTER_NB_PARAM, 1).widget().text())[0]

        self.diseaseBoard.reset(self.nb_tours_init)
        self.nb_tours = self.nb_tours_init
        self.nb_toursLabel.setText("%03d" % self.nb_tours)
        self.updateMap(self.diseaseBoard.lastBoard())

        self.goButton.setText("GO")
        self.status = STATUS_STOPPED

    def updateTimer(self):
        if self.status == STATUS_PLAYING:
            self.nb_tours = self.nb_tours - 1

            if self.nb_tours < 0:
                self.status = STATUS_STOPPED
                for i in range(self.confgrid.rowCount()):
                    self.confgrid.itemAtPosition(i,1).widget().setReadOnly(False)
                    self.confgrid.itemAtPosition(i, 1).widget().setStyleSheet("color: black; selection-color: black")
                    self.confgrid.itemAtPosition(i, 1).widget().repaint()

                return

            self.nb_toursLabel.setText("%03d" % self.nb_tours)
            etat = self.diseaseBoard.nextRound()
            self.updateMap(etat)

    def updateR0(self):
        self.diseaseBoard.contagionRate = self.qLocale.toDouble(
            self.confgrid.itemAtPosition(TRANSMISSION_RATE_PARAM, 1).widget().text())[0]
        self.diseaseBoard.contagionDelay = self.qLocale.toDouble(
            self.confgrid.itemAtPosition(CONTAGION_DELAY_PARAM, 1).widget().text())[0]
        self.r0Label.setText("R0 = {:.3} ".format(self.diseaseBoard.R0))

def usage():
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
        try:
            tours = int(sys.argv[1])
        except:
            pass

    if len(sys.argv) >= 3:
        try:
            board_size = int(sys.argv[2])
        except:
            pass

    if len(sys.argv) >= 4:
        try:
            nb_clusters = int(sys.argv[3])
        except:
            pass

    db = DiseaseBoard(board_size, tours, nb_clusters)
    db.immunityRate = 0.4
    # Entre 2 et 3 personnes contaminées par malade, si on considère qu'à chaque tour (a peu près un jour), on
    # a l'occasion de contaminer environ 15 personnes, et ce pendant la durée de la contamination, considérée comme
    # égale au délai de rétablissement

    db.contagionDelay = 7
    db.contagionRate = 2 / 7
    db.quarantineDelay = 6
    db.quarantineRate = 0.8

    app = QApplication([])
    window = MainWindow(board_size, tours, db)
    app.exec_()
