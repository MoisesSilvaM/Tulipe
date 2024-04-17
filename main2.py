import os
import sys
import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import json
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QFile, QIODevice, Slot, QStringListModel, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QMovie
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QVBoxLayout, QPushButton, QApplication, QWidget, QLineEdit, QListView, QLabel, \
    QRadioButton, QSpinBox, QComboBox
import folium
from PySide6.QtCore import Signal
import seaborn as sn
from qt_ui.mapControl import FoliumDisplay
from qt_ui.mapControlSimulation import FoliumSimulationDisplay
from qt_ui.mapOutputControl import FoliumOutputDisplay


class LoadingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        # self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        self.label_animation = QtWidgets.QLabel(self)

        self.movie = QMovie('qt_ui/Herbert_Kickl.gif')
        # self.movie = QMovie('Loading_2.gif')
        self.label_animation.setMovie(self.movie)
        self.movie.start()
        self.show()

    def startAnimation(self):
        self.movie.start()
        self.show()

    def stopAnimation(self):
        self.movie.stop()
        self.close()


class MainWindow(QWidget):

    @Slot(str)
    def edge_selected(self, edge_id):
        name = self.id_names_dict.get(edge_id)
        self.window.streetNameLineEdit.setText("id: " + edge_id + " \nname: " + name)

    def on_close_road_button_click(self):
        res = re.split(' ', self.window.streetNameLineEdit.text())
        edge_id = res[1]
        edgeIDs = [e.getID() for e in self.net.getEdges()]
        list_edgeClosed = []
        for x in range(self.closed_street_model.rowCount()):
            r = re.split(' ', self.closed_street_model.item(x).text())
            list_edgeClosed.append(r[1])
        if edge_id in edgeIDs and edge_id not in list_edgeClosed:
            self.w.closed_edges.add(edge_id)
            self.w.redraw_folium_map()
            self.w_output.closed_edges.add(edge_id)
            self.w_output.redraw_folium_map()
            name = self.id_names_dict.get(edge_id)
            self.closed_street_model.appendRow(QStandardItem("id: " + edge_id + " \nname: " + name))
        pass

    def on_open_road_button_click(self):
        edge_id = None
        for index in self.window.closedStreetListView.selectedIndexes():
            item = self.window.closedStreetListView.model().itemFromIndex(index)
            res = re.split(' ', item.text())
            edge_id = res[1]
            self.closed_street_model.takeRow(item.row())
            break
        if edge_id is not None:
            self.w.closed_edges.remove(edge_id)
            self.w.redraw_folium_map()

            self.w_output.closed_edges.remove(edge_id)
            self.w_output.redraw_folium_map()

        else:
            res = re.split(' ', self.window.streetNameLineEdit.text())
            edge_id = res[1]
            if edge_id is not None and edge_id in self.w.closed_edges:
                model = self.window.closedStreetListView.model()
                for index in range(model.rowCount()):
                    item = model.item(index)
                    r = re.split(' ', item.text())
                    edge = r[1]
                    if edge == edge_id:
                        item.row()
                        self.closed_street_model.takeRow(item.row())
                        break

                self.w.closed_edges.remove(edge_id)
                self.w.redraw_folium_map()

                self.w_output.closed_edges.remove(edge_id)
                self.w_output.redraw_folium_map()

        self.window.closedStreetListView.clearSelection()
        print(self.w.closed_edges)
        pass

    def set_interval_list(self):
        self.traffic_level = '36'
        self.traffic_level_str = "Low"
        if self.window.radioButton_medium_traffic.isChecked() == True:
            self.traffic_level = '150'
            self.traffic_level_str = "Medium"
        if self.window.radioButton_heavy_traffic.isChecked() == True:
            self.traffic_level = '400'
            self.traffic_level_str = "Heavy"

        self.time_hours = self.window.spinBox_hours.text()
        self.time_minutes = self.window.spinBox_minutes.text()
        self.time_seconds = self.window.spinBox_seconds.text()

        time_total = (int(self.time_hours) * 3600) + (int(self.time_minutes) * 60) + int(self.time_seconds)

        self.intervals = self.window.spinBox_intervals.text()
        interval = int(self.intervals)
        # traffic_level = traffic_level
        if time_total < interval:
            return
        values = round(time_total / interval)
        #
        items = []
        for numbers in range(interval):
            items.append(numbers * values)
        items.append(time_total)
        self.time_total = str(time_total)

        self.interval_list = items
        self.search_and_replace()
        self.generating_random_trips()

    def search_and_replace(self):
        os.system("copy Sumo\osm.original.sumocfg Sumo\osm.sumocfg")
        with open("Sumo\osm.sumocfg", 'r') as file:
            file_contents = file.read()

            updated_contents = file_contents.replace("end_time", self.time_total)

        with open("Sumo\osm.sumocfg", 'w') as file:
            file.write(updated_contents)

    def generating_random_trips(self):
        os.system(
            "python \"" + self.path_sumo_tools + "\\randomTrips.py\" -n Sumo\osm.net.xml.gz --fringe-factor 5 --insertion-density " + self.traffic_level + " -o Sumo\osm.passenger.trips.xml -r Sumo\osm.passenger.rou.xml -b 0 -e " + self.time_total + " --trip-attributes \"departLane=\\\"best\\\"\" --fringe-start-attributes \"departSpeed=\\\"max\\\"\" --validate --remove-loops --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class passenger --vclass passenger --prefix veh --min-distance 300 --min-distance.fringe 10 --allow-fringe.min-length 1000 --lanes")

    def write_open_conf_files(self):
        list_edgeClosed = [self.closed_street_model.item(x).text() for x in range(self.closed_street_model.rowCount())]
        string_list_edgeClosed = ','.join(list_edgeClosed)
        os.system("copy Sumo\osm.poly.original.xml Sumo\osm.poly.xml")
        f = open("Sumo\osm.poly.xml", "a")
        for i in range(len(self.interval_list) - 1):
            f.write("    <edgeData id=\"" + str(self.interval_list[i]) + "_to_" + str(self.interval_list[
                                                                                          i + 1]) + "\" file=\"outputs\\" + self.traffic_level_str + "_" + self.time_hours + "h_" + self.time_minutes + "m_" + self.time_seconds + "s_" + self.intervals + "_closing[" + string_list_edgeClosed + "]_O.out.xml\" begin=\"" + str(
                self.interval_list[i]) + "\" end=\"" + str(self.interval_list[i + 1]) + "\" excludeEmpty=\"True\"/>\n")
        f.write("</additional>")
        f.close()

    def write_close_conf_files(self):
        list_edgeClosed = [self.closed_street_model.item(x).text() for x in range(self.closed_street_model.rowCount())]
        string_list_edgeClosed = ','.join(list_edgeClosed)
        os.system("copy Sumo\osm.poly.original.xml Sumo\osm.poly.xml")
        f = open("Sumo\osm.poly.xml", "a")
        for i in range(len(self.interval_list) - 1):
            f.write("    <edgeData id=\"" + str(self.interval_list[i]) + "_to_" + str(self.interval_list[
                                                                                          i + 1]) + "\" file=\"outputs\\" + self.traffic_level_str + "_" + self.time_hours + "h_" + self.time_minutes + "m_" + self.time_seconds + "s_" + self.intervals + "_closing[" + string_list_edgeClosed + "]_R.out.xml\" begin=\"" + str(
                self.interval_list[i]) + "\" end=\"" + str(self.interval_list[i + 1]) + "\" excludeEmpty=\"True\"/>\n")
        f.write("    <!-- Rerouting -->\n")
        if len(list_edgeClosed) > 0:
            print("write_close_conf_files")
            print(list_edgeClosed)
            for edgeclose in list_edgeClosed:
                nextEdges_incoming = self.net.getEdge(edgeclose).getIncoming()
                # print(nextEdges_incoming)
                text = ""
                for dev_edge in nextEdges_incoming:
                    text = text + dev_edge.getID() + " "
                text = text[:-1]
                f.write("    <rerouter id=\"close_" + edgeclose + "\" edges=\"" + text + "\">\n")
                f.write("        <interval begin=\"0\" end=\"" + self.time_total + "\">\n")
                f.write("            <closingReroute id=\"" + edgeclose + "\" disallow=\"all\"/>\n")
                f.write("        </interval>\n")
                f.write("    </rerouter>\n")
        f.write("</additional>")
        f.close()

    def list_load_results(self):
        thisdir = os.getcwd()
        self.load_results_model.clear()
        # r=root, d=directories, f = files
        for r, d, f in os.walk(thisdir):
            for file in sorted(f):
                if file.endswith("_R.out.xml"):
                    elist = []
                    for element in file.split("_"):
                        elist.append(element)
                    file = elist[0] + "_traffic--" + elist[1] + ":" + elist[2] + ":" + elist[3] + "--" + elist[
                        4] + "intv--" + elist[5]
                    self.load_results_model.appendRow(QStandardItem(file))

    def load_results(self):
        for index in self.window.listView_load_results.selectedIndexes():
            item = self.window.listView_load_results.model().itemFromIndex(index)
            self.managed_result_model.clear()
            self.managed_result_model.appendRow(QStandardItem(item.text()))
            res = re.split('_traffic--|h:|m:|s--|intv--', item.text())
            self.convert_xml_to_csv(res[0], res[1], res[2], res[3], res[4], res[5])
            self.enable_outputs_intervals(res[1], res[2], res[3], res[4])

    def convert_xml_to_csv(self, traffic, h, m, s, i, closing):
        list_edgeClosed = [self.closed_street_model.item(x).text() for x in range(self.closed_street_model.rowCount())]
        string_list_edgeClosed = ','.join(list_edgeClosed)
        Ofile = ("Sumo\outputs\\" + traffic + "_" + h + "h_" + m + "m_" + s + "s_" + i + "_" + closing + "_O.out.xml")
        Rfile = ("Sumo\outputs\\" + traffic + "_" + h + "h_" + m + "m_" + s + "s_" + i + "_" + closing + "_R.out.xml")
        if os.path.exists(Ofile):
            os.system("python \"" + self.path_sumo_tools + "\\xml\\xml2csv.py\" " + Ofile)
        if os.path.exists(Rfile):
            os.system("python \"" + self.path_sumo_tools + "\\xml\\xml2csv.py\" " + Rfile)

        self.traffic = traffic
        self.h = h
        self.m = m
        self.s = s
        self.i = i
        self.closing = closing
    def generate_interval_list(self, h, m, s, i):
        time_total = (int(h) * 3600) + (int(m) * 60) + int(s)
        values = round(time_total / int(i))
        items = []
        for numbers in range(int(i)):
            items.append(numbers * values)
        items.append(time_total)
        return items

    def enable_outputs_intervals(self, h, m, s, i):
        self.window.comboBox_results_traffic_indicator.setDisabled(False)
        self.window.comboBox_results_traffic_indicator.clear()
        self.window.comboBox_results_traffic_indicator.addItem('edge_traveltime')
        self.window.comboBox_results_traffic_indicator.addItem('edge_density')

        self.window.comboBox_results_time_interval.setDisabled(False)
        self.window.comboBox_results_time_interval.clear()
        self.window.comboBox_results_time_interval.addItem('All')
        interval_list = self.generate_interval_list(h, m, s, i)
        for i in range(len(interval_list) - 1):
            self.window.comboBox_results_time_interval.addItem(
                str(interval_list[i]) + "_to_" + str(interval_list[i + 1]))

        self.window.comboBox_results_road_selector.setDisabled(False)
        self.window.comboBox_results_road_selector.clear()
        self.window.comboBox_results_road_selector.addItem('All')
        edgeIDs = [e.getID() for e in self.net.getEdges()]
        for edge in edgeIDs:
            self.window.comboBox_results_road_selector.addItem(edge)

        self.window.comboBox_results_figures.setDisabled(False)
        self.window.comboBox_results_figures.clear()
        self.window.comboBox_results_figures.addItem('histogram')
        self.window.comboBox_results_figures.addItem('histplot')

        self.window.generate_outputs_button.setDisabled(False)


    def generate_outputs(self):
        item = self.window.comboBox_results_traffic_indicator.itemText(
            self.window.comboBox_results_traffic_indicator.currentIndex())
        plot_type = self.window.comboBox_results_figures.itemText(self.window.comboBox_results_figures.currentIndex())
        interval = self.window.comboBox_results_time_interval.itemText(
            self.window.comboBox_results_time_interval.currentIndex())
        edgedata_csv_file_O = "Sumo\outputs\\" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i + "_" + self.closing + "_O.out.csv"
        edgedata_csv_file_R = "Sumo\outputs\\" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i + "_" + self.closing + "_R.out.csv"
        if os.path.exists(edgedata_csv_file_O) and os.path.exists(edgedata_csv_file_R):
            dO = pd.read_csv(edgedata_csv_file_O, sep=";")
            dR = pd.read_csv(edgedata_csv_file_R, sep=";")
        dfO = self.detectors_out_to_table(dO, item)
        dfR = self.detectors_out_to_table(dR, item)
        if interval == 'All' and plot_type == 'histogram':
            self.plots_histogram(dO, dfO, dfR, item)
        elif interval != 'All' and plot_type == 'histogram':
            self.plots_one_histogram(dfO, dfR, item, interval)
        elif interval == 'All' and plot_type == 'histplot':
            self.plots_histplot(dO, dfO, item)
        elif interval != 'All' and plot_type == 'histplot':
            self.plots_one_histplot(dfO, item, interval)

        self.w_output_with.redraw_folium_map()
        self.w_output_without.redraw_folium_map()

    def detectors_out_to_table(self, sim_data_df, field_name):
        # parse all the intervals in the edgedata file
        time_intervals = sim_data_df['interval_id'].unique()
        data_dict = {}
        for time_interval in time_intervals:
            # get the DF related to time_interval
            data_interval = sim_data_df.loc[sim_data_df['interval_id'] == time_interval]
            # print(data_interval)
            # get the IDs of the edges that has an edgedata output value in the current time interval
            list_edges = data_interval['edge_id'].unique()
            for edge_id in list_edges:
                # get the data for all the edges
                data = data_interval.loc[data_interval['edge_id'] == edge_id][field_name]
                if time_interval not in data_dict:
                    data_dict[time_interval] = {}
                data_dict[time_interval][edge_id] = data.item()
        return pd.DataFrame.from_dict(data_dict)

    def plots_histogram(self, dO, dfO, dfR, arg):
        time_intervals = dO['interval_id'].unique()
        idx = 1
        num = len(time_intervals)
        fig, ax = plt.subplots(figsize=(10, 20), nrows=2, ncols=1, sharex=True, sharey=True)
        for name in time_intervals:
            plt.subplot(num, 1, idx)
            ax = plt.hist([dfO[name], dfR[name]], bins=10, label=['open', 'rerouting'])
            plt.title(name)
            plt.xlabel("Values")
            plt.ylabel("Frequency")
            plt.legend(loc='upper right')
            plt.margins(x=0.02, tight=True)
            ax = plt.gca()
            idx += 1
        plt.suptitle('Comparing timeframes in term of ' + arg + ', closing and nonclosing edges', fontsize=16, y=1)
        plt.tight_layout()
        fig.savefig('Sumo\outputs\plots\histogram_' + arg + "_" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i +'.pdf', bbox_inches='tight')
        fig.savefig('Sumo\outputs\plots\histogram_' + arg + "_" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i +'.png', bbox_inches='tight')
        self.generate_png_outputs(arg)


    def plots_one_histogram(self, dfO, dfR, arg, interval):
        # intervals = [str(interval)]
        fig, ax = plt.subplots(figsize=(10, 20), nrows=2, ncols=1, sharex=True, sharey=True)
        plt.subplot(1, 1, 1)
        ax = plt.hist([dfO[interval], dfR[interval]], bins=10, label=['open', 'rerouting'])
        plt.title(interval)
        plt.xlabel("Values")
        plt.ylabel("Frequency")
        plt.legend(loc='upper right')
        plt.margins(x=0.02, tight=True)
        ax = plt.gca()
        plt.suptitle('Comparing Timeframe ' + interval + ' in term of ' + arg + ', closing and nonclosing edges',
                     fontsize=16, y=1)
        plt.tight_layout()
        fig.savefig('Sumo\outputs\plots\histogram_' + arg + "_" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i +'.pdf', bbox_inches='tight')
        fig.savefig('Sumo\outputs\plots\histogram_' + arg + "_" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i +'.png', bbox_inches='tight')
        self.generate_png_outputs(arg)

    def plots_histplot(self, dO, dfO, arg):
        time_intervals = dO['interval_id'].unique()
        idx = 1
        num = len(time_intervals)
        dim = int(round(num / 2))
        fig, ax = plt.subplots(figsize=(10, 10))
        for name in time_intervals:
            plt.subplot(2, dim, idx)
            ax = sn.histplot(dfO[name], kde=True, kde_kws={'bw_adjust': 0.5})
            ax.set(xlabel='seconds')
            ax.set_title(name)
            idx += 1
        plt.subplots_adjust(top=0.9)
        plt.suptitle(arg + ' per time frame (seconds)', fontsize=16)
        plt.tight_layout()
        # plt.show()
        plt.subplots_adjust(wspace=0.26)
        fig.savefig('Sumo\outputs\plots\histplot_' + arg + "_" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i +'.pdf', bbox_inches='tight')
        fig.savefig('Sumo\outputs\plots\histplot_' + arg + "_" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i +'.png', bbox_inches='tight')
        self.generate_png_outputs(arg)

    def plots_one_histplot(self, dfO, arg, interval):
        fig, ax = plt.subplots(figsize=(10, 20))
        plt.subplot(1, 1, 1)
        ax = sn.histplot(dfO[interval], kde=True, kde_kws={'bw_adjust': 0.5})
        ax.set(xlabel='seconds')
        ax.set_title(interval)
        plt.subplots_adjust(top=0.9)
        plt.suptitle(arg + ' per time frame (' + interval + 'seconds)', fontsize=16)
        plt.tight_layout()
        # plt.show()
        plt.subplots_adjust(wspace=0.26)
        fig.savefig('Sumo\outputs\plots\histplot_' + arg + "_" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i +'.pdf', bbox_inches='tight')
        fig.savefig('Sumo\outputs\plots\histplot_' + arg + "_" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i +'.png', bbox_inches='tight')
        self.generate_png_outputs(arg)


    def generate_png_outputs(self, arg):
        plot_type = self.window.comboBox_results_figures.itemText(self.window.comboBox_results_figures.currentIndex())
        filename = "Sumo\outputs\plots\\" + plot_type + "_" + arg + "_" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i + ".png"
        if not filename:
            print("please select the .png file")
            sys.exit(0)
        else:
            self.window.label_plot.setPixmap(QtGui.QPixmap(filename))
            self.window.export_pdf_button.setDisabled(False)

    def export_pdf(self, event):
        traffic_indicator = self.window.comboBox_results_traffic_indicator.itemText(
            self.window.comboBox_results_traffic_indicator.currentIndex())
        plot_type = self.window.comboBox_results_figures.itemText(self.window.comboBox_results_figures.currentIndex())
        filename = plot_type + "_" + traffic_indicator + "_" + self.traffic + "_" + self.h + "h_" + self.m + "m_" + self.s + "s_" + self.i + ".pdf"
        if os.path.exists("Sumo\outputs\plots\\" + filename):
            cmd = "python viewer_pdf.py " + filename
            os.system(cmd)
        else:
            print("file not found")
            sys.exit(0)

    def read_json(self):
        self.id_names_dict = {}
        with open("qt_ui/bxl_Tulipe.geojson") as f:
            data = json.load(f)
        for feature in data['features']:
            self.id_names_dict.update({feature['properties'].get("id"): feature['properties'].get("name")})
        #print(self.id_names_dict.get("-1106583870"))

    def Animation(self):
        # self.window.Button_run_simulation.
        self.loading_screen = LoadingScreen()
        QtCore.QTimer.singleShot(100, lambda: self.run_simulation())

    def execute_sumo(self, args):
        subprocess.run(["sumo", '-c', 'Sumo\osm.sumocfg'])
        if args == 1:
            self.loading_screen.stopAnimation()

    def run_simulation(self):
        self.set_interval_list()

        self.write_open_conf_files()
        self.execute_sumo(0)
        print('Sumo Open finished')

        self.write_close_conf_files()
        self.execute_sumo(1)
        print('Sumo Close finished')

        self.list_load_results()
        # self.convert_xml_to_csv()

    def __init__(self):
        super(MainWindow, self).__init__()
        self.closing = None
        self.i = None
        self.s = None
        self.m = None
        self.h = None
        self.traffic = None
        self.interval_list = None
        self.intervals = None
        self.time_hours = None
        self.time_minutes = None
        self.time_seconds = None
        self.traffic_level_str = None
        self.time_total = None
        self.ui_file_name = "formTulipe.ui"
        self.ui_file = QFile(self.ui_file_name)
        if not self.ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {self.ui_file_name}: {self.ui_file.errorString()}")
            sys.exit(-1)
        self.loader = QUiLoader()
        self.window = self.loader.load(self.ui_file)
        self.ui_file.close()
        self.path_sumo_tools = os.environ["SUMO_TOOL"]
        if not self.window:
            print(self.loader.errorString())
            sys.exit(-1)
        self.read_json()

        self.window.openStreetButton = self.window.findChild(QPushButton, 'openStreetButton')
        self.window.openStreetButton.clicked.connect(self.on_open_road_button_click)
        self.window.closeStreetButton = self.window.findChild(QPushButton, 'closeStreetButton')
        self.window.closeStreetButton.clicked.connect(self.on_close_road_button_click)
        self.window.streetNameLineEdit = self.window.findChild(QLabel, 'label_selected_road_from_map')
        self.window.closedStreetListView = self.window.findChild(QListView, 'closedStreetListView')
        self.closed_street_model = QStandardItemModel()
        self.window.closedStreetListView.setModel(self.closed_street_model)
        self.window.label_mlg = self.window.findChild(QLabel, 'label_mlg')
        self.window.label_mlg.setPixmap(QtGui.QPixmap("mlg.png"))
        self.window.label_ulb = self.window.findChild(QLabel, 'label_ulb')
        self.window.label_ulb.setPixmap(QtGui.QPixmap("ulb.png"))


        #Maps
        self.window.mapLayout = self.window.findChild(QVBoxLayout, 'mapLayout')
        self.window.resultMapLayout = self.window.findChild(QVBoxLayout, 'mapLayout_2')
        self.window.mapLayout_output_with = self.window.findChild(QVBoxLayout, 'mapLayout_output_with')
        self.window.mapLayout_output_without = self.window.findChild(QVBoxLayout, 'mapLayout_output_without')

        self.w = FoliumDisplay(geojson_path="qt_ui/bxl_Tulipe.geojson")
        self.w.on_edge_selected.connect(self.edge_selected)
        self.w_output = FoliumSimulationDisplay(geojson_path="qt_ui/bxl_Tulipe.geojson")
        self.w_output_with = FoliumOutputDisplay(geojson_path="qt_ui/geoDF.geojson")
        self.w_output_without = FoliumOutputDisplay(geojson_path="qt_ui/geoDF.geojson")

        self.window.mapLayout.addWidget(self.w)
        self.window.resultMapLayout.addWidget(self.w_output)
        self.window.mapLayout_output_with.addWidget(self.w_output_with)
        self.window.mapLayout_output_without.addWidget(self.w_output_without)

        # Load Network
        self.net = self.w.net_handler.get_net()


        # Traffic Simulation
        self.window.spinBox_hours = self.window.findChild(QSpinBox, 'spinBox_simulation_hours')
        self.window.spinBox_minutes = self.window.findChild(QSpinBox, 'spinBox_simulation_minutes')
        self.window.spinBox_seconds = self.window.findChild(QSpinBox, 'spinBox_simulation_seconds')
        self.window.spinBox_intervals = self.window.findChild(QSpinBox, 'spinBox_simulation_interval')
        self.window.radioButton_medium_traffic = self.window.findChild(QRadioButton, 'radioButton_medium_traffic')
        self.window.radioButton_heavy_traffic = self.window.findChild(QRadioButton, "radioButton_heavy_traffic")
        self.window.run_simulation_button = self.window.findChild(QPushButton, 'run_simulation_button')
        self.window.run_simulation_button.clicked.connect(self.Animation)


        # Results
        self.window.listView_load_results = self.window.findChild(QListView, 'listView_load_results')
        self.load_results_model = QStandardItemModel()
        self.window.listView_load_results.setModel(self.load_results_model)
        self.window.listView_load_results.selectionModel().selectionChanged.connect(self.load_results)
        #self.window.load_results_button = self.window.findChild(QPushButton, 'load_results_button')
        #self.window.load_results_button.clicked.connect(self.load_results)

        self.window.comboBox_results_time_interval = self.window.findChild(QComboBox, 'comboBox_results_time_interval')
        self.window.comboBox_results_traffic_indicator = self.window.findChild(QComboBox,
                                                                               'comboBox_results_traffic_indicator')
        self.window.comboBox_results_road_selector = self.window.findChild(QComboBox, 'comboBox_results_road_selector')
        self.window.comboBox_results_figures = self.window.findChild(QComboBox, 'comboBox_results_figures')
        self.window.generate_outputs_button = self.window.findChild(QPushButton, 'generate_outputs_button')
        self.window.generate_outputs_button.clicked.connect(self.generate_outputs)
        self.window.export_pdf_button = self.window.findChild(QPushButton, 'export_pdf_button')
        self.window.export_pdf_button.clicked.connect(self.export_pdf)
        self.window.label_plot = self.window.findChild(QLabel, 'label_plot')
        self.window.label_name_currently_managed_result = self.window.findChild(QLabel, 'label_name_currently_managed_result')
        self.window.listview_currently_managed_result = self.window.findChild(QListView, 'listview_name_currently_managed_result')
        self.managed_result_model = QStandardItemModel()
        self.window.listview_currently_managed_result.setModel(self.managed_result_model)

        self.list_load_results()

    def handle_clicked(self):
        for index in self.window.listView_load_results.selectedIndexes():
            item = self.window.listView_load_results.model().itemFromIndex(index)
            self.managed_result_model.clear()
            self.managed_result_model.appendRow(QStandardItem(item.text()))

        # Importing net

    def show(self):
        self.window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
