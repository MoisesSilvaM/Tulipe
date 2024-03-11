#!/usr/bin/env python -W ignore::DeprecationWarning
import sys
from PyQt5 import (QtCore, QtGui, QtWidgets)
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import QApplication, QMainWindow, qApp

from formulario_desplegable import Ui_MainWindow


class ClaseMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(ClaseMainWindow, self).__init__(parent)
        self.setupUi(self)
        #self.find()
        self.configurar()

    def configurar(self):
        #        value = self.comboBox.currentData(self.comboBox.currentIndex())
        self.Boton.pressed.connect(self.start_process)
        self.actionsalir.triggered.connect(qApp.quit)


    def find(self):
        # finding the content of current item in combo box
        content = self.comboBox.itemText(self.comboBox.currentIndex())
        #content = self.comboBox.currentText()
        # showing content on the screen through label
        self.labResultado.setText("Content : " + content)


    def start_process(self):
        content = self.comboBox.itemText(self.comboBox.currentIndex())
        self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
        #self.p.finished.connect(self.process_finished)
        # Clean up once complete.
        content = "python EdgedataToTable.py " + content
        print(content)
        self.p.start(content)


    def closeEvent(self, event):
        print("User has clicked the closed buttom on the main window")
        self.clear()
        #event.accept()

def main():
    app = QApplication(sys.argv)
    ventana = ClaseMainWindow()
    ventana.show()
    ret = app.exec_()
    sys.exit(ret)


if __name__ == '__main__':
    main()
