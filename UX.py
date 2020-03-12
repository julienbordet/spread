#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from diseaseBoard import diseaseBoard

DEFAULT_BOARD_SIZE = 50
DEFAULT_TOUR = 50
STATE = {
    "SAIN":0,
    "MALADE":1,
    "IMMUN": 2,
    "QUARANTAINE": 3,
    "DECEDE": 4
}

STATUS_PLAYING = 1
STATUS_STOPPED = 0

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

    def reveal(self):
        self.is_revealed = True
        self.update()

    def click(self):
        pass
        return
        if not self.is_revealed:
            self.reveal()
            if self.adjacent_n == 0:
                self.expandable.emit(self.x, self.y)

        self.clicked.emit()

    def mouseReleaseEvent(self, e):
        pass

class MainWindow(QMainWindow):
    def __init__(self, board_size, nb_tours, dB, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.status = STATUS_STOPPED

        self.board_size = board_size

        self.diseaseBoard = dB
        self.nb_tours_init = nb_tours
        self.nb_tours = nb_tours

        w = QWidget()
        hb = QHBoxLayout()

        self.nb_toursLabel = QLabel()
        self.nb_toursLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.nb_toursLabel.setText("%03d" % self.nb_tours)

        self._timer = QTimer()
        self._timer.timeout.connect(self.update_timer)
        self._timer.start(100) # in ms

        self.goButton = QPushButton()
        self.goButton.setFixedSize(QSize(52, 32))
        self.goButton.setText("GO")
        self.goButton.setFlat(False)
        self.goButton.pressed.connect(self.goButton_pressed)

        self.nextButton = QPushButton()
        self.nextButton.setFixedSize(QSize(72, 32))
        self.nextButton.setText("NEXT")
        self.nextButton.setFlat(False)
        self.nextButton.pressed.connect(self.nextButton_pressed)

        self.resetButton = QPushButton()
        self.resetButton.setFixedSize(QSize(112, 32))
        self.resetButton.setText("RESET")
        self.resetButton.setFlat(False)
        self.resetButton.pressed.connect(self.resetButton_pressed)

        hb.addWidget(self.nb_toursLabel)
        hb.addWidget(self.goButton)
        hb.addWidget(self.nextButton)
        hb.addWidget(self.resetButton)

        vb = QVBoxLayout()
        vb.addLayout(hb)

        self.grid = QGridLayout()
        self.grid.setSpacing(2)

        vb.addLayout(self.grid)
        w.setLayout(vb)
        self.setCentralWidget(w)

        self.init_map(dB.dernier_etat())
        self.show()

    def init_map(self, etat):
        print(etat)
        # Add positions to the map
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                w = Pos(x, y)
                self.grid.addWidget(w, x, y)
                w.redraw(etat[x,y])

    def update_map(self, etat):
        # Add positions to the map
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                w = self.grid.itemAtPosition(x, y).widget()
                w.redraw(etat[x,y])

    def goButton_pressed(self):
        if self.status == STATUS_STOPPED:
            self.status = STATUS_PLAYING
        else:
            self.status = STATUS_STOPPED

    def nextButton_pressed(self):
        self.nb_tours = self.nb_tours - 1
        print("next %d" % self.nb_tours)

        if self.nb_tours < 0:
            self.status = STATUS_STOPPED
            return

        self.nb_toursLabel.setText("%03d" % self.nb_tours)
        etat = self.diseaseBoard.prochain_tour()
        print("next : gonna update")
        self.update_map(etat)
        print("next : updated")
        self.grid.update()

    def resetButton_pressed(self):
        print("Reset pressed")
        self.diseaseBoard.reset(self.nb_tours_init)
        print("db Reset done")
        self.nb_tours = self.nb_tours_init
        self.nb_toursLabel.setText("%03d" % self.nb_tours)

        self.update_map(self.diseaseBoard.dernier_etat())
        print("init map done")

    def update_timer(self):
        if self.status == STATUS_PLAYING:
            self.nb_tours = self.nb_tours - 1

            if self.nb_tours < 0:
                self.status = STATUS_STOPPED
                return

            self.nb_toursLabel.setText("%03d" % self.nb_tours)
            etat = self.diseaseBoard.prochain_tour()
            self.update_map(etat)

if __name__ == '__main__':
    tours = DEFAULT_TOUR
    board_size = 10
    nb_clusters = 3

    db = diseaseBoard(board_size, tours, nb_clusters)
    db.setTauxImmunite(0.4)
    # Entre 2 et 3 personnes contaminées par malade, si on considère qu'à chaque tour (a peu près un jour), on
    # a l'occasion de contaminer environ 15 personnes, et ce pendant la durée de la contamination, considérée comme
    # égale au délai de rétablissement

    delaiRetablissement = 10

    db.setDelaiRetablissement(delaiRetablissement)
    db.setProbaContag(2/7/delaiRetablissement)
    db.setDelaiQuarantaine(6)
    db.setTauxQuarantaine(0.8)

    app = QApplication([])
    window = MainWindow(board_size, tours, db)
    app.exec_()
