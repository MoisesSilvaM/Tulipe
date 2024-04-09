#!/usr/bin/env python -W ignore::DeprecationWarning

import sys
import io
import json
import subprocess
import os
import time

from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets
from PyQt5.QtCore import QProcess, pyqtSignal, Qt, QUrl, QTimer, QThread, QThreadPool
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QApplication, QMainWindow, qApp, QLabel, QMessageBox, QFileDialog, QWidget, QVBoxLayout
import folium
from folium.plugins import MousePosition, Draw
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from Tulipe_project import Ui_MainWindow
from branca.element import Element
import sumolib
import libsumo as traci
import re
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')
import pandas as pd
from pylab import *
import subprocess
from multiprocessing import Process
from threading import Thread
from PyQt5.QtCore import pyqtSignal


class WebEnginePage(QWebEnginePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent


    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        print(msg)  # Check js errors
        if 'coordinates' in msg:
            self.parent.handleConsoleMessage(msg)


class AnotherWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layoutt = QtWidgets.QApplication(sys.argv)

        # if not filename:
        #    print("please select the .pdf file")
        #    sys.exit(0)
        self.view = QtWebEngineWidgets.QWebEngineView()
        settings = self.view.settings()
        settings.setAttribute(QtWebEngineWidgets.QWebEngineSettings.PluginsEnabled, True)
        self.view.resize(640, 480)

class LoadingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        #self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        self.label_animation = QtWidgets.QLabel(self)

        self.movie = QMovie('Herbert_Kickl.gif')
        #self.movie = QMovie('Loading_2.gif')
        self.label_animation.setMovie(self.movie)
        self.movie.start()
        self.show()
        #timer = QTimer(self)
        #self.startAnimation()
        #timer.singleShot(3000, self.stopAnimation)


    def startAnimation(self):
        self.movie.start()
        self.show()

    def stopAnimation(self):
        self.movie.stop()
        self.close()

class ClaseMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(ClaseMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.path_sumo_tools = os.environ["SUMO_TOOL"]
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.interval_list = []
        #self.view = AnotherWindow()
        #self.loading_screen = LoadingScreen()
        # self.find()
        #self.Animation()
        self.configurar()
        self.maps()

    def maps(self):
        # layout = QtWidgets.QVBoxLayout()
        # self.setLayout(layout)

        coordinate = (50.827939952244854, 4.371480840800054)
        m = folium.Map(location=coordinate,
                       zoom_start=14
                       )
        # self.layout.setHtml(m.get_root().render())
        # MousePosition().add_to(m)
        # print(m)

        m = self.add_customjs(m)
        # save map data to data object
        data = io.BytesIO()
        m.save(data, close_file=False)

        # webView = QWebEngineView()
        # start web engine
        page = WebEnginePage(self)
        self.webView.setPage(page)
        self.webView.setHtml(data.getvalue().decode())  # give html of folium map to webengine
        # self.label.addWidget(webView)
        # self.label.setLayout(self.webView)
        # layout.addWidget(self.label)

    def add_customjs(self, map_object):
        my_js = f"""{map_object.get_name()}.on("click",
                 function (e) {{
                    var data = `{{"coordinates": ${{JSON.stringify(e.latlng)}}}}`;
                    console.log(data)}});"""

        e = Element(my_js)
        html = map_object.get_root()
        html.script.get_root().render()
        # Insert new element or custom JS
        html.script._children[e.get_name()] = e

        return map_object

    def handleConsoleMessage(self, msg):
        data = json.loads(msg)
        lat = data['coordinates']['lat']
        lng = data['coordinates']['lng']
        # coords = f"lat: {lat} lon: {lng}"
        latitude = f"{lat}"
        longitude = f"{lng}"

        self.convert_to_street(latitude, longitude)

    def convert_to_street(self, lat, lon):
        net = sumolib.net.readNet('osm.net.xml')
        # print(lat)
        # print(lon)
        radius = 100
        x, y = net.convertLonLat2XY(lon, lat)
        edges = net.getNeighboringEdges(x, y, radius)
        #print(x)
        #print(y)
        # pick the closest edge
        if len(edges) > 0:
            distancesAndEdges = sorted([(dist, edge) for edge, dist in edges], key=lambda x: x[0])
            # print(distancesAndEdges)
            dist, closestEdge = distancesAndEdges[0]
            edge_id = closestEdge.getID()
            self.list_edgefrommap.setText(edge_id)
            # for deviation in edges:
            #    print(deviation.getID())

    def get_pos(self):
        print('self.m')

    def configurar(self):
        # value = self.comboBox.currentData(self.comboBox.currentIndex())
        # self.Boton.pressed.connect(self.start_process)
        # self.actionsalir.triggered.connect(qApp.quit)
        self.Button_generate_the_outputs.clicked.connect(self.generate_outputs)
        self.pushButton_close.clicked.connect(self.close_streets)
        self.pushButton_open.clicked.connect(self.open_streets)
        self.listView_closeroad.itemClicked.connect(self.incoming_roads)
        self.pushButton_run_simulation.clicked.connect(self.Animation)
        # self.label.layout().addWidget(self.view, 0, 0)
        # pressed.connect(self.generate_outputs)
        #
        # self.label_plot.setDisabled(False)
        # self.label_plot.clicked.connect(self.export_outputs)

    def Clicked(self, item):
        QMessageBox.information(self, "ListWidget", "You clicked: " + item.text())

    def run_simulation(self):

        #self.startAnimation()
        #z = threading.Thread(target=self.loading_screen.startAnimation(), args=())
        #z.start()
        #self.loading_screen.startAnimation()
        #time.sleep(0.5)

        self.set_interval_list()

        self.write_open_conf_files()
        self.execute_sumo(0)
        # x = threading.Thread(target=self.execute_sumo(0), args=())
        # x.start()
        print('Sumo Open finished')

        self.write_close_conf_files()
        self.execute_sumo(1)
        # y = threading.Thread(target=self.execute_sumo(1), args=())
        # y.start()
        print('Sumo Close finished')
        #if args == 1:
        #    self.loading_screen.stopAnimation()

        #QtCore.QTimer.singleShot(100, lambda: self.convert_xml_to_csv())
        self.convert_xml_to_csv()
        self.enable_output_intervals()

    def Animation(self):
        word = '-37346632'

        # with open(r"" + self.path + "\Sumo\osm.net.xml\osm.net.xml", 'r') as fp:
        #     for l_no, line in enumerate(fp):
        #         # search string
        #         if word in line:
        #             #for stg in line.splitlines():
        #             #res = line.partition("\"")
        #             #r = res.partition("\"")
        #             #res = line.split('name=')#, 1)
        #             #splitString = res[1]
        #             #res = line.split('name=')
        #             keyword = 'name='
        #             keyword, after_keyword = line.partition(keyword)
        #             print(after_keyword)
        #             #m = re.findall(r'name=\"(.+)\"', line)
        #             #print(m)
        #             #print('string found in a file')
        #             #print('Line Number:', l_no)
        #             #print('Line:', line)
        #             # don't look for next lines
        #             break

            # read all lines in a list
            # lines = fp.readlines()
            # for line in lines:
            #     # check if string present on a current line
            #     if line.find(word) != -1:
            #         print(word, 'string exists in file')
            #         print('Line Number:', lines.index(line))
            #         print('Line:', line)

        self.loading_screen = LoadingScreen()
        QtCore.QTimer.singleShot(100, lambda: self.run_simulation())

        #self.run_long_task()
        #self.threadpool = QThreadPool()
        #print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        #self.threadpool.start(self.loading_screen)
        #self.threadpool.start(self.loading_screen)
        #z = threading.Thread(target=self.loading_screen.startAnimation(), args=())
        #z.start()
        #self.loading_screen.startAnimation()



    def execute_sumo(self, args):
        #self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
        #content = "sumo -c Sumo\osm.sumocfg -a Sumo\osm.poly.xml"
        #os.system("sumo -c Sumo\osm.sumocfg")


        #subprocess.Popen(["sumo", "-c", "Sumo\osm.sumocfg"])#), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["sumo", '-c', 'Sumo\osm.sumocfg'])
        # self.process = QProcess()
        # self.process.start("sumo -c Sumo\osm.sumocfg")
        # self.process.close()
        #self.process = None

        if args == 1:
            self.loading_screen.stopAnimation()

        #self.process.close()
        #return args
        #print(subp)
        #print(output)
        #self.p.start(content)
        #self.p.waitForFinished()



    def enable_output_intervals(self):
        self.comboBox_plotoutputs.setDisabled(False)
        self.comboBox_plotoutputs.clear()
        self.comboBox_plotoutputs.addItem('All')
        for i in range(len(self.interval_list) - 1):
            self.comboBox_plotoutputs.addItem(str(self.interval_list[i]) + "_to_" + str(self.interval_list[i + 1]))
        self.label_plot.setDisabled(False)


    def set_interval_list(self):
        #if self.low_traffic.isChecked() == True:
        traffic_level = '36'
        if self.medium_traffic.isChecked() == True:
            traffic_level = '150'
        elif self.heavy_traffic.isChecked() == True:
            traffic_level = '400'

        start_time = int(self.spinBox_starttime.text())
        end_time = int(self.spinBox_endtime.text())
        intervals = int(self.spinBox_intervals.text())
        traffic_level = traffic_level
        if (end_time - start_time) < intervals:
            return
        values = round((end_time - start_time) / intervals)

        items = []
        item_names = []
        for numbers in range(intervals):
            items.append(start_time + (numbers * values))
        items.append(end_time)
            #item_names.append(start_time + (numbers * values))
        self.interval_list = items
        #print(self.interval_list)
        self.search_and_replace()
        self.generating_random_trips(traffic_level)
        #os.system("python \"" + self.path_sumo_tools + "\\xml\\xml2csv.py\" \"" + self.path + "\Sumo\outputs\edgedata_O_" + start_time + "_to_" + end_time + ".out.xml\"")
        # for i in range(len(items)-1):
        #     print(str(items[i]) + "_to_" + str(items[i+1]))

    def search_and_replace(self):
        os.system("copy Sumo\osm.original.sumocfg Sumo\osm.sumocfg")
        start_time = self.spinBox_starttime.text()
        end_time = self.spinBox_endtime.text()
        with open("Sumo\osm.sumocfg", 'r') as file:
            file_contents = file.read()

            updated_contents = file_contents.replace("start_time", start_time).replace("end_time", end_time)

        with open("Sumo\osm.sumocfg", 'w') as file:
            file.write(updated_contents)


    def generating_random_trips(self, traffic_level):
        start_time = self.spinBox_starttime.text()
        end_time = self.spinBox_endtime.text()
        #os.system("python \"" + self.path_sumo_tools + "\ptlines2flows.py\" -n osm.net.xml.gz -b " + start_time + " -e " + end_time + " -p " + values + " --random-begin --seed 42 --ptstops osm_stops.add.xml --ptlines osm_ptlines.xml -o osm_pt.rou.xml --ignore-errors --vtype-prefix pt_ --stopinfos-file stopinfos.xml --routes-file vehroutes.xml --trips-file trips.trips.xml --min-stops 0 --extend-to-fringe --verbose")
        os.system("python \"" + self.path_sumo_tools + "\\randomTrips.py\" -n Sumo\osm.net.xml.gz --fringe-factor 5 --insertion-density " + traffic_level + " -o Sumo\osm.passenger.trips.xml -r Sumo\osm.passenger.rou.xml -b " + start_time + " -e " + end_time + " --trip-attributes \"departLane=\\\"best\\\"\" --fringe-start-attributes \"departSpeed=\\\"max\\\"\" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class passenger --vclass passenger --prefix veh --min-distance 300 --min-distance.fringe 10 --allow-fringe.min-length 1000 --lanes")

    def write_open_conf_files(self):
        start_time = self.spinBox_starttime.text()
        end_time = self.spinBox_endtime.text()
        os.system("copy Sumo\osm.poly.original.xml Sumo\osm.poly.xml")
        f = open("Sumo\osm.poly.xml", "a")
        #f.seek(2)
        #f.truncate()
        #f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        #f.write(
        #    "<additional xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://sumo.dlr.de/xsd/additional_file.xsd\">\n")
        #x = 0
        for i in range(len(self.interval_list)-1):
            f.write("    <edgeData id=\"" + str(self.interval_list[i]) + "_to_" + str(self.interval_list[i+1]) + "\" file=\"outputs/edgedata_O_" + start_time + "_to_" + end_time + ".out.xml\" begin=\"" + str(self.interval_list[i]) + "\" end=\"" + str(self.interval_list[i+1]) + "\" excludeEmpty=\"True\"/>\n")
        #    x = x + 1
        #f.write("    <edgeData id=\"" + str(self.interval_list[x]) + "_to_" + end_time + "\" file=\"outputs/edgedata_R_" + start_time + "_to_" + end_time + ".out.xml\" begin=\"" + str(self.interval_list[x]) + "\" end=\"" + end_time + "\" excludeEmpty=\"True\"/>\n")
        f.write("</additional>")
        f.close()

        #os.system("python3 /usr/share/sumo/tools/xml/xml2csv.py Sumo/edgedata_O" + start_time + "_to_" + end_time + ".out.xml")

    def write_close_conf_files(self):
        #path = os.path.dirname(os.path.abspath(__file__))
        start_time = self.spinBox_starttime.text()
        end_time = self.spinBox_endtime.text()
        net = sumolib.net.readNet('osm.net.xml')
        list_edgeClosed = [self.listView_closeroad.item(x).text() for x in range(self.listView_closeroad.count())]
        os.system("copy Sumo\osm.poly.original.xml Sumo\osm.poly.xml")
        f = open("Sumo\osm.poly.xml", "a")
        #f.seek(0)
        #f.truncate()
        #f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        #f.write(
        #    "<additional xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://sumo.dlr.de/xsd/additional_file.xsd\">\n")
        #x=0
        for i in range(len(self.interval_list)-1):
            f.write("    <edgeData id=\"" + str(self.interval_list[i]) + "_to_" + str(self.interval_list[i+1]) + "\" file=\"outputs/edgedata_R_" + start_time + "_to_" + end_time + ".out.xml\" begin=\"" + str(self.interval_list[i]) + "\" end=\"" + str(self.interval_list[i+1]) + "\" excludeEmpty=\"True\"/>\n")
        #    x=x+1
        #f.write("    <edgeData id=\"" + str(self.interval_list[x]) + "_to_" + end_time + "\" file=\"outputs/edgedata_R_" + start_time + "_to_" + end_time + ".out.xml\" begin=\"" + str(self.interval_list[x]) + "\" end=\"" + end_time + "\" excludeEmpty=\"True\"/>\n")
        #f.write("    <edgeData id=\"" + start_time + "_to_" + end_time + "\" file=\"outputs/edgedata_R_" + start_time + "_to_" + end_time + ".out.xml\" begin=\"" + start_time + "\" end=\"" + end_time + "\" excludeEmpty=\"True\"/>\n")
        f.write("    <!-- Rerouting -->\n")
        if len(list_edgeClosed) > 0:
            for edgeclose in list_edgeClosed:
                nextEdges_incoming = net.getEdge(edgeclose).getIncoming()
                #print(nextEdges_incoming)
                text = ""
                for dev_edge in nextEdges_incoming:
                    text = text + dev_edge.getID() + " "
                text = text[:-1]
                # print(text)
                f.write("    <rerouter id=\"close_"+edgeclose+"\" edges=\"" + text + "\">\n")
                f.write("        <interval begin=\"" + start_time + "\" end=\"" + end_time + "\">\n")
                f.write("            <closingReroute id=\"" + edgeclose + "\" disallow=\"all\"/>\n")
                f.write("        </interval>\n")
                f.write("    </rerouter>\n")
        f.write("</additional>")
        f.close()


    def convert_xml_to_csv(self):
        start_time = self.spinBox_starttime.text()
        end_time = self.spinBox_endtime.text()
        # if os.path.exists(self.path + "\Sumo\outputs\edgedata_O_" + start_time + "_to_" + end_time + ".out.xml"):
        #     os.remove(self.path + "\Sumo\outputs\edgedata_O_" + start_time + "_to_" + end_time + ".out.xml")
        # if os.path.exists(self.path + "\Sumo\outputs\edgedata_R_" + start_time + "_to_" + end_time + ".out.xml"):
        #     os.remove(self.path + "\Sumo\outputs\edgedata_R_" + start_time + "_to_" + end_time + ".out.xml")
        os.system("python \"" + self.path_sumo_tools +"\\xml\\xml2csv.py\" " + self.path + "\Sumo\outputs\edgedata_O_" + start_time + "_to_" + end_time + ".out.xml")
        os.system("python \"" + self.path_sumo_tools + "\\xml\\xml2csv.py\" " + self.path + "\Sumo\outputs\edgedata_R_" + start_time + "_to_" + end_time + ".out.xml")

    def open_streets(self):
        if self.listView_closeroad.currentItem() is not None:

            net = sumolib.net.readNet('osm.net.xml')
            item_id = self.listView_closeroad.currentItem().text()
            index = self.listView_closeroad.currentRow()
            self.listView_closeroad.takeItem(index)
            #nextEdges_outcoming = net.getEdge(item_id).getOutgoing()
            nextEdges_incoming = net.getEdge(item_id).getIncoming()

            for incoming in nextEdges_incoming:
                items_i = self.listView_deviation.findItems(incoming.getID(), Qt.MatchContains)
                if items_i:  # we have found something
                    self.listView_deviation.takeItem(self.listView_deviation.row(items_i[0]))

            #for outcoming in nextEdges_outcoming:
            #    items_o = self.listView_deviation.findItems(outcoming.getID(), Qt.MatchContains)
            #    if items_o:  # we have found something
            #        self.listView_deviation.takeItem(self.listView_deviation.row(items_o[0]))

    def close_streets(self):
        item_id = self.list_edgefrommap.text()
        net = sumolib.net.readNet('osm.net.xml')
        edgeIDs = [e.getID() for e in net.getEdges()]
        edgeClosed = [self.listView_closeroad.item(x).text() for x in range(self.listView_closeroad.count())]
        # print(edgeClosed)
        if item_id in edgeIDs and item_id not in edgeClosed:
            self.listView_closeroad.addItem(item_id)

            # nextEdges_outcoming = net.getEdge(item_id).getOutgoing()
            # nextEdges_incoming = net.getEdge(item_id).getToNode().getIncoming()
            # print(nextEdges_incoming)
            # print(nextEdges_outcoming)
            # items = []
            # for incoming in nextEdges_incoming:
            #    items.append(incoming.getID())
            # for outcoming in nextEdges_outcoming:
            #    items.append(outcoming.getID())
            # self.listView_deviation.addItems(items)

    def incoming_roads(self, item):
        item_id = item.text()
        net = sumolib.net.readNet('osm.net.xml')
        self.listView_deviation.clear()
        #nextEdges_outcoming = net.getEdge(item_id).getOutgoing()
        nextEdges_incoming = net.getEdge(item_id).getIncoming()
        # print("nextEdges_incoming")
        # print(nextEdges_incoming)
        # print("nextEdges_outcoming")
        # print(nextEdges_outcoming)
        items = []
        for incoming in nextEdges_incoming:
            items.append(incoming.getID())
        #for outcoming in nextEdges_outcoming:
        #    items.append(outcoming.getID())
        #print(items)
        self.listView_deviation.addItems(items)


    def find(self):
        # finding the content of current item in combo box
        content = self.comboBox.itemText(self.comboBox.currentIndex())
        # content = self.comboBox.currentText()
        # showing content on the screen through label
        self.labResultado.setText("Content : " + content)


    def generate_outputs(self):
        item = self.comboBox.itemText(self.comboBox.currentIndex())
        start_time = self.spinBox_starttime.text()
        end_time = self.spinBox_endtime.text()
        interval = self.comboBox_plotoutputs.currentText()
        edgedata_csv_file_O = self.path + "\Sumo\outputs\edgedata_O_" + start_time + "_to_" + end_time + ".out.csv"
        edgedata_csv_file_R = self.path + "\Sumo\outputs\edgedata_R_" + start_time + "_to_" + end_time + ".out.csv"
        #print(edgedata_csv_file_O)
        dO = pd.read_csv(edgedata_csv_file_O, sep=";")
        dR = pd.read_csv(edgedata_csv_file_R, sep=";")
        #print(dO)
        dfO = self.detectors_out_to_table(dO, item)
        dfR = self.detectors_out_to_table(dR, item)
        #df = dfR - dfO
        #print('dO')
        #print(dO)
        #print('dfO')
        #print(dfO.head())
        #if os.path.exists(self.path +'\Sumo\outputs\histogram_' + item + '.pdf'):
        #    os.remove(self.path +'\Sumo\outputs\histogram_' + item + '.pdf')
        #    print("delete")
        if interval == 'All':
            #print()
            self.plots_hist(dO, dfO, dfR, item)
        else:
            #dfOi = dfO[str(interval)]
            #dfRi = dfR[str(interval)]
            self.plots_one_hist(dfO, dfR, item, interval)



            #self.interval_out_to_table(dfO, interval)
            #print(dfOi)
            #dfRi = self.interval_out_to_table(dfR, interval)
            #self.plots_hist(dO, dfOi, dfRi, item)
        #df.to_csv('OUTPUT.csv', sep=";", na_rep='0')
        #time_intervals = dO['interval_id'].unique()
        #print(time_intervals)


    def detectors_out_to_table(self, sim_data_df, field_name):
        # parse all the intervals in the edgedata file
        time_intervals = sim_data_df['interval_id'].unique()
        data_dict = {}
        for time_interval in time_intervals:
            # get the DF related to time_interval
            data_interval = sim_data_df.loc[sim_data_df['interval_id'] == time_interval]
            #print(data_interval)
            # get the IDs of the edges that has an edgedata output value in the current time interval
            list_edges = data_interval['edge_id'].unique()
            for edge_id in list_edges:
                # get the data for all the edges
                data = data_interval.loc[data_interval['edge_id'] == edge_id][field_name]
                if time_interval not in data_dict:
                    data_dict[time_interval] = {}
                data_dict[time_interval][edge_id] = data.item()
        return pd.DataFrame.from_dict(data_dict)

    def plots_hist(self, dO, dfO, dfR, arg):
        time_intervals = dO['interval_id'].unique()
        idx = 1
        num = len(time_intervals)
        fig, ax = plt.subplots(figsize=(10, 20), nrows=2, ncols=1, sharex=True, sharey=True)
        for name in time_intervals:
            subplot(num, 1, idx)
            ax = plt.hist([dfO[name], dfR[name]], bins=10, label=['open', 'rerouting'])  # , range=[0,rang_max])
            plt.title(name)
            plt.xlabel("Values")
            plt.ylabel("Frequency")
            plt.legend(loc='upper right')
            plt.margins(x=0.02, tight=True)
            ax = plt.gca()
            idx += 1
            # plt.xlim(0,40)
            # plt.ylim(0, 110)
            # mode_index = ax.argmax()
            # print(mode_index)
        plt.suptitle('Comparing timeframes in term of ' + arg + ', closing and nonclosing edges', fontsize=16, y=1)
        plt.tight_layout()
        fig.savefig('Sumo\outputs\histogram_' + arg + '.pdf', bbox_inches='tight')
        fig.savefig('Sumo\outputs\histogram_' + arg + '.png', bbox_inches='tight')
        self.generate_png_outputs()

    def plots_one_hist(self, dfO, dfR, arg, interval):
        #intervals = [str(interval)]
        fig, ax = plt.subplots(figsize=(10, 20), nrows=2, ncols=1, sharex=True, sharey=True)
        subplot(1, 1, 1)
        ax = plt.hist([dfO[interval], dfR[interval]], bins=10, label=['open', 'rerouting'])  # , range=[0,rang_max])
        plt.title(interval)
        plt.xlabel("Values")
        plt.ylabel("Frequency")
        plt.legend(loc='upper right')
        plt.margins(x=0.02, tight=True)
        ax = plt.gca()
        plt.suptitle('Comparing Timeframe ' + interval + ' in term of ' + arg + ', closing and nonclosing edges', fontsize=16, y=1)
        plt.tight_layout()
        fig.savefig('Sumo\outputs\histogram_' + arg + '.pdf', bbox_inches='tight')
        fig.savefig('Sumo\outputs\histogram_' + arg + '.png', bbox_inches='tight')
        self.generate_png_outputs()

    # def generate_outputs2(self):
    #     content = self.comboBox.itemText(self.comboBox.currentIndex())
    #     start_time = self.spinBox_starttime.text()
    #     end_time = self.spinBox_endtime.text()
    #     self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
    #     # self.p.finished.connect(self.process_finished)
    #     # Clean up once complete.
    #     content = "python ./EdgedataToTable.py " + content + " " + start_time + " " + end_time
    #     #print(content)
    #     self.p.start(content)
    #     self.p.finished.connect(self.generate_png_outputs)


    def generate_png_outputs(self):
        content = self.comboBox.itemText(self.comboBox.currentIndex())
        #self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
        #print(content)
        self.label_plot.setPixmap(QtGui.QPixmap("Sumo\outputs\histogram_" + content + ".png"))
        #self.label_plot.setDisabled(False)
        self.label_plot.clicked.connect(self.export_outputs)


    def export_outputs(self):
        # root = os.path.dirname(sys.argv[0])
        content = self.comboBox.itemText(self.comboBox.currentIndex())
        # # print(root)
        # filename = root + "\Sumo\outputs\histogram_" + content + ".pdf"  # "\\test.pdf" #sys.argv[1]
        #
        # url = QtCore.QUrl.fromLocalFile(filename)
        # self.view.load(url)
        #self.view.show()
        # content = self.comboBox.itemText(self.comboBox.currentIndex())
        #os.system("python viewer_pdf2.py \Sumo\outputs\histogram_" + content + ".pdf")
        # cmd = "python viewer_pdf2.py \Sumo\outputs\histogram_" + content + ".pdf"
        # subprocess.Popen(cmd)
        self.p = QProcess()
        self.p.start("python viewer_pdf2.py \Sumo\outputs\histogram_" + content + ".pdf")
        #self.p.waitForFinished()
        self.p.close()
        self.p = None



    # def export_outputs2(self):
    #     #self.w = export_outputs2()
    #     #root = os.path.dirname(sys.argv[0])
    #     root = os.path.dirname(os.path.abspath(__file__))
    #     #print(root)
    #     filename = root + "\\test.pdf" #sys.argv[1]
    #     #print(filename)
    #     #    if not filename:
    #     #        print("please select the .pdf file")
    #     #        sys.exit(0)
    #     view = QtWebEngineWidgets.QWebEngineView()
    #     settings = view.settings()
    #     settings.setAttribute(QtWebEngineWidgets.QWebEngineSettings.PluginsEnabled, True)
    #     url = QtCore.QUrl.fromLocalFile(filename)
    #     view.load(url)
    #     view.resize(640, 480)
    #     view.show()


    def closeEvent(self, event):
        print("User has clicked the closed buttom on the main window")
        self.clear()
        # event.accept()


def main():
    #sumo_tools = os.environ["SUMO_TOOL"]
    #path = os.path.dirname(os.path.abspath(__file__))
    app = QApplication(sys.argv)
    ventana = ClaseMainWindow()
    ventana.show()
    ret = app.exec_()
    sys.exit(ret)


if __name__ == '__main__':
    main()
