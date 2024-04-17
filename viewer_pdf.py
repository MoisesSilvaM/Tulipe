import os

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView  # , QWebEngineSettings
from os import path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Viewer")
        self.setGeometry(0, 28, 1000, 750)

        self.webView = QWebEngineView()
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PluginsEnabled, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PdfViewerEnabled, True)
        self.setCentralWidget(self.webView)

    def url_changed(self):
        self.setWindowTitle(self.webView.title())

    def go_back(self):
        self.webView.back()


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    if len(sys.argv) > 1:
        wd = os.path.dirname(os.path.abspath(__file__))
        url = (f"{wd}/Sumo/outputs/plots/{sys.argv[1]}")
        print(url)
        file_url = url.replace("\\", "/")
        print(file_url)
        win.webView.setUrl(QUrl(file_url))
    else:
        wd = path.dirname(path.abspath(sys.argv[0]))
        test_pdf = "test.pdf"
        win.webView.setUrl(QUrl(f"C:/Users/moise/PycharmProjects/pythonProjectDavide/Sumo/outputs/plots/histogram_edge_traveltime_Low_1h_0m_0s_12_closing[4726706#0].pdf"))
    sys.exit(app.exec())