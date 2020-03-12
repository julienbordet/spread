#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

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

CONF_LIGNE_TAUX_IMMUNITE = 0
CONF_LIGNE_PROBA_TRANSMISSION = 1
CONF_LIGNE_TAUX_MORTALITE = 2
CONF_LIGNE_DELAI_MORTALITE = 3
CONF_LIGNE_DELAI_RETABLISSEMENT = 4
CONF_LIGNE_TAUX_QUARANTAINE = 5
CONF_LIGNE_DELAI_QUARANTAINE = 6


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

        self.qLocale = QLocale()

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
        self._timer.timeout.connect(self.update_timer)
        self._timer.start(100)  # in ms

        self.goButton = QPushButton("GO")
        self.goButton.setFixedSize(QSize(72, 32))
        self.goButton.setFlat(False)
        self.goButton.pressed.connect(self.goButton_pressed)

        self.nextButton = QPushButton("NEXT")
        self.nextButton.setFixedSize(QSize(72, 32))
        self.nextButton.setFlat(False)
        self.nextButton.pressed.connect(self.nextButton_pressed)

        self.resetButton = QPushButton("RESET")
        self.resetButton.setFixedSize(QSize(82, 32))
        self.resetButton.setFlat(False)
        self.resetButton.pressed.connect(self.resetButton_pressed)

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

        self.init_map(dB.dernier_etat())
        self.show()

    def setupConfGrid(self):

        confgrid = QGridLayout()
        confgrid.setSpacing(1)

        TI = QLabel("Taux Immunité : ")
        TIV = QLineEdit(self.qLocale.toString(self.diseaseBoard.tauxImmunite, precision = 2))
        TIV.setValidator(QDoubleValidator(0.0, 1.0, 2))
        TIV.setAlignment(Qt.AlignRight)
        TIV.setFixedWidth(40)
        confgrid.addWidget(TI, CONF_LIGNE_TAUX_IMMUNITE, 0)
        confgrid.addWidget(TIV, CONF_LIGNE_TAUX_IMMUNITE, 1)

        TI = QLabel("Proba transmission : ")
        TIV = QLineEdit(self.qLocale.toString(self.diseaseBoard.probaTransmission, precision = 2))
        TIV.setValidator(QDoubleValidator(0.0, 1.0, 2))
        TIV.textChanged.connect(self.updateR0)
        TIV.setAlignment(Qt.AlignRight)
        TIV.setFixedWidth(40)
        confgrid.addWidget(TI, CONF_LIGNE_PROBA_TRANSMISSION, 0)
        confgrid.addWidget(TIV, CONF_LIGNE_PROBA_TRANSMISSION, 1)

        TI = QLabel("Taux Mortalité : ")
        TIV = QLineEdit(self.qLocale.toString(self.diseaseBoard.tauxMortalite, precision = 2))
        TIV.setValidator(QDoubleValidator(0.0, 1.0, 2))
        TIV.setValidator(QDoubleValidator(0.0, 1.0, 2))
        TIV.setAlignment(Qt.AlignRight)
        TIV.setFixedWidth(40)
        confgrid.addWidget(TI, CONF_LIGNE_TAUX_MORTALITE, 0)
        confgrid.addWidget(TIV, CONF_LIGNE_TAUX_MORTALITE, 1)

        TI = QLabel("Délai Transmission : ")
        TIV = QLineEdit(self.qLocale.toString(self.diseaseBoard.delaiContagion))
        TIV.setAlignment(Qt.AlignRight)
        TIV.textChanged.connect(self.updateR0)
        TIV.setFixedWidth(40)
        confgrid.addWidget(TI, CONF_LIGNE_DELAI_RETABLISSEMENT, 0)
        confgrid.addWidget(TIV, CONF_LIGNE_DELAI_RETABLISSEMENT, 1)

        TI = QLabel("Délai Mortalité : ")
        TIV = QLineEdit(self.qLocale.toString(self.diseaseBoard.delaiMortalite))
        TIV.setAlignment(Qt.AlignRight)
        TIV.setFixedWidth(40)
        confgrid.addWidget(TI, CONF_LIGNE_DELAI_MORTALITE, 0)
        confgrid.addWidget(TIV, CONF_LIGNE_DELAI_MORTALITE, 1)

        TI = QLabel("Taux Quarantaine : ")
        TIV = QLineEdit(self.qLocale.toString(self.diseaseBoard.tauxQuarantaine, precision = 2))
        TIV.setAlignment(Qt.AlignRight)
        TIV.setFixedWidth(40)
        confgrid.addWidget(TI, CONF_LIGNE_TAUX_QUARANTAINE, 0)
        confgrid.addWidget(TIV, CONF_LIGNE_TAUX_QUARANTAINE, 1)

        TI = QLabel("Délai Quarantaine : ")
        TIV = QLineEdit(str(self.diseaseBoard.delaiQuarantaine))
        TIV.setAlignment(Qt.AlignRight)
        TIV.setFixedWidth(40)
        confgrid.addWidget(TI, CONF_LIGNE_DELAI_QUARANTAINE, 0)
        confgrid.addWidget(TIV, CONF_LIGNE_DELAI_QUARANTAINE, 1)

        return confgrid

    def init_map(self, etat):
        # Add positions to the map
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                w = Pos(x, y)
                self.grid.addWidget(w, x, y)
                w.redraw(etat[x, y])

    def update_map(self, etat):
        # Add positions to the map
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                w = self.grid.itemAtPosition(x, y).widget()
                w.redraw(etat[x, y])

    def goButton_pressed(self):
        if (self.nb_tours_init == self.nb_tours):
            # Reconfiguration de la simulation
            self.diseaseBoard.probaTransmission = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(CONF_LIGNE_PROBA_TRANSMISSION, 1).widget().text())[0]
            self.diseaseBoard.tauxMortalite = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(CONF_LIGNE_TAUX_MORTALITE, 1).widget().text())[0]
            self.diseaseBoard.delaiContagion = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(CONF_LIGNE_DELAI_RETABLISSEMENT, 1).widget().text())[0]
            self.diseaseBoard.delaiMortalite = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(CONF_LIGNE_DELAI_MORTALITE, 1).widget().text())[0]
            self.diseaseBoard.tauxQuarantaine = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(CONF_LIGNE_TAUX_QUARANTAINE, 1).widget().text())[0]
            self.diseaseBoard.delaiQuarantaine = self.qLocale.toDouble(
                self.confgrid.itemAtPosition(CONF_LIGNE_DELAI_QUARANTAINE, 1).widget().text())[0]

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

    def nextButton_pressed(self):
        self.nb_tours = self.nb_tours - 1

        if self.nb_tours < 0:
            self.status = STATUS_STOPPED
            return

        self.nb_toursLabel.setText("%03d" % self.nb_tours)
        etat = self.diseaseBoard.prochain_tour()
        self.update_map(etat)
        self.grid.update()

    def resetButton_pressed(self):
        self.diseaseBoard.tauxImmunite = self.qLocale.toDouble(
            self.confgrid.itemAtPosition(CONF_LIGNE_TAUX_IMMUNITE, 1).widget().text())[0]

        self.diseaseBoard.reset(self.nb_tours_init)
        self.nb_tours = self.nb_tours_init
        self.nb_toursLabel.setText("%03d" % self.nb_tours)
        self.update_map(self.diseaseBoard.dernier_etat())

        self.goButton.setText("GO")
        self.status = STATUS_STOPPED

    def update_timer(self):
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
            etat = self.diseaseBoard.prochain_tour()
            self.update_map(etat)

    def updateR0(self):
        self.diseaseBoard.probaTransmission = self.qLocale.toDouble(
            self.confgrid.itemAtPosition(CONF_LIGNE_PROBA_TRANSMISSION, 1).widget().text())[0]
        self.diseaseBoard.delaiContagion = self.qLocale.toDouble(
            self.confgrid.itemAtPosition(CONF_LIGNE_DELAI_RETABLISSEMENT, 1).widget().text())[0]
        self.r0Label.setText("R0 = {:.3} ".format(self.diseaseBoard.R0))


if __name__ == '__main__':
    tours = 60
    board_size = 30
    nb_clusters = 3

    db = DiseaseBoard(board_size, tours, nb_clusters)
    db.tauxImmunite = 0.4
    # Entre 2 et 3 personnes contaminées par malade, si on considère qu'à chaque tour (a peu près un jour), on
    # a l'occasion de contaminer environ 15 personnes, et ce pendant la durée de la contamination, considérée comme
    # égale au délai de rétablissement

    db.delaiContagion = 7
    db.probaTransmission = 2 / 7
    db.delaiQuarantaine = 6
    db.tauxQuarantaine = 0.8

    app = QApplication([])
    window = MainWindow(board_size, tours, db)
    app.exec_()
