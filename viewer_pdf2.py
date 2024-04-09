import sys
import os
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
from PyQt5.QtCore import QUrl


def main():
    #    print(
    #        f"PyQt5 version: {QtCore.PYQT_VERSION_STR}, Qt version: {QtCore.QT_VERSION_STR}"
    #    )

    app = QtWidgets.QApplication(sys.argv)
    # filename, _ = QtWidgets.QFileDialog.getOpenFileName(None, filter="PDF (*.pdf)")
    root = os.path.dirname(sys.argv[0])
    # print(root)
    filename = root + sys.argv[1]  # "\\test.pdf" #sys.argv[1]
    # print(filename)
    if not filename:
        print("please select the .pdf file")
        sys.exit(0)
    view = QtWebEngineWidgets.QWebEngineView()
    settings = view.settings()
    settings.setAttribute(QtWebEngineWidgets.QWebEngineSettings.PluginsEnabled, True)
    url = QtCore.QUrl.fromLocalFile(filename)
    view.load(url)
    view.resize(640, 480)
    view.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
