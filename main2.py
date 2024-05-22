import os
import sys
import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import json
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QFile, QIODevice, Slot, QStringListModel, Qt, QProcess, QObject, QRunnable, QThreadPool
from PySide6.QtGui import QStandardItemModel, QStandardItem, QMovie
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QVBoxLayout, QPushButton, QApplication, QWidget, QLineEdit, QListView, QLabel, \
    QRadioButton, QSpinBox, QComboBox
import folium
from PySide6.QtCore import Signal
import seaborn as sns
from qt_ui.mapControl import FoliumDisplay
from qt_ui.mapControl2 import FoliumDisplay2
from qt_ui.mapControlSimulation import FoliumSimulationDisplay
from qt_ui.mapOutputControl import FoliumOutputDisplay
from datetime import datetime


class LoadingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)
        # self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        self.label_animation = QtWidgets.QLabel(self)

        self.movie = QMovie(os.path.join(os.getcwd(), "qt_ui", "Herbert_Kickl.gif"))
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
        self.window.label_selected_road_from_map.setText("id: " + edge_id + " \n" + name)

    def edge_selected_results(self, edge_id):
        name = self.id_names_dict.get(edge_id)
        self.window.selected_street_label.clear()
        self.window.selected_street_label.setText("id: " + edge_id + " \n" + name)

        #Results by vehicles
        self.window.comboBox_results_veh_traffic_indicator.setDisabled(False)
        self.window.comboBox_results_veh_traffic_indicator.clear()
        self.window.comboBox_results_veh_traffic_indicator.addItem('tripinfo_duration')
        self.window.comboBox_results_veh_traffic_indicator.addItem('tripinfo_routeLength')
        #self.window.comboBox_results_veh_traffic_indicator.addItem('tripinfo_speedFactor')
        self.window.comboBox_results_veh_traffic_indicator.addItem('tripinfo_timeLoss')
        self.window.comboBox_results_veh_traffic_indicator.addItem('tripinfo_waitingTime')
        self.window.generate_vehicles_button.setDisabled(False)

        self.window.comboBox_results_veh_figure.setDisabled(False)
        self.window.comboBox_results_veh_figure.clear()
        self.window.comboBox_results_veh_figure.addItem('scatter plot')
        self.window.comboBox_results_veh_figure.addItem('histogram plot')

        #Results by Street
        self.window.comboBox_results_by_street_traffic_indicator.setDisabled(False)
        self.window.comboBox_results_by_street_traffic_indicator.clear()
        self.window.comboBox_results_by_street_traffic_indicator.addItem('edge_timeLoss')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('edge_traveltime')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('edge_occupancy')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('edge_density')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('edge_waitingTime')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('edge_speed')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('edge_speedRelative')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('edge_sampledSeconds')
        self.window.generate_street_outputs_button.setDisabled(False)

        for index in self.window.listView_load_results.selectedIndexes():
            item = self.window.listView_load_results.model().itemFromIndex(index)
            loaded_exp_id = item.text()

        Ofile_Veh = os.path.join(os.getcwd(), "Sumo", "outputs", loaded_exp_id + "_O.veh.xml")
        Rfile_Veh = os.path.join(os.getcwd(), "Sumo", "outputs", loaded_exp_id + "_R.veh.xml")
        if os.path.exists(Ofile_Veh):
            os.system("python \"" + os.path.join(os.environ["SUMO_TOOL"], "xml", "xml2csv.py\" ") + Ofile_Veh + " -o " + os.path.join(os.getcwd(), "Sumo", "outputs", "Ofile.veh.csv"))
        if os.path.exists(Rfile_Veh):
            os.system("python \"" + os.path.join(os.environ["SUMO_TOOL"], "xml", "xml2csv.py\" ") + Rfile_Veh + " -o " + os.path.join(os.getcwd(), "Sumo", "outputs", "Rfile.veh.csv"))

        nextEdges_incoming = self.net.getEdge(edge_id).getIncoming()
        print(nextEdges_incoming)

    def listview_closed_road_result(self):
        for index in self.window.listview_closed_road_result.selectedIndexes():
            item = self.window.listview_closed_road_result.model().itemFromIndex(index)
            self.window.selected_street_label.clear()
            #self.window.selected_street_label.setText(item.text())

    def listView_simulation(self):
        self.window.spinBox_beginning_hours.setDisabled(False)
        self.window.spinBox_beginning_minutes.setDisabled(False)
        self.window.spinBox_beginning_seconds.setDisabled(False)

        self.window.spinBox_end_hours.setDisabled(False)
        self.window.spinBox_end_minutes.setDisabled(False)
        self.window.spinBox_end_seconds.setDisabled(False)

        for index in self.window.listView_simulation.selectedIndexes():
            item = self.window.listView_simulation.model().itemFromIndex(index)
            #print(item.text())
            res = re.split('from: |to: |h:|m:|s', item.text())
            s_end = res[-2]
            m_end = res[-3]
            h_end = res[-4]
            s_beg = res[-6]
            m_beg = res[-7]
            h_beg = res[-8]

        h = self.window.spinBox_hours.text()
        m = self.window.spinBox_minutes.text()
        s = self.window.spinBox_seconds.text()
        #     hour = h + 'h: ' + m + 'm:' + s + 's'
        #     self.window.label_simulation_duration.setText(hour)
        #
        # self.window.spinBox_beginning_hours.setRange(0, int(h))
        # self.window.spinBox_end_hours.setRange(0, int(h))
        self.window.spinBox_beginning_hours.setValue(int(h_beg))
        self.window.spinBox_end_hours.setValue(int(h_end))
        #
        self.window.spinBox_beginning_minutes.setRange(0, 59)
        self.window.spinBox_end_minutes.setRange(0, 59)
        self.window.spinBox_beginning_minutes.setValue(int(m_beg))
        self.window.spinBox_end_minutes.setValue(int(m_end))

        self.window.spinBox_beginning_seconds.setRange(0, 59)
        self.window.spinBox_end_seconds.setRange(0, 59)
        self.window.spinBox_beginning_seconds.setValue(int(s_beg))
        self.window.spinBox_end_seconds.setValue(int(s_end))


    def on_close_road_button_click(self):
        res = re.split(' ', self.window.label_selected_road_from_map.text())
        edge_id = res[1]
        edgeIDs = [e.getID() for e in self.net.getEdges()]
        list_edgeClosed = []
        for x in range(self.closed_street_model.rowCount()):
            r = re.split(' ', self.closed_street_model.item(x).text())
            list_edgeClosed.append(r[1])
        if edge_id in edgeIDs and edge_id not in list_edgeClosed:
            self.w.closed_edges.add(edge_id)
            self.w.redraw_folium_map()
            self.w_simulation.closed_edges.add(edge_id)
            self.w_simulation.redraw_folium_map()
            name = self.id_names_dict.get(edge_id)
            # h_b = self.window.spinBox_beginning_hours.text()
            # m_b = self.window.spinBox_beginning_minutes.text()
            # s_b = self.window.spinBox_beginning_seconds.text()
            h = self.window.spinBox_simulation_hours.text()
            m = self.window.spinBox_simulation_minutes.text()
            s = self.window.spinBox_simulation_seconds.text()
            self.closed_street_model.appendRow(QStandardItem("id: " + edge_id + " - " + name))
            self.listView_simulation_model.appendRow(QStandardItem("id: " + edge_id + " - " + name + " \nClosing from: 0h:0m:0s - to: " + h + "h:" +m+ "m:" +s+ "s"))
            self.listView_current_simulation_model.appendRow(QStandardItem("id: " + edge_id + " - " + name + " \nClosing from: 0h:0m:0s - to: " + h + "h:" +m+ "m:" +s+ "s"))
        pass

    def on_open_road_button_click(self):
        res = None
        #Deleting from closedStreetListView
        for index in self.window.closedStreetListView.selectedIndexes():
            item = self.window.closedStreetListView.model().itemFromIndex(index)
            res = re.split(' ', item.text())
        if res is not None:
            edge_id = res[1]
            self.closed_street_model.takeRow(item.row())
            # self.listView_simulation_model.takeRow(item.row())
            #break

            model_simulation = self.window.listView_simulation.model()
            for index in range(model_simulation.rowCount()):
                item = model_simulation.item(index)
                r = re.split(' ', item.text())
                edge = r[1]
                if edge == edge_id:
                    #item.row()
                    self.listView_simulation_model.takeRow(item.row())
                    break

            model_current = self.window.listView_current_simulation.model()
            for index in range(model_current.rowCount()):
                item = model_current.item(index)
                r = re.split(' ', item.text())
                edge = r[1]
                if edge == edge_id:
                    #item.row()
                    self.listView_current_simulation_model.takeRow(item.row())
                    break

            self.w.closed_edges.remove(edge_id)
            self.w.redraw_folium_map()

            self.w_simulation.closed_edges.remove(edge_id)
            self.w_simulation.redraw_folium_map()

        else:
            # Deleting from the map
            res = re.split(' ', self.window.label_selected_road_from_map.text())
            edge_id = res[1]
            if edge_id is not None and edge_id in self.w.closed_edges:
                model = self.window.closedStreetListView.model()
                for index in range(model.rowCount()):
                    item = model.item(index)
                    r = re.split(' ', item.text())
                    edge = r[1]
                    if edge == edge_id:
                        #item.row()
                        self.closed_street_model.takeRow(item.row())
                        # self.listView_simulation_model.takeRow(item.row())
                        # self.listView_current_simulation_model.takeRow(item.row())
                        break

                model_simulation = self.window.listView_simulation.model()
                for index in range(model_simulation.rowCount()):
                    item = model_simulation.item(index)
                    r = re.split(' ', item.text())
                    edge = r[1]
                    if edge == edge_id:
                        #item.row()
                        self.listView_simulation_model.takeRow(item.row())
                        break

                model_current = self.window.listView_current_simulation.model()
                for index in range(model_current.rowCount()):
                    item = model_current.item(index)
                    r = re.split(' ', item.text())
                    edge = r[1]
                    if edge == edge_id:
                        #item.row()
                        self.listView_current_simulation_model.takeRow(item.row())
                        break

                self.w.closed_edges.remove(edge_id)
                self.w.redraw_folium_map()

                self.w_simulation.closed_edges.remove(edge_id)
                self.w_simulation.redraw_folium_map()

        self.window.closedStreetListView.clearSelection()
        #print(self.w.closed_edges)
        pass

    def set_interval_list(self):
        self.traffic_level = '500'
        self.traffic_level_str = "Low"
        if self.window.radioButton_medium_traffic.isChecked() == True:
            self.traffic_level = '2000'
            self.traffic_level_str = "Medium"
        if self.window.radioButton_heavy_traffic.isChecked() == True:
            self.traffic_level = '7000'
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
        #self.search_and_replace()
        self.generating_random_trips()

    # def search_and_replace(self):
    #     os.system("copy Sumo\osm.original.sumocfg Sumo\osm.sumocfg")
    #     with open("Sumo\osm.sumocfg", 'r') as file:
    #         file_contents = file.read()
    #
    #         updated_contents = file_contents.replace("end_time", self.time_total)
    #
    #     with open("Sumo\osm.sumocfg", 'w') as file:
    #         file.write(updated_contents)

    def generating_random_trips(self):
        #print(
        #    "python \"" + os.path.join(os.environ["SUMO_TOOL"], "randomTrips.py\"") + " -n " + os.path.join(os.getcwd(), "Sumo", "osm.net.xml.gz") + " --fringe-factor 30 --insertion-rate " + self.traffic_level + " -o " + os.path.join(os.getcwd(), "Sumo", "osm.passenger.trips.xml") + " -r " + os.path.join(os.getcwd(), "Sumo", "osm.passenger.rou.xml") + " -b 0 -e " + self.time_total + " --validate --remove-loops")
        os.system(
            "python \"" + os.path.join(os.environ["SUMO_TOOL"], "randomTrips.py\"") + " -n " + os.path.join(os.getcwd(), "Sumo", "osm.net.xml.gz") + " --fringe-factor 30 --insertion-rate " + self.traffic_level + " -o " + os.path.join(os.getcwd(), "Sumo", "osm.passenger.trips.xml") + " -r " + os.path.join(os.getcwd(), "Sumo", "osm.passenger.rou.xml") + " -b 0 -e " + self.time_total + " --validate --remove-loops") #--trip-attributes \"departLane=\\\"best\\\"\" --fringe-start-attributes \"departSpeed=\\\"max\\\"\" --via-edge-types highway.motorway,highway.motorway_link,highway.trunk_link,highway.primary_link,highway.secondary_link,highway.tertiary_link --vehicle-class passenger --vclass passenger --prefix veh --min-distance 300 --min-distance.fringe 10 --allow-fringe.min-length 1000 --lanes")
        # with open('Sumo\osm.passenger.trips.xml', "r") as file:
        #     data = file.readlines()
        #
        # num = len(self.w.closed_edges)
        # list(self.w.closed_edges)[0]
        # deleted_veh = []
        # with open('Sumo\osm.passenger.trips.xml', "w") as file:
        #     for line in data:
        #         write = True
        #         for i in range(num):
        #             if list(self.w.closed_edges)[i] in line:
        #                 veh = re.split(' ', line)
        #                 deleted_veh.append(veh[5])
        #                 write = False
        #         if write:
        #             file.write(line)
        # #print(deleted_veh)
        # #print(list(self.w.closed_edges)[0])
        # with open('Sumo\osm.passenger.rou.xml', "r") as file:
        #     data = file.readlines()
        # num = len(deleted_veh)
        # with open('Sumo\osm.passenger.rou.xml', 'w') as file:
        #     i = 0
        #     while i < len(data):
        #         write = True
        #         if 'vehicle id' not in data[i]: #and 'route edges' not in line and '/vehicle' not in line:
        #             file.write(data[i])
        #             i = i + 1
        #         else:
        #             for j in range(num):
        #                 if deleted_veh[j] in data[i]:
        #                     #print(deleted_veh[j])
        #                     write = False
        #                     break
        #             if write:
        #                 file.write(data[i])
        #                 i = i + 1
        #             else:
        #                 i = i + 3

    # def write_open_conf_files(self, exp_id, args):
    #     list_edgeClosed = []
    #     for x in range(self.closed_street_model.rowCount()):
    #         r = re.split(' ', self.closed_street_model.item(x).text())
    #         list_edgeClosed.append(r[1])
    #     string_list_edgeClosed = ','.join(list_edgeClosed)
    #     os.system("copy Sumo\osm.poly.original.xml Sumo\osm.poly.xml")
    #     #f = open("Sumo\osm.poly.xml", "a")
    #     f = open("Sumo\conf."+args+".xml", "w")
    #     f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    #     f.write("<additional xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://sumo.dlr.de/xsd/additional_file.xsd\">")
    #     f.write("    <edgeData id=\"0_to_" + str(
    #         self.interval_list[-1]) + "\" file=\"outputs\\" + exp_id + "_O.out.xml\" begin=\"0\" end=\"" + str(
    #         self.interval_list[-1]) + "\" excludeEmpty=\"True\"/>\n")
    #     for i in range(len(self.interval_list) - 1):
    #         f.write("    <edgeData id=\"" + str(self.interval_list[i]) + "_to_" + str(self.interval_list[
    #                                                                                       i + 1]) + "\" file=\"outputs\\" + exp_id + "_O.out.xml\" begin=\"" + str(
    #             self.interval_list[i]) + "\" end=\"" + str(self.interval_list[i + 1]) + "\" excludeEmpty=\"True\"/>\n")
    #     f.write("</additional>")
    #     f.close()

    def write_conf_files(self, exp_id, args):
        list_edgeClosed = []
        for x in range(self.closed_street_model.rowCount()):
            r = re.split(' ', self.closed_street_model.item(x).text())
            list_edgeClosed.append(r[1])
        string_list_edgeClosed = ','.join(list_edgeClosed)
        #os.system("copy Sumo\osm.poly.original.xml Sumo\osm.poly.xml")
        f = open(os.path.join(os.getcwd(), "Sumo", "conf."+args+".xml"), "w")
            #"Sumo\conf."+args+".xml", "w")
        #os.path.join(os.getcwd(), "Sumo", "conf."+args+".xml")
        f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        f.write("<additional xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://sumo.dlr.de/xsd/additional_file.xsd\">\n")
        f.write("    <edgeData id=\"0_to_" + str(
            self.interval_list[-1]) + "\" file=\"outputs\\" + exp_id + "_" + args + ".out.xml\" begin=\"0\" end=\"" + str(
            self.interval_list[-1]) + "\" excludeEmpty=\"True\"/>\n")
        for i in range(len(self.interval_list) - 1):
            f.write("    <edgeData id=\"" + str(self.interval_list[i]) + "_to_" + str(self.interval_list[
                                                                                          i + 1]) + "\" file=\"outputs\\" + exp_id + "_" + args + ".out.xml\" begin=\"" + str(
                self.interval_list[i]) + "\" end=\"" + str(self.interval_list[i + 1]) + "\" excludeEmpty=\"True\"/>\n")
        f.write("    <!-- Rerouting -->\n")
        if len(list_edgeClosed) > 0:
            for edgeclose in list_edgeClosed:

                nextEdges_incoming = self.net.getEdge(edgeclose).getIncoming()
                print(nextEdges_incoming)
                text = ""
                for dev_edge in nextEdges_incoming:
                    text = text + dev_edge.getID() + " "
                text = text[:-1]

                model = self.window.listView_current_simulation.model()
                for index in range(model.rowCount()):
                    item = model.item(index)
                    res = re.split(' |h:|m:|s', item.text())
                    #print(res)
                    if res[1] == edgeclose:
                        s_end = res[-2]
                        m_end = res[-3]
                        h_end = res[-4]
                        s_beg = res[-8]
                        m_beg = res[-9]
                        h_beg = res[-10]
                        break

                b_time = (int(h_beg) * 3600) + (int(m_beg) * 60) + int(s_beg)
                e_time = (int(h_end) * 3600) + (int(m_end) * 60) + int(s_end)
                # print(b_time)
                # print(e_time)

                f.write("    <rerouter id=\"close_" + edgeclose + "\" edges=\"" + text + "\">\n")
                if args == 'R':
                    f.write("        <interval begin=\""+str(b_time)+"\" end=\"" + str(e_time) + "\">\n")
                    f.write("            <closingReroute id=\"" + edgeclose + "\" disallow=\"all\"/>\n")
                    f.write("        </interval>\n")
                f.write("    </rerouter>\n")
        f.write("</additional>")
        f.close()

    def list_load_results(self):
        self.load_results_model.clear()
        for id in self.existing_exp_dic:
            self.load_results_model.appendRow(QStandardItem(id))


    def load_results(self):
        for index in self.window.listView_load_results.selectedIndexes():
            item = self.window.listView_load_results.model().itemFromIndex(index)
            loaded_exp_id = item.text()
            self.window.selected_simulation_label.clear()
            self.window.selected_simulation_label.setText("Selected simulation : "+loaded_exp_id)
            self.traffic = self.existing_exp_dic[item.text()].get('traffic')
            self.h = self.existing_exp_dic[item.text()].get('hours')
            self.m = self.existing_exp_dic[item.text()].get('minutes')
            self.s = self.existing_exp_dic[item.text()].get('seconds')
            self.i = self.existing_exp_dic[item.text()].get('intervals')
            self.closing = self.existing_exp_dic[item.text()].get('closed_roads')
            self.events = self.existing_exp_dic[item.text()].get('events')
            traffic_lev = str(self.traffic) + " traffic"
            duration = self.h + "h : " + str(self.m) + "m : " + str(self.s) + "s"
            self.window.traffic_level_output_label.setText(traffic_lev)
            self.window.intervals_output_label.setText(str(self.i))
            self.window.durationl_output_label.setText(duration)
            self.listview_closed_road_result_model.clear()
            self.window.selected_street_label.clear()
            for edge_id in self.closing:
                name = self.id_names_dict.get(edge_id)
                for times in self.events:
                    if times[0] ==edge_id:
                        self.listview_closed_road_result_model.appendRow(QStandardItem("id: " + edge_id + " \n" + name + "\nClosing from: "+ times[1]+"h:" +times[2]+"m:"+times[3]+"s - to: " + times[4] + "h:" + times[5] + "m:" + times[6] + "s)"))
                        break
            self.convert_xml_to_csv(loaded_exp_id)
            self.enable_outputs_intervals(self.h, self.m, self.s, self.i)
            self.generate_maps_outputs()

    def plot_vehicles(self):

        res = re.split(' ', self.window.selected_street_label.text())
        edge_id = res[1]
        veh = []
        with open(os.path.join(os.getcwd(), "Sumo", "osm.passenger.rou.xml"), 'r') as file:
            lines = file.readlines()
            for i in range(len(lines)):
                if edge_id in lines[i]:
                    r = re.split('\"', lines[i - 1])
                    veh.append(int(r[1]))
        traffic_indicator = self.window.comboBox_results_veh_traffic_indicator.itemText(
            self.window.comboBox_results_veh_traffic_indicator.currentIndex())

        edgedata_csv_file_O = os.path.join(os.getcwd(), "Sumo", "outputs", "Ofile.veh.csv")
        edgedata_csv_file_R = os.path.join(os.getcwd(), "Sumo", "outputs", "Rfile.veh.csv")
        if os.path.exists(edgedata_csv_file_O) and os.path.exists(edgedata_csv_file_R):
            dO = pd.read_csv(edgedata_csv_file_O, sep=";")
            dR = pd.read_csv(edgedata_csv_file_R, sep=";")

        #print(veh)
        dO = dO.loc[:,
                      ['tripinfo_id',
                       traffic_indicator]]

        dfO = dO[dO['tripinfo_id'].isin(veh)]

        dR = dR.loc[:,
                      ['tripinfo_id',
                       traffic_indicator]]

        dfR = dR.loc[dR['tripinfo_id'].isin(veh)]
        dfO = dfO.set_index('tripinfo_id')
        dfR = dfR.set_index('tripinfo_id')

        dfO_aligned, dfR_aligned = dfO.align(dfR, fill_value=0)

        value = 'Seconds'
        if traffic_indicator == 'tripinfo_routeLength':
            value = 'Meters'

        veh_figure = self.window.comboBox_results_veh_figure.itemText(
            self.window.comboBox_results_veh_figure.currentIndex())

        df = dfR_aligned - dfO_aligned
        if veh_figure == 'scatter plot':
            name = self.id_names_dict.get(edge_id)
            fig, ax = plt.subplots(figsize=(15, 10))
            #for name in time_intervals:
            sns.stripplot(data=df, orient="h")
            #plt.plot(df.index, df[name], linewidth=3.0)
            #ax.set(xlabel='Edges')
            ax.set_ylabel(traffic_indicator, fontsize=30)
            ax.set_xlabel(value, fontsize=30)
            plt.xticks(rotation=90)
            plt.tick_params(labelleft=False)
            ax.tick_params(axis='x', which="both", bottom=False, top=False, labelsize=24, rotation=90)
            #ax.tick_params(axis='y', labelsize=30, rotation=90)
            #plt.margins(x=0.002, tight=True)
            #leg = plt.legend(time_intervals, loc=7, bbox_to_anchor=(1.3, 0.5), fontsize=24)
            #leg = plt.legend(time_intervals, loc=7, fontsize=24)

            plt.subplots_adjust(top=0.9)
            plt.suptitle(traffic_indicator +' of the vehicles that originally passed through \n' + edge_id + ' - ' + name, fontsize=32)
            fig.subplots_adjust(wspace=0.26)


        elif veh_figure == 'histogram plot':
            fig, ax = plt.subplots(figsize=(17, 10))#, nrows=2, ncols=1, sharex=True, sharey=True)
            plt.subplot(1, 1, 1)
            ax = plt.hist([dO[traffic_indicator], dR[traffic_indicator]], bins=10, label=['open', 'rerouting'])
            #plt.title(traffic_indicator)
            plt.xlabel("Values", fontsize=24)
            plt.ylabel("Frequency", fontsize=24)
            plt.xticks(fontsize=18)
            plt.yticks(fontsize=18)

            plt.legend(loc='upper right', fontsize=22)
            #plt.margins(x=0.02, tight=True)
            #ax = plt.gca()
            plt.suptitle('Comparing vehicles in term of ' + traffic_indicator + ', closing and nonclosing edges', fontsize=26, y=1)

        plt.tight_layout()
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()

    def convert_xml_to_csv(self, loaded_exp_id):
        #print(loaded_exp_id)
        Ofile = (os.path.join(os.getcwd(), "Sumo", "outputs", loaded_exp_id + "_O.out.xml"))
        Rfile = (os.path.join(os.getcwd(), "Sumo", "outputs", loaded_exp_id + "_R.out.xml"))
        if os.path.exists(Ofile):
            os.system("python \"" + os.path.join(self.path_sumo_tools, "xml", "xml2csv.py\" ") + Ofile + " -o " + os.path.join(os.getcwd(), "Sumo", "outputs", "Ofile.out.csv"))
        if os.path.exists(Rfile):
            os.system("python \"" + os.path.join(self.path_sumo_tools, "xml", "xml2csv.py\" ") + Rfile + " -o " + os.path.join(os.getcwd(), "Sumo", "outputs", "Rfile.out.csv"))

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
        self.window.comboBox_results_traffic_indicator.addItem('edge_density')
        self.window.comboBox_results_traffic_indicator.addItem('edge_occupancy')
        self.window.comboBox_results_traffic_indicator.addItem('edge_timeLoss')
        self.window.comboBox_results_traffic_indicator.addItem('edge_traveltime')
        self.window.comboBox_results_traffic_indicator.addItem('edge_waitingTime')
        self.window.comboBox_results_traffic_indicator.addItem('edge_speed')
        self.window.comboBox_results_traffic_indicator.addItem('edge_speedRelative')
        self.window.comboBox_results_traffic_indicator.addItem('edge_sampledSeconds')

        self.window.comboBox_results_time_interval.setDisabled(False)
        self.window.comboBox_results_time_interval.clear()
        #self.window.comboBox_results_time_interval.addItem('All')
        interval_list = self.generate_interval_list(h, m, s, i)
        self.window.comboBox_results_time_interval.addItem("All")
        self.window.comboBox_results_time_interval.addItem("0_to_" + str(interval_list[-1]))
        for i in range(len(interval_list) - 1):
            self.window.comboBox_results_time_interval.addItem(
                str(interval_list[i]) + "_to_" + str(interval_list[i + 1]))

        self.window.comboBox_results_maps_time_interval.setDisabled(False)
        self.window.comboBox_results_maps_time_interval.clear()
        # self.window.comboBox_results_time_interval.addItem('All')
        #interval_list = self.generate_interval_list(h, m, s, i)
        self.window.comboBox_results_maps_time_interval.addItem("0_to_" + str(interval_list[-1]))
        for i in range(len(interval_list) - 1):
            self.window.comboBox_results_maps_time_interval.addItem(
                str(interval_list[i]) + "_to_" + str(interval_list[i + 1]))

        self.window.comboBox_results_maps_traffic_indicator.setDisabled(False)
        self.window.comboBox_results_maps_traffic_indicator.clear()
        self.window.comboBox_results_maps_traffic_indicator.addItem('edge_density')
        self.window.comboBox_results_maps_traffic_indicator.addItem('edge_occupancy')
        self.window.comboBox_results_maps_traffic_indicator.addItem('edge_timeLoss')
        self.window.comboBox_results_maps_traffic_indicator.addItem('edge_traveltime')
        self.window.comboBox_results_maps_traffic_indicator.addItem('edge_waitingTime')
        self.window.comboBox_results_maps_traffic_indicator.addItem('edge_speed')
        self.window.comboBox_results_maps_traffic_indicator.addItem('edge_speedRelative')
        self.window.comboBox_results_maps_traffic_indicator.addItem('edge_sampledSeconds')

        self.window.comboBox_results_figures.setDisabled(False)
        self.window.comboBox_results_figures.clear()
        self.window.comboBox_results_figures.addItem('histogram')
        self.window.comboBox_results_figures.addItem('histplot')
        self.window.comboBox_results_figures.addItem('plot')

        self.window.generate_integrate_outputs_button.setDisabled(False)
        self.window.generate_map_button.setDisabled(False)


    def generate_integrated_outputs(self):
        traffic_indicator = self.window.comboBox_results_traffic_indicator.itemText(
            self.window.comboBox_results_traffic_indicator.currentIndex())
        plot_type = self.window.comboBox_results_figures.itemText(self.window.comboBox_results_figures.currentIndex())
        interval = self.window.comboBox_results_time_interval.itemText(
            self.window.comboBox_results_time_interval.currentIndex())
        edgedata_csv_file_O = os.path.join(os.getcwd(), "Sumo", "outputs", "Ofile.out.csv")
        edgedata_csv_file_R = os.path.join(os.getcwd(), "Sumo", "outputs", "Rfile.out.csv")
        if os.path.exists(edgedata_csv_file_O) and os.path.exists(edgedata_csv_file_R):
            dO = pd.read_csv(edgedata_csv_file_O, sep=";")
            dR = pd.read_csv(edgedata_csv_file_R, sep=";")

            dfO = self.detectors_out_to_table(dO, traffic_indicator)
            dfR = self.detectors_out_to_table(dR, traffic_indicator)
            dfO = dfO.fillna(0)
            dfR = dfR.fillna(0)

            dfO_aligned, dfR_aligned = dfO.align(dfR, fill_value=0)

            # print(edgedata_csv_file_O)
            # print(edgedata_csv_file_R)
            # print(dO)
            # print(dR)
            # print()
            # print(dfO)
            # print(dfR)
            # print()
            # print(dfO_aligned)
            # print(dfR_aligned)
            # dfO.to_csv(os.path.join(os.getcwd(), "Sumo", "outputs", "dfO.csv"), sep=';')
            # dfR.to_csv(os.path.join(os.getcwd(), "Sumo", "outputs", "dfR.csv"), sep=';')

            if interval == 'All' and plot_type == 'histogram':
                self.plots_histogram(dO, dfO_aligned, dfR_aligned, traffic_indicator)
            elif interval != 'All' and plot_type == 'histogram':
                self.plots_one_histogram(dfO_aligned, dfR_aligned, traffic_indicator, interval)
            elif interval == 'All' and plot_type == 'histplot':
                self.plots_histplot(dO, dfO_aligned, traffic_indicator)
            elif interval != 'All' and plot_type == 'histplot':
                self.plots_one_histplot(dfO_aligned, traffic_indicator, interval)
            elif plot_type == 'plot': #interval == 'All' and
                self.generate_group_outputs(dfO_aligned, dfR_aligned, traffic_indicator)

    def generate_streets_outputs(self):
        ##https://www.statology.org/plot-pandas-series/
        ##https://saturncloud.io/blog/how-to-search-pandas-data-frame-by-index-value-and-value-in-any-column/#:~:text=To%20search%20a%20pandas%20data%20frame%20by%20index%20value%2C%20you,a%20variety%20of%20input%20formats.
        selected_street = None
        selected_street = re.split(' ', self.window.selected_street_label.text())
        if selected_street == None:
            return
        edge_id = selected_street[1]
        list_edgeClosed = []
        for x in range(self.listview_closed_road_result_model.rowCount()):
            r = re.split(' ', self.listview_closed_road_result_model.item(x).text())
            list_edgeClosed.append(r[1])
        if edge_id not in list_edgeClosed:
            traffic_indicator = self.window.comboBox_results_by_street_traffic_indicator.itemText(
                self.window.comboBox_results_by_street_traffic_indicator.currentIndex())

            edgedata_csv_file_O = os.path.join(os.getcwd(), "Sumo", "outputs", "Ofile.out.csv")
            edgedata_csv_file_R = os.path.join(os.getcwd(), "Sumo", "outputs", "Rfile.out.csv")
            if os.path.exists(edgedata_csv_file_O) and os.path.exists(edgedata_csv_file_R):
                dO = pd.read_csv(edgedata_csv_file_O, sep=";")
                dR = pd.read_csv(edgedata_csv_file_R, sep=";")

                dfO = self.detectors_out_to_table(dO, traffic_indicator)
                dfR = self.detectors_out_to_table(dR, traffic_indicator)

                dfO.fillna(0, inplace=True)
                dfR.fillna(0, inplace=True)

                dfO = dfO.loc[edge_id]
                dfR = dfR.loc[edge_id]
                dfO.drop(dfO.index[-1], inplace=True)
                dfR.drop(dfR.index[-1], inplace=True)

                time_intervals = dO['interval_id'].unique()
                name = self.id_names_dict.get(edge_id)
                sns.axes_style("ticks")
                fig, ax = plt.subplots(figsize=(12, 10))
                plt.plot(dfO.index, dfO.values, color='red', linewidth=2.5)
                plt.plot(dfR.index, dfR.values, color='blue', linewidth=2.5)
                plt.legend(labels=["Without deviations", "With deviations"], fontsize="large")

                ax.tick_params(axis='x', labelsize=14, rotation=90)
                #ax.set_ylim([0, 100])
                #plt.legend(loc=7, bbox_to_anchor=(1.33, 0.5), fontsize=16)
                ax.set_xlabel('Timeframes', fontsize=18)
                ax.set_ylabel(traffic_indicator, fontsize=18)
                plt.suptitle(name +' ('+ edge_id + ')', fontsize=26, x=0.5)
                plt.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
                plt.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
                self.generate_png_outputs()

    def generate_group_outputs(self, dfO_aligned, dfR_aligned, traffic_indicator):
        df = dfR_aligned - dfO_aligned
        fig, ax = plt.subplots(figsize=(20, 10))
        sns.stripplot(data=df, orient="h")
        #plt.plot(df.index, df[name], linewidth=3.0)
        ax.set(xlabel='Edges')
        ax.set_ylabel('Time intervals', fontsize=30)
        ax.set_xlabel('Values', fontsize=30)
        plt.xticks(rotation=90)
        ax.tick_params(axis='x', which="both", bottom=False, top=False, labelsize=18, rotation=90)
        ax.tick_params(axis='y', labelsize=18)
        plt.subplots_adjust(top=0.9)
        plt.suptitle('Comparing the streets in terms of ' + traffic_indicator, fontsize=32)
        plt.tight_layout()
        fig.subplots_adjust(wspace=0.26)
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()

    def generate_maps_outputs(self):
        edgedata_O_out_csv = os.path.join(os.getcwd(), "Sumo", "outputs", "Ofile.out.csv")
        edgedata_R_out_csv = os.path.join(os.getcwd(), "Sumo", "outputs", "Rfile.out.csv")
        output_geojson_O_path = os.path.join(os.getcwd(), "qt_ui", "geoDFO.geojson")
        output_geojson_R_path = os.path.join(os.getcwd(), "qt_ui", "geoDFR.geojson")
        interval = self.window.comboBox_results_maps_time_interval.itemText(
            self.window.comboBox_results_time_interval.currentIndex())
        traffic_indicator = self.window.comboBox_results_maps_traffic_indicator.itemText(
            self.window.comboBox_results_maps_traffic_indicator.currentIndex())

        O1, O2, O3, O4, Ominim, Omaxim = self.mapLayout_output.map_to_geojson(edgedata_O_out_csv, output_geojson_O_path, interval, traffic_indicator)
        R1, R2, R3, R4, Rminim, Rmaxim = self.mapLayout_output.map_to_geojson(edgedata_R_out_csv, output_geojson_R_path, interval, traffic_indicator)

        minim = min(Ominim, Rminim)
        maxim = max(Omaxim, Rmaxim)

        self.mapLayout_output.redraw_folium_map(output_geojson_O_path, output_geojson_R_path, traffic_indicator, O1, O2, O3, O4, minim, maxim, self.closing)

    def detectors_out_to_table(self, sim_data_df, field_name):
        # parse all the intervals in the edgedata file
        time_intervals = sim_data_df['interval_id'].unique()
        data_dict = {}
        for time_interval in time_intervals:
            #print(time_interval)
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

    def plots_histogram(self, dO, dfO, dfR, arg):
        time_intervals = dO['interval_id'].unique()
        idx = 1
        num = len(time_intervals)
        fig, ax = plt.subplots(figsize=(10, 30))#, nrows=2, ncols=1, sharex=True, sharey=True)
        # ax = plt.gca()
        for name in time_intervals:
            plt.subplot(num, 1, idx)
            ax = plt.hist([dfO[name], dfR[name]], bins=10, label=['open', 'rerouting'])
            plt.title(name)
            plt.xlabel("Values", fontsize=14)
            plt.ylabel("Frequency", fontsize=14)
            plt.xticks(fontsize=12)
            plt.yticks(fontsize=12)
            plt.legend(loc='upper right', fontsize=14)
            plt.margins(x=0.02, tight=True)
            ##
            idx += 1
        plt.suptitle('Comparing timeframes in term of ' + arg + ', \nclosing and nonclosing edges', fontsize=22, y=1)
        plt.tight_layout()
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()


    def plots_one_histogram(self, dfO, dfR, arg, interval):
        # intervals = [str(interval)]
        fig, ax = plt.subplots(figsize=(10, 10), nrows=2, ncols=1, sharex=True, sharey=True)
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
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()

    def plots_histplot(self, dO, dfO, arg):
        time_intervals = dO['interval_id'].unique()
        idx = 0
        num = len(time_intervals)
        dim = int(round(num / 2))
        fig, ax = plt.subplots(figsize=(10, 20))
        for name in time_intervals:
            idx += 1
            plt.subplot(dim, 2, idx)
            ax = sns.histplot(dfO[name], kde=True, kde_kws={'bw_adjust': 0.5})
            ax.set(xlabel='seconds')
            ax.set_title(name)

        plt.subplots_adjust(top=0.9)
        plt.suptitle(arg + ' per time frame (seconds)', fontsize=16)
        plt.tight_layout()
        # plt.show()
        plt.subplots_adjust(wspace=0.26)
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()

    def plots_one_histplot(self, dfO, arg, interval):
        fig, ax = plt.subplots(figsize=(10, 10))
        plt.subplot(1, 1, 1)
        ax = sns.histplot(dfO[interval], kde=True, kde_kws={'bw_adjust': 0.5})
        ax.set(xlabel='seconds')
        ax.set_title(interval)
        plt.subplots_adjust(top=0.9)
        plt.suptitle(arg + ' per time frame (' + interval + 'seconds)', fontsize=16)
        plt.tight_layout()
        # plt.show()
        plt.subplots_adjust(wspace=0.26)
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()


    def generate_png_outputs(self):
        # plot_type = self.window.comboBox_results_figures.itemText(self.window.comboBox_results_figures.currentIndex())
        filename = os.path.join(os.getcwd(), "Sumo", "outputs", "file.png")
        if not filename:
            print("please select the .png file")
            sys.exit(0)
        else:
            self.window.label_plot.setPixmap(QtGui.QPixmap(filename))
            self.window.export_pdf_button.setDisabled(False)

    def export_pdf(self, event):
        if os.path.exists(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf")):
            cmd = "python viewer_pdf.py"
            os.system(cmd)
        else:
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage("file not found")
            print("file not found")
            sys.exit(0)

    def read_json(self):
        self.id_names_dict = {}
        with open(os.path.join(os.getcwd(), "qt_ui", "bxl_Tulipe.geojson"), encoding='utf-8') as f:


            data = json.load(f)
        for feature in data['features']:
            self.id_names_dict.update({feature['properties'].get("id"): feature['properties'].get("name")})
            #print({feature['properties'].get("id"): feature['properties'].get("name")})

    def Animation(self):
        # self.window.Button_run_simulation.
        self.loading_screen = LoadingScreen()
        QtCore.QTimer.singleShot(100, lambda: self.run_simulation())


    def execute_sumo(self, exp_id, args):
        # if self.p is None:  # No process running.
        #     self.message("Executing process")
        #     self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
        #     self.p.finished.connect(self.process_finished)  # Clean up once complete.
        #     self.p.start("sumo", ['-c Sumo\osm.sumocfg'])
        # self.threadpool = QThreadPool()
        # print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        # worker = Worker()
        # self.threadpool.start(worker)
        #"" + exp_id + "_O.out.xml"
        os.system("sumo -n " + os.path.join(os.getcwd(), "Sumo", "osm.net.xml.gz") + " -r " + os.path.join(os.getcwd(), "Sumo", "osm.passenger.trips.xml") +
                  " -a " + os.path.join(os.getcwd(), "Sumo", "conf."+args+".xml") + " -b 0 -e " +self.time_total +
                  " --tripinfo-output " + os.path.join(os.getcwd(), "Sumo", "outputs", exp_id + "_" + args + ".veh.xml") +
                " --tripinfo-output.write-unfinished --ignore-route-errors true --verbose false --duration-log.statistics "
                "true --no-step-log true")# --fcd-output Sumo\\outputs\\" + exp_id + "_" + args + ".fcd.xml")

        if args == 'R':
            self.loading_screen.stopAnimation()

    def run_simulation(self):
        now = datetime.now()
        exp_id = now.strftime("%d_%m_%Y-%H_%M_%S")

        self.set_interval_list()
        #self.write_open_conf_files(exp_id, 'O')
        self.write_conf_files(exp_id, 'O')
        self.execute_sumo(exp_id, 'O')
        print('Sumo Open finished')

        self.write_conf_files(exp_id, 'R')
        self.execute_sumo(exp_id, 'R')
        print('Sumo Close finished')

        self.write_exp_dict(exp_id)
        self.list_load_results()


    def valueChanged_hours(self):
        h = self.window.spinBox_hours.text()
        m = self.window.spinBox_minutes.text()
        s = self.window.spinBox_seconds.text()
        hour = h + 'h: ' + m + 'm:' + s + 's'
        self.window.label_simulation_duration.setText(hour)

        if len(self.w.closed_edges) != 0:
            model_event = self.window.listView_simulation.model()
            model_current = self.window.listView_current_simulation.model()
            for index in range(model_event.rowCount()):
                item = model_event.item(index)
                item2 = model_current.item(index)
                item_name = re.split(' \n', item.text())
                res = re.split('from: |to: |h:|m:|s', item.text())
                s_end = res[-2]
                m_end = res[-3]
                h_end = res[-4]
                s_beg = res[-6]
                m_beg = res[-7]
                h_beg = res[-8]
                item.setText(item_name[0] + " \nClosing from: "+ h_beg+"h:" +m_beg+"m:"+s_beg+"s - to: " + h + "h:" + m + "m:" + s + "s")
                item2.setText(item_name[
                                 0] + " \nClosing from: " + h_beg + "h:" + m_beg + "m:" + s_beg + "s  - to: " + h + "h:" + m + "m:" + s + "s")

            self.window.spinBox_end_hours.setValue(int(h))
            self.window.spinBox_end_minutes.setValue(int(m))
            self.window.spinBox_end_seconds.setValue(int(s))

    def valueChanged_event(self):
        if len(self.w.closed_edges) != 0:
            h_beg = self.window.spinBox_beginning_hours.text()
            m_beg = self.window.spinBox_beginning_minutes.text()
            s_beg = self.window.spinBox_beginning_seconds.text()
            h_end = self.window.spinBox_end_hours.text()
            m_end = self.window.spinBox_end_minutes.text()
            s_end = self.window.spinBox_end_seconds.text()
            for index in self.window.listView_simulation.selectedIndexes():
                item = self.window.listView_simulation.model().itemFromIndex(index)
                item_name = re.split(' \n', item.text())
                item.setText(item_name[0] + " \nClosing from: "+ h_beg+"h:" +m_beg+"m:"+s_beg+"s - to: " + h_end + "h:" + m_end + "m:" + s_end + "s")

            model_event = self.window.listView_simulation.model()
            model_current = self.window.listView_current_simulation.model()
            for index in range(model_event.rowCount()):
                item = model_event.item(index)
                item2 = model_current.item(index)
                item2.setText(item.text())

    def valueChanged_intervals(self):
        self.window.label_simulation_intervals.setText(self.window.spinBox_intervals.text())

    def valueChanged_traffic(self):
        traffic_level = "Low"
        if self.window.radioButton_medium_traffic.isChecked() == True:
            traffic_level = "Medium"
        if self.window.radioButton_heavy_traffic.isChecked() == True:
            traffic_level = "Heavy"
        self.window.label_simulation_traffic.setText(traffic_level)

    def write_exp_dict(self, exp_id):
        edge_times = []
        closed_edges = []
        model_event = self.window.listView_simulation.model()
        for index in range(model_event.rowCount()):
            edge = []
            item = model_event.item(index)
            r = re.split(' ', item.text())
            edge_id = r[1]
            res = re.split('from: |to: |h:|m:|s', item.text())
            edge.append(edge_id)
            edge.append(res[-8])
            edge.append(res[-7])
            edge.append(res[-6])
            edge.append(res[-4])
            edge.append(res[-3])
            edge.append(res[-2])
            edge_times.append(edge)
        for street in self.w.closed_edges:
            closed_edges.append(street)
        self.existing_exp_dic[exp_id] = {
            'traffic': self.traffic_level_str,
            "hours": self.time_hours,
            'minutes': self.time_minutes,
            'seconds': self.time_seconds,
            'intervals': self.intervals,
            'closed_roads': closed_edges,
            'events' : edge_times
        }
        with open(os.path.join(os.getcwd(), "Sumo", "outputs", "data"), 'w') as file:
            file.write(json.dumps(self.existing_exp_dic))
        #print(self.existing_exp_dic)

    def read_exp_dict(self):
        file_size = os.path.getsize(os.path.join(os.getcwd(), "Sumo", "outputs", "data"))
        #print(file_size)
        if file_size != 0:
            with open(os.path.join(os.getcwd(), "Sumo", "outputs", "data"), "r") as file:
                data = file.read()
                data = json.loads(data)
                self.existing_exp_dic = data

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
        self.existing_exp_dic = {}
        self.ui_file_name = "formTulipe2.ui"
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
        self.read_exp_dict()
        self.p = None


        self.window.openStreetButton = self.window.findChild(QPushButton, 'openStreetButton')
        self.window.openStreetButton.clicked.connect(self.on_open_road_button_click)
        self.window.closeStreetButton = self.window.findChild(QPushButton, 'closeStreetButton')
        self.window.closeStreetButton.clicked.connect(self.on_close_road_button_click)
        self.window.label_selected_road_from_map = self.window.findChild(QLabel, 'label_selected_road_from_map')
        self.window.closedStreetListView = self.window.findChild(QListView, 'closedStreetListView')
        self.closed_street_model = QStandardItemModel()
        self.window.closedStreetListView.setModel(self.closed_street_model)
        self.window.label_mlg = self.window.findChild(QLabel, 'label_mlg')
        self.window.label_mlg.setPixmap(QtGui.QPixmap("mlg.png"))
        self.window.label_ulb = self.window.findChild(QLabel, 'label_ulb')
        self.window.label_ulb.setPixmap(QtGui.QPixmap("ulb.png"))


        #Maps
        self.window.mapLayout = self.window.findChild(QVBoxLayout, 'mapLayout')
        self.window.MapLayoutsimulation = self.window.findChild(QVBoxLayout, 'mapLayout_simulation')
        self.window.mapLayout_output = self.window.findChild(QVBoxLayout, 'mapLayout_output')

        self.w = FoliumDisplay(geojson_path=os.path.join(os.getcwd(), "qt_ui", "bxl_Tulipe.geojson"))
        self.w.on_edge_selected.connect(self.edge_selected)

        self.w_simulation = FoliumSimulationDisplay(geojson_path=os.path.join(os.getcwd(), "qt_ui", "bxl_Tulipe.geojson"))
        self.mapLayout_output = FoliumDisplay2(geojson_path=os.path.join(os.getcwd(), "qt_ui", "geoDF.geojson"))
        self.mapLayout_output.on_edge_selected.connect(self.edge_selected_results)

        self.window.mapLayout.addWidget(self.w)
        self.window.MapLayoutsimulation.addWidget(self.w_simulation)
        self.window.mapLayout_output.addWidget(self.mapLayout_output)

        # Load Network
        self.net = self.w.net_handler.get_net()


        ##### Traffic Simulation
        self.window.spinBox_hours = self.window.findChild(QSpinBox, 'spinBox_simulation_hours')
        self.window.spinBox_minutes = self.window.findChild(QSpinBox, 'spinBox_simulation_minutes')
        self.window.spinBox_seconds = self.window.findChild(QSpinBox, 'spinBox_simulation_seconds')
        self.window.spinBox_intervals = self.window.findChild(QSpinBox, 'spinBox_simulation_interval')
        self.window.radioButton_low_traffic = self.window.findChild(QRadioButton, 'radioButton_low_traffic')
        self.window.radioButton_medium_traffic = self.window.findChild(QRadioButton, 'radioButton_medium_traffic')
        self.window.radioButton_heavy_traffic = self.window.findChild(QRadioButton, "radioButton_heavy_traffic")
        self.window.run_simulation_button = self.window.findChild(QPushButton, 'run_simulation_button')
        self.window.run_simulation_button.clicked.connect(self.Animation)

        self.window.spinBox_hours.valueChanged.connect(self.valueChanged_hours)
        self.window.spinBox_minutes.valueChanged.connect(self.valueChanged_hours)
        self.window.spinBox_seconds.valueChanged.connect(self.valueChanged_hours)
        self.window.spinBox_intervals.valueChanged.connect(self.valueChanged_intervals)
        self.window.radioButton_low_traffic.toggled.connect(self.valueChanged_traffic)
        self.window.radioButton_medium_traffic.toggled.connect(self.valueChanged_traffic)
        self.window.radioButton_heavy_traffic.toggled.connect(self.valueChanged_traffic)

        self.valueChanged_hours()
        self.valueChanged_intervals()
        self.valueChanged_traffic()

        ##Event
        self.window.spinBox_end_hours = self.window.findChild(QSpinBox, 'spinBox_end_hours')
        self.window.spinBox_end_minutes = self.window.findChild(QSpinBox, 'spinBox_end_minutes')
        self.window.spinBox_end_seconds = self.window.findChild(QSpinBox, 'spinBox_end_seconds')
        self.window.spinBox_beginning_hours = self.window.findChild(QSpinBox, 'spinBox_beginning_hours')
        self.window.spinBox_beginning_minutes = self.window.findChild(QSpinBox, 'spinBox_beginning_minutes')
        self.window.spinBox_beginning_seconds = self.window.findChild(QSpinBox, 'spinBox_beginning_seconds')
        self.window.listView_simulation = self.window.findChild(QListView, 'listView_simulation')
        self.listView_simulation_model = QStandardItemModel()
        self.window.listView_simulation.setModel(self.listView_simulation_model)
        self.window.listView_simulation.selectionModel().selectionChanged.connect(self.listView_simulation)

        self.window.spinBox_end_hours.valueChanged.connect(self.valueChanged_event)
        self.window.spinBox_end_minutes.valueChanged.connect(self.valueChanged_event)
        self.window.spinBox_end_seconds.valueChanged.connect(self.valueChanged_event)
        self.window.spinBox_beginning_hours.valueChanged.connect(self.valueChanged_event)
        self.window.spinBox_beginning_minutes.valueChanged.connect(self.valueChanged_event)
        self.window.spinBox_beginning_seconds.valueChanged.connect(self.valueChanged_event)

        ## Current Simulation
        self.window.label_simulation_traffic = self.window.findChild(QLabel, 'label_simulation_traffic')
        self.window.label_simulation_intervals = self.window.findChild(QLabel, 'label_simulation_intervals')
        self.window.label_simulation_duration = self.window.findChild(QLabel, 'label_simulation_duration')
        self.window.listView_current_simulation = self.window.findChild(QListView, 'listView_current_simulation')
        self.listView_current_simulation_model = QStandardItemModel()
        self.window.listView_current_simulation.setModel(self.listView_current_simulation_model)

        self.window.label_mlg_2 = self.window.findChild(QLabel, 'label_mlg_3')
        self.window.label_mlg_2.setPixmap(QtGui.QPixmap("mlg.png"))
        self.window.label_ulb_2 = self.window.findChild(QLabel, 'label_ulb_3')
        self.window.label_ulb_2.setPixmap(QtGui.QPixmap("ulb.png"))

        ##### Results
        #Select the simulation
        self.window.listView_load_results = self.window.findChild(QListView, 'listView_load_results')
        self.load_results_model = QStandardItemModel()
        self.window.listView_load_results.setModel(self.load_results_model)
        self.window.listView_load_results.selectionModel().selectionChanged.connect(self.load_results)
        self.window.selected_simulation_label = self.window.findChild(QLabel, 'selected_simulation_label')
        self.window.traffic_level_output_label = self.window.findChild(QLabel, 'traffic_level_output_label')
        self.window.intervals_output_label = self.window.findChild(QLabel, 'intervals_output_label')
        self.window.durationl_output_label = self.window.findChild(QLabel, 'durationl_output_label')
        self.window.listview_closed_road_result = self.window.findChild(QListView, 'listview_closed_road_result')
        self.listview_closed_road_result_model = QStandardItemModel()
        self.window.listview_closed_road_result.setModel(self.listview_closed_road_result_model)
        #self.window.listview_closed_road_result.selectionModel().selectionChanged.connect(self.listview_closed_road_result)

        ##Maps
        self.window.comboBox_results_maps_time_interval = self.window.findChild(QComboBox, 'comboBox_results_maps_time_interval')
        self.window.comboBox_results_maps_traffic_indicator = self.window.findChild(QComboBox,'comboBox_results_maps_traffic_indicator')
        self.window.generate_map_button = self.window.findChild(QPushButton, 'generate_map_button')
        self.window.generate_map_button.clicked.connect(self.generate_maps_outputs)

        ##Output
        #Results by street
        self.window.comboBox_results_by_street_traffic_indicator = self.window.findChild(QComboBox,'comboBox_results_by_street_traffic_indicator')
        self.window.selected_street_label  = self.window.findChild(QLabel, 'selected_street_label')
        self.window.generate_street_outputs_button = self.window.findChild(QPushButton, 'generate_street_outputs_button')
        self.window.generate_street_outputs_button.clicked.connect(self.generate_streets_outputs)

        #Groups

        self.window.comboBox_results_veh_figure = self.window.findChild(QComboBox, 'comboBox_results_veh_figure')
        self.window.comboBox_results_veh_traffic_indicator = self.window.findChild(QComboBox, 'comboBox_results_veh_traffic_indicator')
        self.window.generate_vehicles_button = self.window.findChild(QPushButton,'generate_vehicles_button')
        self.window.generate_vehicles_button.clicked.connect(self.plot_vehicles)

        #Integrated results
        self.window.comboBox_results_time_interval = self.window.findChild(QComboBox, 'comboBox_results_time_interval')
        self.window.comboBox_results_traffic_indicator = self.window.findChild(QComboBox, 'comboBox_results_traffic_indicator')
        self.window.comboBox_results_figures = self.window.findChild(QComboBox, 'comboBox_results_figures')
        self.window.generate_integrate_outputs_button = self.window.findChild(QPushButton, 'generate_integrated_outputs_button')
        self.window.generate_integrate_outputs_button.clicked.connect(self.generate_integrated_outputs)

        #Plots
        self.window.export_pdf_button = self.window.findChild(QPushButton, 'export_pdf_button')
        self.window.export_pdf_button.clicked.connect(self.export_pdf)
        self.window.label_plot = self.window.findChild(QLabel, 'label_plot')

        self.window.label_mlg_2 = self.window.findChild(QLabel, 'label_mlg_2')
        self.window.label_mlg_2.setPixmap(QtGui.QPixmap("mlg.png"))
        self.window.label_ulb_2 = self.window.findChild(QLabel, 'label_ulb_2')
        self.window.label_ulb_2.setPixmap(QtGui.QPixmap("ulb.png"))
        self.window.without_label = self.window.findChild(QLabel, 'without_label')
        self.window.without_label.setPixmap(QtGui.QPixmap("Without.png"))
        self.window.without_label = self.window.findChild(QLabel, 'with_label')
        self.window.without_label.setPixmap(QtGui.QPixmap("With.png"))

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
