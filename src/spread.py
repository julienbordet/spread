#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtGui import (QColor, QPainter, QBrush, QPen, QPalette, QDoubleValidator, QIntValidator,
                         QCursor)
from PyQt5.QtWidgets import (QWidget, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLineEdit, QApplication)
from PyQt5.QtCore import (pyqtSignal, QSize, QPoint, Qt, QEvent, QLocale, QTimer)
import pyqtgraph as pg
import sys
import getopt
from typing import Optional, Union, cast

from DiseaseBoard import DiseaseBoard, BoardState

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

PARAM_TO_PROPERTY = {
    IMMUNITY_RATE_PARAM: 'immunity_rate',
    CLUSTER_NB_PARAM: 'cluster_nbr',
    TRANSMISSION_RATE_PARAM: 'contagion_rate',
    MORTALITY_RATE_PARAM: 'mortality_rate',
    MORTALITY_DELAY_PARAM: 'mortality_delay',
    CONTAGION_DELAY_PARAM: 'contagion_delay',
    HOSPITALIZED_RATE_PARAM: 'hospitalized_rate',
    HOSPITALIZED_DELAY_PARAM: 'hospitalized_delay',
    QUARANTINE_RATE_PARAM: 'quarantine_rate',
    DIAGNOSIS_DELAY_PARAM: 'diagnosis_delay',
    SOCIALDISTANCING_DELAY_PARAM: 'social_distancing_delay',
    SOCIALDISTANCING_RATE_PARAM: 'social_distancing_contagion_rate',
}

PROPERTY_TO_PARAM = {v: k for k, v in PARAM_TO_PROPERTY.items()}

LANG_FR: int = 0
LANG_US: int = 1

INFECTED_PLOT = 0
HOSPITALIZED_PLOT = 1
QUARANTINED_PLOT = 2
PLOT_NB = 3


class Pos(QWidget):
    expandable = pyqtSignal(int, int, name="expandable")
    clicked = pyqtSignal(name="clicked")
    ohno = pyqtSignal(name="ohno")

    # stores floating label list, as we might miss some leaveEvent, we need a way to hide them all
    activeLabelList: list = []

    def __init__(self, lang: int) -> None:
        super(Pos, self).__init__(parent=None)

        self.setFixedSize(QSize(10, 10))

        self.lang: int = lang

        self.floatingLabel: QLabel = QLabel()
        self.floatingLabel.setWindowFlags(Qt.FramelessWindowHint)
        self.floatingLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.patient_state: Optional[int] = None

    def redraw(self, state: int) -> None:
        self.patient_state = state
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = event.rect()

        outer: Optional[Union[QColor, Qt.GlobalColor]] = None
        inner: Optional[Union[QColor, Qt.GlobalColor]] = None

        if self.patient_state == STATE["SUSCEPTIBLE"]:
            blue_color: QColor = QColor(210, 210, 255)
            outer, inner = blue_color, blue_color
        elif self.patient_state == STATE["INFECTED"]:
            outer, inner = Qt.darkRed, Qt.red
        elif self.patient_state == STATE["DECEASED"]:
            outer, inner = Qt.black, Qt.black
        elif self.patient_state == STATE["QUARANTINE"]:
            outer, inner = Qt.darkYellow, Qt.yellow
        elif self.patient_state == STATE["IMMUNE"]:
            outer, inner = Qt.gray, Qt.lightGray
        elif self.patient_state == STATE["HOSPITALIZED"]:
            darkblue_color: QColor = QColor(100, 110, 200)
            outer, inner = darkblue_color, darkblue_color

        if outer is None or inner is None:
            raise ValueError("Invalid color")

        p.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(r)

    @staticmethod
    def click() -> None:
        pass
        return

        # self.clicked.emit()

    def mouseReleaseEvent(self, e) -> None:
        pass

    def enterEvent(self, event) -> None:
        if event.type() == QEvent.Enter and not self.floatingLabel.isVisible():
            self.cleanFloatingLabel()

            # Get current position of the cursor as a QPoint
            position: QPoint = QCursor.pos()  # type: ignore
            position += QPoint(0, -20)  # Move the floating label up to improve its visibility

            if self.patient_state is None:
                raise ValueError("Invalid patient state")

            label_text = STATE_NAME[self.patient_state][self.lang]
            self.floatingLabel.setText(label_text)
            self.floatingLabel.move(position)

            self.floatingLabel.setVisible(True)
            self.floatingLabel.update()

            Pos.activeLabelList.append(self.floatingLabel)

    def leaveEvent(self, event) -> None:
        if event.type() == QEvent.Leave:
            self.cleanFloatingLabel()

    @staticmethod
    def cleanFloatingLabel() -> None:
        for i, label in enumerate(Pos.activeLabelList):
            label.setVisible(False)
            label.update()

        Pos.activeLabelList = []


class MainWindow(QMainWindow):
    def __init__(self, newboard_size: int, round_nbr: int, disease_board: DiseaseBoard) -> None:
        super(MainWindow, self).__init__(parent=None)
        self.setWindowTitle("spread : disease spread simple model")

        self.lang: int

        self.qLocale = QLocale()
        if self.qLocale.name()[0:2] == "fr":
            self.lang = LANG_FR
        else:
            self.lang = LANG_US

        self.status = STATUS_STOPPED

        self.board_size = newboard_size
        self.diseaseBoard: DiseaseBoard = disease_board
        self.total_round_nbr = round_nbr

        # w est le Widget QT affiché dans la fenêtre
        w = QWidget(self)

        # hb : la bande horizontale supérieure de la fenêtre
        hb = QHBoxLayout()
        hb.addStretch(1)

        self.nb_toursLabel = QLabel()
        self.nb_toursLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.nb_toursLabel.setText("%03d" % 0)

        self._timer = QTimer(parent=self)
        self._timer.timeout.connect(self.updateTimer)  # type: ignore
        self._timer.start(100)  # in ms

        self.goButton = QPushButton("GO")
        self.goButton.setFixedSize(QSize(72, 32))
        self.goButton.setFlat(False)
        self.goButton.pressed.connect(self.goButtonPressed)  # type: ignore

        self.nextButton = QPushButton("NEXT")
        self.nextButton.setFixedSize(QSize(72, 32))
        self.nextButton.setFlat(False)
        self.nextButton.pressed.connect(self.nextButtonPressed)  # type: ignore

        self.resetButton = QPushButton("RESET")
        self.resetButton.setFixedSize(QSize(82, 32))
        self.resetButton.setFlat(False)
        self.resetButton.pressed.connect(self.resetButtonPressed)  # type: ignore

        hb.addWidget(self.nb_toursLabel)  # type: ignore
        hb.addWidget(self.goButton)  # type: ignore
        hb.addWidget(self.nextButton)  # type: ignore
        hb.addWidget(self.resetButton)  # type: ignore

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
        self.confgrid: QGridLayout = self.setupConfGrid()

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
        graph_widget.setXRange(0, self.total_round_nbr, padding=0.0)  # type: ignore
        graph_layout.addWidget(graph_widget)  # type: ignore

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
        footer_layout.addWidget(pop_label)  # type: ignore

        r0_label = QLabel("R0 = " + self.qLocale.toString(self.diseaseBoard.R0))
        r0_label.setStyleSheet("color: grey")
        self.r0_label = r0_label
        footer_layout.addWidget(r0_label)  # type: ignore

        ratio_label = QLabel("#infected / #detected = 1")
        ratio_label.setStyleSheet("color: grey")
        self.ratio_label = ratio_label
        footer_layout.addWidget(ratio_label)  # type: ignore

        deceased_label = QLabel("#Death = " + self.qLocale.toString(self.diseaseBoard.deceased_nbr))
        deceased_label.setStyleSheet("color: grey")
        self.deceased_label = deceased_label
        footer_layout.addWidget(deceased_label)  # type: ignore

        infected_label = QLabel("#Sick = " + self.qLocale.toString(self.diseaseBoard.sick_nbr))
        infected_label.setStyleSheet("color: grey")
        self.infectedLabel = infected_label
        footer_layout.addWidget(infected_label)  # type: ignore

        vb.addLayout(footer_layout)

        w.setLayout(vb)
        self.setCentralWidget(w)

        self.initMap(disease_board.last_board())
        self.show()

    def setupConfGrid(self) -> QGridLayout:

        confgrid = QGridLayout()
        confgrid.setSpacing(1)

        for param, data in CONF_ELEMENTS.items():
            lbl = QLabel(data[0][self.lang])

            qle = QLineEdit()

            property_to_read = PARAM_TO_PROPERTY[param]
            value = getattr(self.diseaseBoard, property_to_read)
            if param in [IMMUNITY_RATE_PARAM, TRANSMISSION_RATE_PARAM, MORTALITY_RATE_PARAM,
                         QUARANTINE_RATE_PARAM, SOCIALDISTANCING_RATE_PARAM]:
                qle.setText(self.qLocale.toString(value, precision=2))  # type: ignore
            else:
                qle.setText(self.qLocale.toString(value))

            if param in [TRANSMISSION_RATE_PARAM, CONTAGION_DELAY_PARAM]:
                qle.textChanged.connect(self.updateR0)  # type: ignore

            if data[1] == "double":
                qle.setValidator(QDoubleValidator(0.0, 1.0, 2))
            elif data[1] == "int":
                qle.setValidator(QIntValidator(0, self.total_round_nbr))

            qle.setAlignment(Qt.AlignRight)
            qle.setFixedWidth(40)

            confgrid.addWidget(lbl, param, 0)
            confgrid.addWidget(qle, param, 1)

        return confgrid

    def initMap(self, bs: BoardState) -> None:
        # Add positions to the map
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                w = Pos(self.lang)
                self.grid.addWidget(w, x, y)
                w.redraw(bs[x, y])

    def updateMap(self, bs: BoardState) -> None:
        # Add positions to the map
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                widget = self.grid.itemAtPosition(x, y).widget()
                my_pos = cast(Pos, widget)
                my_pos.redraw(bs[x, y])

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

        self.plots[INFECTED_PLOT].setData(range(0, round_nbr + 1),  # type: ignore
                                          self.diseaseBoard.infected_data)
        self.plots[HOSPITALIZED_PLOT].setData(range(0, round_nbr + 1),  # type: ignore
                                              self.diseaseBoard.hospitalized_data)
        self.plots[QUARANTINED_PLOT].setData(range(0, round_nbr + 1),  # type: ignore
                                             self.diseaseBoard.quarantined_data)

    def goButtonPressed(self) -> None:
        line_edit: QLineEdit

        if self.diseaseBoard.current_round == 0:
            # Reconfiguration de la simulation

            for key, value in PROPERTY_TO_PARAM.items():
                item = self.confgrid.itemAtPosition(value, 1)
                if item is not None:
                    line_edit = cast(QLineEdit, item.widget())
                    setattr(self.diseaseBoard, key, self.qLocale.toDouble(line_edit.text())[0])

        if self.status == STATUS_STOPPED:
            self.status = STATUS_PLAYING
            self.goButton.setText("PAUSE")

            for i in range(self.confgrid.rowCount()):
                widget = self.confgrid.itemAtPosition(i, 1).widget()

                line_edit = cast(QLineEdit, widget)
                line_edit.setReadOnly(True)
                line_edit.setStyleSheet("color: grey; selection-color: grey")
                line_edit.repaint()

        else:
            self.status = STATUS_STOPPED
            self.goButton.setText("GO")
            for i in range(self.confgrid.rowCount()):
                widget = self.confgrid.itemAtPosition(i, 1).widget()

                line_edit = cast(QLineEdit, widget)
                line_edit.setReadOnly(False)
                line_edit.setStyleSheet("color: black; selection-color: black")
                line_edit.repaint()

    def nextButtonPressed(self) -> None:
        if self.diseaseBoard.current_round + 1 > self.total_round_nbr:
            self.status = STATUS_STOPPED
            return

        etat: BoardState = self.diseaseBoard.next_round()
        self.nb_toursLabel.setText("%03d" % self.diseaseBoard.current_round)
        self.updateMap(etat)
        self.updateR0()
        self.grid.update()

    def resetButtonPressed(self) -> None:
        widget: QWidget = self.confgrid.itemAtPosition(IMMUNITY_RATE_PARAM, 1).widget()
        line_edit: QLineEdit = cast(QLineEdit, widget)
        self.diseaseBoard.immunity_rate = self.qLocale.toDouble(line_edit.text())[0]

        widget = self.confgrid.itemAtPosition(CLUSTER_NB_PARAM, 1).widget()
        line_edit = cast(QLineEdit, widget)
        self.diseaseBoard.cluster_nbr = self.qLocale.toInt(line_edit.text())[0]

        self.diseaseBoard.reset()
        self.nb_toursLabel.setText("%03d" % 0)
        self.updateMap(self.diseaseBoard.last_board())
        self.updateR0()

        self.goButton.setStyleSheet("color: black; selection-color: black")
        self.status = STATUS_STOPPED

    def updateTimer(self) -> None:
        if self.status == STATUS_PLAYING:

            if self.diseaseBoard.current_round + 1 > self.total_round_nbr or \
                    (self.diseaseBoard.sick_nbr == 0 and self.diseaseBoard.quarantined_nbr == 0):
                self.status = STATUS_STOPPED
                self.goButton.setStyleSheet("color: grey; selection-color: black")
                self.goButton.setText("GO")
                # Set text in goButton to dark gray

                for i in range(self.confgrid.rowCount()):
                    widget: QWidget = self.confgrid.itemAtPosition(i, 1).widget()
                    line_edit: QLineEdit = cast(QLineEdit, widget)
                    line_edit.setReadOnly(False)
                    line_edit.setStyleSheet("color: black; selection-color: black")
                    line_edit.repaint()

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

    db = DiseaseBoard(board_size, nb_clusters)
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
