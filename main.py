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
    QRadioButton, QSpinBox, QComboBox, QTimeEdit
import folium
from PySide6.QtCore import Signal
import seaborn as sns
from qt_ui.mapControl import FoliumDisplay
from qt_ui.mapOutputControl import FoliumDisplay2
from qt_ui.mapControlSimulation import FoliumSimulationDisplay
from sumo import SumoClass
import math
from datetime import datetime
import time
import xmltodict
# from fpdf import FPDF
import matplotlib.ticker as ticker

class LoadingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 200)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        self.label_animation = QtWidgets.QLabel(self)

        self.movie = QMovie(os.path.join(os.getcwd(), "qt_ui", "Herbert_Kickl.gif"))
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

        # Results by vehicles
        self.window.comboBox_results_veh_traffic_indicator.setDisabled(False)
        self.window.comboBox_results_veh_traffic_indicator.clear()
        self.window.comboBox_results_veh_traffic_indicator.addItem('duration')
        self.window.comboBox_results_veh_traffic_indicator.addItem('routeLength')
        self.window.comboBox_results_veh_traffic_indicator.addItem('timeLoss')
        self.window.comboBox_results_veh_traffic_indicator.addItem('waitingTime')
        self.window.generate_vehicles_button.setDisabled(False)

        self.window.comboBox_results_veh_figure.setDisabled(False)
        self.window.comboBox_results_veh_figure.clear()
        self.window.comboBox_results_veh_figure.addItem('scatter plot')
        self.window.comboBox_results_veh_figure.addItem('histogram plot')
        self.window.comboBox_results_veh_figure.addItem('vehicles plot')

        # Results by Street
        self.window.comboBox_results_by_street_traffic_indicator.setDisabled(False)
        self.window.comboBox_results_by_street_traffic_indicator.clear()
        self.window.comboBox_results_by_street_traffic_indicator.addItem('density')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('occupancy')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('timeLoss')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('traveltime')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('waitingTime')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('speed')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('speedRelative')
        self.window.comboBox_results_by_street_traffic_indicator.addItem('sampledSeconds')
        self.window.generate_street_outputs_button.setDisabled(False)

        for index in self.window.listView_load_results.selectedIndexes():
            item = self.window.listView_load_results.model().itemFromIndex(index)
            loaded_exp_id = item.text()
            res = re.split(' ', loaded_exp_id)
            id = res[1]

        Ofile_Veh = os.path.join(os.getcwd(), "Sumo", "outputs", id + "_O.veh.xml")
        Rfile_Veh = os.path.join(os.getcwd(), "Sumo", "outputs", id + "_R.veh.xml")
        if os.path.exists(Ofile_Veh):
            os.system("python \"" + os.path.join(os.environ["SUMO_TOOL"], "xml",
                                                 "xml2csv.py\" ") + Ofile_Veh + " -o " + os.path.join(os.getcwd(),
                                                                                                      "Sumo", "outputs",
                                                                                                      "Ofile.veh.csv"))
        if os.path.exists(Rfile_Veh):
            os.system("python \"" + os.path.join(os.environ["SUMO_TOOL"], "xml",
                                                 "xml2csv.py\" ") + Rfile_Veh + " -o " + os.path.join(os.getcwd(),
                                                                                                      "Sumo", "outputs",
                                                                                                      "Rfile.veh.csv"))

        nextEdges_incoming = self.net.getEdge(edge_id).getIncoming()

    def listview_closed_road_result(self):
        for index in self.window.listview_closed_road_result.selectedIndexes():
            item = self.window.listview_closed_road_result.model().itemFromIndex(index)
            self.window.selected_street_label.clear()

    def listView_simulation(self):
        self.window.spinBox_beginning_hours.setDisabled(False)
        self.window.spinBox_beginning_minutes.setDisabled(False)
        self.window.spinBox_beginning_seconds.setDisabled(False)

        self.window.spinBox_end_hours.setDisabled(False)
        self.window.spinBox_end_minutes.setDisabled(False)
        self.window.spinBox_end_seconds.setDisabled(False)

        for index in self.window.listView_simulation.selectedIndexes():
            item = self.window.listView_simulation.model().itemFromIndex(index)
            # print(item.text())
            res = re.split('from: |to: |:| -', item.text())
            s_end = res[-1]
            m_end = res[-2]
            h_end = res[-3]
            s_beg = res[-5]
            m_beg = res[-6]
            h_beg = res[-7]

        # h = self.window.spinBox_hours.text()
        # m = self.window.spinBox_minutes.text()
        # s = self.window.spinBox_seconds.text()

        # resu = re.split(':', self.starting_time_hours_minutes_seconds)
        # starting_hours = resu[0]
        # starting_minutes = resu[1]
        # starting_seconds = resu[2]

        self.window.spinBox_beginning_hours.setValue(int(h_beg))
        self.window.spinBox_end_hours.setValue(int(h_end))

        self.window.spinBox_beginning_minutes.setRange(0, 59)
        self.window.spinBox_end_minutes.setRange(0, 59)
        self.window.spinBox_beginning_minutes.setValue(int(m_beg))
        self.window.spinBox_end_minutes.setValue(int(m_end))

        self.window.spinBox_beginning_seconds.setRange(0, 59)
        self.window.spinBox_end_seconds.setRange(0, 59)
        self.window.spinBox_beginning_seconds.setValue(int(s_beg))
        self.window.spinBox_end_seconds.setValue(int(s_end))
        #+int(starting_seconds)

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
            h = self.window.spinBox_simulation_hours.text()
            m = self.window.spinBox_simulation_minutes.text()
            s = self.window.spinBox_simulation_seconds.text()

            resu = re.split(' |:', self.starting_time_hours_minutes_seconds)
            starting_hours = resu[0]
            starting_minutes = resu[1]
            starting_seconds = resu[2]
            print(self.starting_time_hours_minutes_seconds)

            hs = int(h) + int(starting_hours)
            ms = int(m) + int(starting_minutes)
            ss = int(s) + int(starting_seconds)

            if hs < 10:
                hs = "0"+ str(hs)
            if ms < 10:
                ms = "0"+ str(ms)
            if ss < 10:
                ss = "0"+ str(ss)

            self.closed_street_model.appendRow(QStandardItem("id: " + edge_id + " - " + name))
            self.listView_simulation_model.appendRow(QStandardItem(
                "id: " + edge_id + " - " + name + " \nClosing from: "+str(starting_hours)+":"+starting_minutes+":"+starting_seconds+" - to: " + str(hs) + ":" + str(ms) + ":" + str(ss)))
            self.listView_current_simulation_model.appendRow(QStandardItem(
                "id: " + edge_id + " - " + name + " \nClosing from: "+str(starting_hours)+":"+starting_minutes+":"+starting_seconds+" - to: " + str(hs) + ":" + str(ms) + ":" + str(ss)))
        pass

    def on_open_road_button_click(self):
        res = None
        # Deleting from closedStreetListView
        for index in self.window.closedStreetListView.selectedIndexes():
            item = self.window.closedStreetListView.model().itemFromIndex(index)
            res = re.split(' ', item.text())
        if res is not None:
            edge_id = res[1]
            self.closed_street_model.takeRow(item.row())

            model_simulation = self.window.listView_simulation.model()
            for index in range(model_simulation.rowCount()):
                item = model_simulation.item(index)
                r = re.split(' ', item.text())
                edge = r[1]
                if edge == edge_id:
                    # item.row()
                    self.listView_simulation_model.takeRow(item.row())
                    break

            model_current = self.window.listView_current_simulation.model()
            for index in range(model_current.rowCount()):
                item = model_current.item(index)
                r = re.split(' ', item.text())
                edge = r[1]
                if edge == edge_id:
                    # item.row()
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
                        self.closed_street_model.takeRow(item.row())
                        break

                model_simulation = self.window.listView_simulation.model()
                for index in range(model_simulation.rowCount()):
                    item = model_simulation.item(index)
                    r = re.split(' ', item.text())
                    edge = r[1]
                    if edge == edge_id:
                        self.listView_simulation_model.takeRow(item.row())
                        break

                model_current = self.window.listView_current_simulation.model()
                for index in range(model_current.rowCount()):
                    item = model_current.item(index)
                    r = re.split(' ', item.text())
                    edge = r[1]
                    if edge == edge_id:
                        self.listView_current_simulation_model.takeRow(item.row())
                        break

                self.w.closed_edges.remove(edge_id)
                self.w.redraw_folium_map()

                self.w_simulation.closed_edges.remove(edge_id)
                self.w_simulation.redraw_folium_map()

        self.window.closedStreetListView.clearSelection()
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
        if time_total < interval:
            return
        values = round(time_total / interval)

        items = []
        for numbers in range(interval):
            items.append(numbers * values)
        items.append(time_total)
        self.time_total = str(time_total)
        self.interval_list = items

        res = re.split(':', self.starting_time_hours_minutes_seconds)
        starting_hours = res[0]
        starting_minutes = res[1]
        starting_seconds = res[2]
        starting_time_in_seconds = (int(starting_hours) * 3600) + (int(starting_minutes) * 60) + int(starting_seconds)
        self.starting_time_in_seconds = str(starting_time_in_seconds)

    def generate_random_trips(self):
        end_time = int(self.starting_time_in_seconds) + int(self.time_total)
        os.system(
            "python \"" + os.path.join(os.environ["SUMO_TOOL"], "randomTrips.py\"") + " -n " +
            os.path.join(os.getcwd(), "Sumo", "osm.net.xml.gz") + " --fringe-factor " + self.fringe_factor +
            " --insertion-rate " + self.traffic_level + " -o " + os.path.join(os.getcwd(), "Sumo", "osm.passenger.trips.xml") +
            " -r " + os.path.join(os.getcwd(), "Sumo", "osm.passenger.rou.xml") + " -b " + self.starting_time_in_seconds +
            " -e " + str(end_time) + " --validate --remove-loops")

    def list_load_results(self):
        self.load_results_model.clear()
        i = 1
        for id in self.existing_exp_dic:
            exp = "Exp" + str(i) + ": " + id
            self.load_results_model.appendRow(QStandardItem(exp))
            i += 1

    def load_results(self):
        loaded_exp_id = self.load_info()
        self.convert_xml_to_csv(loaded_exp_id)
        self.enable_outputs_intervals(self.startingtime, self.h, self.m, self.s, self.i)
        self.generate_maps_outputs()

    def load_info(self):
        for index in self.window.listView_load_results.selectedIndexes():
            item = self.window.listView_load_results.model().itemFromIndex(index)
            res = re.split(' ', item.text())
            loaded_exp_id = res[1]
            self.window.selected_simulation_label.clear()
            self.window.selected_simulation_label.setText("Selected simulation : " + item.text())
            self.traffic = self.existing_exp_dic[loaded_exp_id].get('traffic')
            self.startingtime  = self.existing_exp_dic[loaded_exp_id].get('starting_time')
            self.h = self.existing_exp_dic[loaded_exp_id].get('hours')
            self.m = self.existing_exp_dic[loaded_exp_id].get('minutes')
            self.s = self.existing_exp_dic[loaded_exp_id].get('seconds')
            self.i = self.existing_exp_dic[loaded_exp_id].get('intervals')
            self.closing = self.existing_exp_dic[loaded_exp_id].get('closed_roads')
            self.events = self.existing_exp_dic[loaded_exp_id].get('events')
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
                    if times[0] == edge_id:
                        self.listview_closed_road_result_model.appendRow(QStandardItem(
                            "id: " + edge_id + " \n" + name + "\nClosing from: " + times[1] + ":" + times[2] + ":" +
                            times[3] + " - to: " + times[4] + ":" + times[5] + ":" + times[6] + ")"))
                        break
        return loaded_exp_id

    def convert_xml_to_csv(self, loaded_exp_id):
        Ofile = (os.path.join(os.getcwd(), "Sumo", "outputs", loaded_exp_id + "_O.out.xml"))
        Rfile = (os.path.join(os.getcwd(), "Sumo", "outputs", loaded_exp_id + "_R.out.xml"))
        if os.path.exists(Ofile):
            os.system("python \"" + os.path.join(self.path_sumo_tools, "xml",
                                                 "xml2csv.py\" ") + Ofile + " -o " + os.path.join(os.getcwd(), "Sumo",
                                                                                                  "outputs",
                                                                                                  "Ofile.out.csv"))
        if os.path.exists(Rfile):
            os.system("python \"" + os.path.join(self.path_sumo_tools, "xml",
                                                 "xml2csv.py\" ") + Rfile + " -o " + os.path.join(os.getcwd(), "Sumo",
                                                                                                  "outputs",
                                                                                                  "Rfile.out.csv"))

    # def generate_interval_list(self, h, m, s, i):
    #     time_total = (int(h) * 3600) + (int(m) * 60) + int(s)
    #     values = round(time_total / int(i))
    #     items = []
    #     for numbers in range(int(i)):
    #         items.append(numbers * values)
    #     items.append(time_total)
    #     return items

    def convert(self, n):
        return time.strftime("%H:%M:%S", time.gmtime(n))

    def generate_interval_list(self, starting_time, h, m, s, i):
        time_total = (int(h) * 3600) + (int(m) * 60) + int(s)
        end_time = time_total + int(starting_time)
        values = round(time_total / int(i))
        items = []
        items_str = []
        hh = 0
        mm = 0
        ss = 0
        for numbers in range(int(i)):
            time = int(starting_time) + (int(numbers) * int(values))
            items.append(time)
            hms = self.convert(time)
            items_str.append(hms)
        items.append(end_time)
        items_str.append(self.convert(end_time))
        return items, items_str

    def enable_outputs_intervals(self, startingtime, h, m, s, i):
        self.window.comboBox_results_traffic_indicator.setDisabled(False)
        self.window.comboBox_results_traffic_indicator.clear()
        self.window.comboBox_results_traffic_indicator.addItem('density')
        self.window.comboBox_results_traffic_indicator.addItem('occupancy')
        self.window.comboBox_results_traffic_indicator.addItem('timeLoss')
        self.window.comboBox_results_traffic_indicator.addItem('traveltime')
        self.window.comboBox_results_traffic_indicator.addItem('waitingTime')
        self.window.comboBox_results_traffic_indicator.addItem('speed')
        self.window.comboBox_results_traffic_indicator.addItem('speedRelative')
        self.window.comboBox_results_traffic_indicator.addItem('sampledSeconds')

        self.window.comboBox_results_time_interval.setDisabled(False)
        self.window.comboBox_results_time_interval.clear()

        interval_list_seconds, interval_list = self.generate_interval_list(startingtime, h, m, s, i)
        self.window.comboBox_results_time_interval.addItem("All")
        self.window.comboBox_results_time_interval.addItem(str(interval_list[0]) + " - " + str(interval_list[-1]))
        for i in range(len(interval_list) - 1):
            self.window.comboBox_results_time_interval.addItem(
                str(interval_list[i]) + " - " + str(interval_list[i + 1]))

        self.window.comboBox_results_maps_time_interval.setDisabled(False)
        self.window.comboBox_results_maps_time_interval.clear()
        self.window.comboBox_results_maps_time_interval.addItem(str(interval_list[0]) + " - " + str(interval_list[-1]))
        for i in range(len(interval_list) - 1):
            self.window.comboBox_results_maps_time_interval.addItem(
                str(interval_list[i]) + " - " + str(interval_list[i + 1]))
        self.interval_dic = {}
        self.interval_dic[str(interval_list[0]) + " - " + str(interval_list[-1])] = {str(interval_list_seconds[0]) + "_to_" + str(interval_list_seconds[-1])}
        for i in range(len(interval_list) - 1):
            self.interval_dic[str(interval_list[i]) + " - " + str(interval_list[i+1])] = {str(interval_list_seconds[i]) + "_to_" + str(interval_list_seconds[i+1])}
        self.window.comboBox_results_maps_traffic_indicator.setDisabled(False)
        self.window.comboBox_results_maps_traffic_indicator.clear()
        self.window.comboBox_results_maps_traffic_indicator.addItem('density')
        self.window.comboBox_results_maps_traffic_indicator.addItem('occupancy')
        self.window.comboBox_results_maps_traffic_indicator.addItem('timeLoss')
        self.window.comboBox_results_maps_traffic_indicator.addItem('traveltime')
        self.window.comboBox_results_maps_traffic_indicator.addItem('waitingTime')
        self.window.comboBox_results_maps_traffic_indicator.addItem('speed')
        self.window.comboBox_results_maps_traffic_indicator.addItem('speedRelative')
        self.window.comboBox_results_maps_traffic_indicator.addItem('sampledSeconds')

        self.window.comboBox_results_figures.setDisabled(False)
        self.window.comboBox_results_figures.clear()
        self.window.comboBox_results_figures.addItem('histogram')
        # self.window.comboBox_results_figures.addItem('histplot')
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

            if interval == 'All' and plot_type == 'histogram':
                self.plots_histogram(dO, dfO_aligned, dfR_aligned, traffic_indicator)
            elif interval != 'All' and plot_type == 'histogram':
                interval_seconds = self.interval_dic[interval]
                self.plots_one_histogram(dfO_aligned, dfR_aligned, traffic_indicator, interval, interval_seconds)
            # elif interval == 'All' and plot_type == 'histplot':
            #     self.plots_histplot(dO, dfO_aligned, traffic_indicator)
            # elif interval != 'All' and plot_type == 'histplot':
            #     self.plots_one_histplot(dfO_aligned, traffic_indicator, interval)
            elif plot_type == 'plot':  # interval == 'All' and
                self.generate_group_outputs(dfO_aligned, dfR_aligned, traffic_indicator)

    def detectors_out_to_table(self, sim_data_df, field_name):
        # parse all the intervals in the edgedata file
        traffic_indicator = "edge_" + field_name
        time_intervals = sim_data_df['interval_id'].unique()
        data_dict = {}
        for time_interval in time_intervals:
            # get the DF related to time_interval
            data_interval = sim_data_df.loc[sim_data_df['interval_id'] == time_interval]
            # get the IDs of the edges that has an edgedata output value in the current time interval
            list_edges = data_interval['edge_id'].unique()
            for edge_id in list_edges:
                # get the data for all the edges
                data = data_interval.loc[data_interval['edge_id'] == edge_id][traffic_indicator]
                if time_interval not in data_dict:
                    data_dict[time_interval] = {}
                data_dict[time_interval][edge_id] = data.item()
        return pd.DataFrame.from_dict(data_dict)

    def get_key(self, val):
        for key, value in self.interval_dic.items():
            value = str(value)
            if val == value:
                return key
        return "key doesn't exist"

    def plots_histogram(self, dO, dfO, dfR, traffic):
        if traffic == "density":
            inf = "vehicle density (veh/km)"
        elif traffic == "occupancy":
            inf = "occupancy of the streets (%)"
        elif traffic == "timeLoss":
            inf = "time loss due to driving slower than desired (s)"
        elif traffic == "traveltime":
            inf = "travel time of the street (s))"
        elif traffic == "waitingTime":
            inf = "waiting time (s)"
        elif traffic == "speed":
            inf = "average speed (m/s)"
        elif traffic == "speedRelative":
            inf = "speed relative (average speed / speed limit)"
        elif traffic == "sampledSeconds":
            inf = "sampled seconds (veh/s)"
        time_intervals = dO['interval_id'].unique()
        idx = 1
        num = len(time_intervals)
        fig = plt.figure(figsize=(10, 30))#plt.subplots(figsize=(10, 30))  # , nrows=2, ncols=1, sharex=True, sharey=True)
        # ax = plt.gca()
        for name in time_intervals:
            plt.subplot(num, 1, idx)
            plt.hist([dfO[name], dfR[name]], bins=10, label=['Without deviations', 'With deviations'])
            na = "{\'" + name + "\'}"
            val = self.get_key(na)
            plt.title(val)
            plt.xlabel(inf, fontsize=10)
            plt.ylabel("Frequency of streets", fontsize=10)
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)
            plt.legend(loc='upper right', fontsize=12)
            plt.margins(x=0.02, tight=True)
            idx += 1
        plt.suptitle(
            'Comparing timeframes in term of the ' + traffic + ' of the streets, \nWith and without deviations',
            fontsize=18, y=1)
        plt.tight_layout()
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()

    def plots_one_histogram(self, dfO, dfR, traffic, interval, interval_seconds):
        if traffic == "density":
            inf = "vehicle density (veh/km)"
        elif traffic == "occupancy":
            inf = "occupancy of the streets (%)"
        elif traffic == "timeLoss":
            inf = "time loss due to driving slower than desired (s)"
        elif traffic == "traveltime":
            inf = "travel time of the street (s))"
        elif traffic == "waitingTime":
            inf = "waiting time (s)"
        elif traffic == "speed":
            inf = "average speed (m/s)"
        elif traffic == "speedRelative":
            inf = "speed relative (average speed / speed limit)"
        elif traffic == "sampledSeconds":
            inf = "sampled seconds (veh/s)"
        res = re.split("\'", str(interval_seconds))
        interval_sec = res[1]
        fig = plt.figure()
        plt.hist([dfO[interval_sec], dfR[interval_sec]], bins=10, label=['Without deviations', 'With deviations'])
        #plt.title(interval)
        plt.xlabel(inf)
        plt.ylabel("Number of streets")
        plt.legend(loc='upper right')
        plt.margins(x=0.02, tight=True)
        #ax = plt.gca()
        plt.suptitle(
            'Comparing Timeframe ' + interval + ' in term of ' + traffic + ' of the streets, \nwith and without deviations',
            fontsize=16, y=1)
        plt.tight_layout()
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()

    def plots_histplot(self, dO, dfO, arg):
        traffic = re.split('_', arg)
        traffic = traffic[1]
        time_intervals = dO['interval_id'].unique()
        idx = 0
        num = len(time_intervals)
        dim = int(math.ceil(num / 2))
        fig, ax = plt.subplots(figsize=(10, 20))
        for name in time_intervals:
            idx += 1
            plt.subplot(dim, 2, idx)
            ax = sns.histplot(dfO[name])  # , kde=True, kde_kws={'bw_adjust': 0.5})
            ax.set(xlabel='seconds')
            ax.set_title(name)
        plt.subplots_adjust(top=0.9)
        plt.suptitle('Comparing timeframes in term of ' + traffic + ', \nwith and without deviations', fontsize=16)
        plt.tight_layout()
        plt.subplots_adjust(wspace=0.26)
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()

    def plots_one_histplot(self, dfO, arg, interval):
        fig, ax = plt.subplots(figsize=(10, 10))
        plt.subplot(1, 1, 1)
        ax = sns.histplot(dfO[interval])  # , kde=True, kde_kws={'bw_adjust': 0.5})
        ax.set(xlabel='seconds')
        ax.set_title(interval)
        plt.subplots_adjust(top=0.9)
        plt.suptitle('Comparing Timeframe ' + interval + ' in term of ' + arg + ', with and without deviations',
                     fontsize=16)
        plt.tight_layout()
        plt.subplots_adjust(wspace=0.26)
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()

    def generate_group_outputs(self, dfO_aligned, dfR_aligned, traffic_indicator):
        df = dfR_aligned - dfO_aligned
        fig, ax = plt.subplots(figsize=(20, 10))
        sns.stripplot(data=df, orient="h")
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

    def plot_vehicles(self):
        traffic = self.window.comboBox_results_veh_traffic_indicator.itemText(
            self.window.comboBox_results_veh_traffic_indicator.currentIndex())

        traffic_indicator = "tripinfo_" + traffic

        edgedata_csv_file_O = os.path.join(os.getcwd(), "Sumo", "outputs", "Ofile.veh.csv")
        edgedata_csv_file_R = os.path.join(os.getcwd(), "Sumo", "outputs", "Rfile.veh.csv")
        if os.path.exists(edgedata_csv_file_O) and os.path.exists(edgedata_csv_file_R):
            dO = pd.read_csv(edgedata_csv_file_O, sep=";")
            dR = pd.read_csv(edgedata_csv_file_R, sep=";")

        dO = dO.loc[:,
             ['tripinfo_id',
              traffic_indicator]]

        dR = dR.loc[:,
             ['tripinfo_id',
              traffic_indicator]]

        veh_figure = self.window.comboBox_results_veh_figure.itemText(
            self.window.comboBox_results_veh_figure.currentIndex())

        if veh_figure == 'scatter plot':
            self.vehicles_scatter_plot(dO, dR, traffic)
        elif veh_figure == 'histogram plot':
            self.vehicles_histogram_plot(dO, dR, traffic_indicator, traffic)
        elif veh_figure == 'vehicles plot':
            self.extractreroutedvehicles()

    def vehicles_histogram_plot(self, dO, dR, traffic_indicator, traffic):
        if traffic == 'duration':
            value = 'Duration of the trips (s)'
        if traffic == 'routeLength':
            value = 'Route length (m)'
        if traffic == 'timeLoss':
            value = 'Time loss (s)'
        if traffic == 'waitingTime':
            value = 'Waiting time (s)'
        fig = plt.figure()#figsize=() #17, 10))  # , nrows=2, ncols=1, sharex=True, sharey=True)
        #plt.subplot(1, 1, 1)
        plt.hist([dO[traffic_indicator], dR[traffic_indicator]], bins=10, label=["Without deviations", "With deviations"])
        plt.xlabel(value, fontsize=14)
        plt.ylabel("Frequency of the vehicles", fontsize=14)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.legend(loc='upper right', fontsize=14)
        # plt.margins(x=0.02, tight=True)
        # ax = plt.gca()
        plt.suptitle('Comparing the ' + traffic + 'of the vehicles, \nwith and without deviations', fontsize=16,
                     y=1)
        plt.tight_layout()
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()

    def vehicles_scatter_plot(self, dO, dR, traffic):
        res = re.split(' ', self.window.selected_street_label.text())
        edge_id = res[1]
        veh = []
        with open(os.path.join(os.getcwd(), "Sumo", "osm.passenger.rou.xml"), 'r') as file:
            lines = file.readlines()
            for i in range(len(lines)):
                if edge_id in lines[i]:
                    r = re.split('\"', lines[i - 1])
                    veh.append(int(r[1]))

        dfO = dO[dO['tripinfo_id'].isin(veh)]
        dfR = dR[dR['tripinfo_id'].isin(veh)]
        dfO = dfO.set_index('tripinfo_id')
        dfR = dfR.set_index('tripinfo_id')
        dfO_aligned, dfR_aligned = dfO.align(dfR, fill_value=0)
        df = dfR_aligned - dfO_aligned
        print(dfO)
        value = 'Difference (in seconds) with and without deviations'
        if traffic == 'duration':
            value = 'Duration of the trips (s)'
        if traffic == 'routeLength':
            value = 'Route length (m)'
        if traffic == 'timeLoss':
            value = 'Time loss (s)'
        if traffic == 'waitingTime':
            value = 'Waiting time (s)'

        name = self.id_names_dict.get(edge_id)
        fig, ax = plt.subplots(figsize=(15, 10))
        sns.stripplot(data=df, orient="h")
        ax.set_ylabel('Vehicles', fontsize=30)
        ax.set_xlabel(value, fontsize=30)
        plt.xticks(rotation=90)
        plt.tick_params(labelleft=False)
        ax.tick_params(axis='x', which="both", bottom=False, top=False, labelsize=24, rotation=90)
        plt.subplots_adjust(top=0.9)
        plt.suptitle(traffic + ' of the vehicles that originally passed through \n' + edge_id + ' - ' + name,
                     fontsize=32)
        fig.subplots_adjust(wspace=0.26)
        plt.tight_layout()
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
        self.generate_png_outputs()

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
                list_time_intervals = time_intervals[:-1]
                values = []
                for key, value in self.interval_dic.items():
                    values.append(str(key))
                values = values[1:]
                name = self.id_names_dict.get(edge_id)
                sns.axes_style("ticks")
                fig, ax = plt.subplots(figsize=(12, 10))
                plt.plot(dfO.index, dfO.values, color='red', linewidth=2.5)
                plt.plot(dfR.index, dfR.values, color='blue', linewidth=2.5)
                plt.legend(labels=["Without deviations", "With deviations"], fontsize=18)

                ax.tick_params(axis='x', labelsize=14, rotation=90)
                ax.tick_params(axis='y', labelsize=14)
                ax.set_xlabel('Time intervals', fontsize=18)
                ax.set_xticks(list_time_intervals)
                ax.set_xticklabels(values)

                if traffic_indicator == "density":
                    inf = "vehicle density (veh/km)"
                elif traffic_indicator == "occupancy":
                    inf = "occupancy of the streets (%)"
                elif traffic_indicator == "timeLoss":
                    inf = "time loss due to driving slower than desired (s)"
                elif traffic_indicator == "traveltime":
                    inf = "travel time of the street (s))"
                elif traffic_indicator == "waitingTime":
                    inf = "waiting time (s)"
                elif traffic_indicator == "speed":
                    inf = "average speed (m/s)"
                elif traffic_indicator == "speedRelative":
                    inf = "speed relative (average speed / speed limit)"
                elif traffic_indicator == "sampledSeconds":
                    inf = "sampled seconds (veh/s)"
                ax.set_ylabel(inf, fontsize=18)
                plt.suptitle(name + ' (' + edge_id + ')', fontsize=26, x=0.5)
                plt.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.pdf"), bbox_inches='tight')
                plt.savefig(os.path.join(os.getcwd(), "Sumo", "outputs", "file.png"), bbox_inches='tight')
                self.generate_png_outputs()


    # def generate_pdf(self):
    #     pdf = FPDF()
    #     # Add a page
    #     pdf.add_page()
    #     # set style and size of font
    #     # that you want in the pdf
    #     pdf.set_font("Arial", size=15)
    #     # create a cell
    #     pdf.cell(200, 10, txt="GeeksforGeeks",
    #              ln=1, align='C')
    #     # add another cell
    #     pdf.cell(200, 10, txt="A Computer Science portal for geeks.",
    #              ln=2, align='C')
    #     # save the pdf with name .pdf
    #     pdf.output("GFG.pdf")

    def generate_png_outputs(self):
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

    def generate_maps_outputs(self):
        edgedata_O_out_csv = os.path.join(os.getcwd(), "Sumo", "outputs", "Ofile.out.csv")
        edgedata_R_out_csv = os.path.join(os.getcwd(), "Sumo", "outputs", "Rfile.out.csv")
        output_geojson_O_path = os.path.join(os.getcwd(), "qt_ui", "geoDFO.geojson")
        output_geojson_R_path = os.path.join(os.getcwd(), "qt_ui", "geoDFR.geojson")
        interval = self.window.comboBox_results_maps_time_interval.itemText(
            self.window.comboBox_results_time_interval.currentIndex())
        traffic_indicator = self.window.comboBox_results_maps_traffic_indicator.itemText(
            self.window.comboBox_results_maps_traffic_indicator.currentIndex())
        interval_seconds = self.interval_dic[interval]
        res = re.split("\'", str(interval_seconds))
        interval_sec = res[1]

        O1, O2, O3, O4, Ominim, Omaxim = self.mapLayout_output.map_to_geojson(edgedata_O_out_csv, output_geojson_O_path,
                                                                              interval_sec, traffic_indicator)
        R1, R2, R3, R4, Rminim, Rmaxim = self.mapLayout_output.map_to_geojson(edgedata_R_out_csv, output_geojson_R_path,
                                                                              interval_sec, traffic_indicator)

        minim = min(Ominim, Rminim)
        maxim = max(Omaxim, Rmaxim)

        self.mapLayout_output.redraw_folium_map(output_geojson_O_path, output_geojson_R_path, traffic_indicator, O1, O2,
                                                O3, O4, minim, maxim, self.closing)

    def read_json(self):
        self.id_names_dict = {}
        with open(os.path.join(os.getcwd(), "qt_ui", "bxl_Tulipe.geojson"), encoding='utf-8') as f:
            data = json.load(f)
        for feature in data['features']:
            self.id_names_dict.update({feature['properties'].get("id"): feature['properties'].get("name")})

    def Animation(self):
        self.loading_screen = LoadingScreen()
        QtCore.QTimer.singleShot(100, lambda: self.run_simulation())

    def execute_sumo(self, exp_id, args):
        end_time = int(self.starting_time_in_seconds) + int(self.time_total)
        # if self.p is None:  # No process running.
        #     self.message("Executing process")
        #     self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
        #     self.p.finished.connect(self.process_finished)  # Clean up once complete.
        #     self.p.start("sumo", ['-c Sumo\osm.sumocfg'])
        # self.threadpool = QThreadPool()
        # print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        # worker = Worker()
        # self.threadpool.start(worker)
        os.system("sumo -n " + os.path.join(os.getcwd(), "Sumo", "osm.net.xml.gz") + " -r " + os.path.join(os.getcwd(),
               "Sumo", "osm.passenger.trips.xml") + " -a " + os.path.join(os.getcwd(), "Sumo", "conf." + args + ".xml")
               + " -b " + self.starting_time_in_seconds + " -e " + str(end_time) + " --tripinfo-output " + os.path.join(
               os.getcwd(), "Sumo", "outputs", exp_id + "_" + args + ".veh.xml") + " --tripinfo-output.write-unfinished"
               + " --ignore-route-errors true --verbose false --duration-log.statistics "
               "true --no-step-log true")  # --fcd-output Sumo\\outputs\\" + exp_id + "_" + args + ".fcd.xml")

        if args == 'R':
            self.loading_screen.stopAnimation()

    def run_simulation(self):
        now = datetime.now()
        exp_id = now.strftime("%d_%m_%Y-%H_%M_%S")

        self.set_interval_list()
        self.generate_random_trips()
        self.write_conf_files(exp_id, 'O')
        self.execute_sumo(exp_id, 'O')
        print('Sumo Open finished')

        self.write_conf_files(exp_id, 'R')
        self.execute_sumo(exp_id, 'R')
        print('Sumo Close finished')

        self.write_exp_dict(exp_id)
        self.list_load_results()

    def write_conf_files(self, exp_id, args):
        list_edgeClosed = []
        for x in range(self.closed_street_model.rowCount()):
            r = re.split(' ', self.closed_street_model.item(x).text())
            list_edgeClosed.append(r[1])
        string_list_edgeClosed = ','.join(list_edgeClosed)
        f = open(os.path.join(os.getcwd(), "Sumo", "conf." + args + ".xml"), "w")
        f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        f.write(
            "<additional xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://sumo.dlr.de/xsd/additional_file.xsd\">\n")
        f.write("    <edgeData id=\"" + self.starting_time_in_seconds + "_to_" + str(int(self.starting_time_in_seconds) + int(self.interval_list[-1])) +
                "\" file=\"outputs\\" + exp_id + "_" + args + ".out.xml\" begin=\"" +
                self.starting_time_in_seconds + "\" end=\"" + str(int(self.starting_time_in_seconds) + int(self.interval_list[-1])) + "\" excludeEmpty=\"True\"/>\n")
        for i in range(len(self.interval_list) - 1):
            f.write("    <edgeData id=\"" + str(int(self.starting_time_in_seconds) + int(self.interval_list[i])) + "_to_" +
                    str(int(self.starting_time_in_seconds) + int(self.interval_list[i + 1])) + "\" file=\"outputs\\" + exp_id +
                        "_" + args + ".out.xml\" begin=\"" + str(int(self.starting_time_in_seconds) + int(self.interval_list[i])) +
                    "\" end=\"" + str(int(self.starting_time_in_seconds) + int(self.interval_list[i + 1])) + "\" excludeEmpty=\"True\"/>\n")
        f.write("    <!-- Rerouting -->\n")
        if len(list_edgeClosed) > 0:
            for edgeclose in list_edgeClosed:

                nextEdges_incoming = self.net.getEdge(edgeclose).getIncoming()
                #print(nextEdges_incoming)
                text = ""
                for dev_edge in nextEdges_incoming:
                    text = text + dev_edge.getID() + " "
                text = text[:-1]

                model = self.window.listView_current_simulation.model()
                for index in range(model.rowCount()):
                    item = model.item(index)
                    res = re.split("id: | - |:", item.text())
                    if res[1] == edgeclose:
                        s_end = res[-1]
                        m_end = res[-2]
                        h_end = res[-3]
                        s_beg = res[-5]
                        m_beg = res[-6]
                        h_beg = res[-7]
                        break

                b_time = (int(h_beg) * 3600) + (int(m_beg) * 60) + int(s_beg) + int(self.starting_time_in_seconds)
                e_time = (int(h_end) * 3600) + (int(m_end) * 60) + int(s_end) + int(self.starting_time_in_seconds)

                f.write("    <rerouter id=\"close_" + edgeclose + "\" edges=\"" + text + "\">\n")
                if args == 'R':
                    f.write("        <interval begin=\"" + str(b_time) + "\" end=\"" + str(e_time) + "\">\n")
                    f.write("            <closingReroute id=\"" + edgeclose + "\" disallow=\"all\"/>\n")
                    f.write("        </interval>\n")
                f.write("    </rerouter>\n")
        f.write("</additional>")
        f.close()

    def valueChanged_hours(self):
        h = self.window.spinBox_hours.text()
        m = self.window.spinBox_minutes.text()
        s = self.window.spinBox_seconds.text()
        hour = h + 'h:' + m + 'm:' + s + 's'
        self.window.label_simulation_duration.setText(hour)

        dt = self.window.timeedit_starting.dateTime()
        self.starting_time_hours_minutes_seconds = dt.toString(self.window.timeedit_starting.displayFormat())
        self.window.label_simulation_starting.setText(self.starting_time_hours_minutes_seconds)
        resu = re.split(' |:', self.starting_time_hours_minutes_seconds)
        starting_hours = resu[0]
        starting_minutes = resu[1]
        starting_seconds = resu[2]

        if len(self.w.closed_edges) != 0:
            model_event = self.window.listView_simulation.model()
            model_current = self.window.listView_current_simulation.model()
            for index in range(model_event.rowCount()):
                item = model_event.item(index)
                item2 = model_current.item(index)
                #print(item.text())
                item_name = re.split(' \n', item.text())
                res = re.split('from: |to: |:| -', item.text())
                s_end = res[-1]
                m_end = res[-2]
                h_end = res[-3]
                s_beg = res[-5]
                m_beg = res[-6]
                h_beg = res[-7]

                s_e = str(int(starting_seconds) + int(s))
                m_e = str(int(starting_minutes) + int(m))
                h_e = str(int(starting_hours) + int(h))
                s_b = str(int(starting_seconds) + int(s))
                m_b = str(int(starting_minutes) + int(m))
                h_b = str(int(starting_hours) + int(h))

                if int(h_e) < 10:
                    h_e = "0" + str(h_e)
                if int(m_e) < 10:
                    m_e = "0" + str(m_e)
                if int(s_e) < 10:
                    s_e = "0" + str(s_e)

                item.setText(item_name[
                                 0] + " \nClosing from: " + starting_hours + ":" + starting_minutes + ":" + starting_seconds + " - to: " + h_e + ":" + m_e + ":" + s_e)
                item2.setText(item_name[
                                  0] + " \nClosing from: " + starting_hours + ":" + starting_minutes + ":" + starting_seconds + " - to: " + h_e + ":" + m_e + ":" + s_e)

            self.window.spinBox_beginning_hours.setValue(int(starting_hours))
            self.window.spinBox_beginning_minutes.setValue(int(starting_minutes))
            self.window.spinBox_beginning_seconds.setValue(int(starting_seconds))
            self.window.spinBox_end_hours.setValue(int(h_e))
            self.window.spinBox_end_minutes.setValue(int(m_e))
            self.window.spinBox_end_seconds.setValue(int(s_e))


    def valueChanged_event(self):
        if len(self.w.closed_edges) != 0:
            h_beg = str(int(self.window.spinBox_beginning_hours.text()) + int(self.starting_hours))
            m_beg = self.window.spinBox_beginning_minutes.text()
            s_beg = self.window.spinBox_beginning_seconds.text()
            h_end = self.window.spinBox_end_hours.text()
            m_end = self.window.spinBox_end_minutes.text()
            s_end = self.window.spinBox_end_seconds.text()
            if int(h_beg) < 10:
                h_beg = "0" + str(h_beg)
            if int(m_beg) < 10:
                m_beg = "0" + str(m_beg)
            if int(s_beg) < 10:
                s_beg = "0" + str(s_beg)
            if int(h_end) < 10:
                h_end = "0" + str(h_end)
            if int(m_end) < 10:
                m_end = "0" + str(m_end)
            if int(s_end) < 10:
                s_end = "0" + str(s_end)

            for index in self.window.listView_simulation.selectedIndexes():
                item = self.window.listView_simulation.model().itemFromIndex(index)
                item_name = re.split(' \n', item.text())
                item.setText(item_name[
                                 0] + " \nClosing from: " + h_beg + ":" + m_beg + ":" + s_beg + " - to: " + h_end + ":" + m_end + ":" + s_end)

            model_event = self.window.listView_simulation.model()
            model_current = self.window.listView_current_simulation.model()
            for index in range(model_event.rowCount()):
                item = model_event.item(index)
                item2 = model_current.item(index)
                item2.setText(item.text())

    def valueChanged_starting(self):
        dt = self.window.timeedit_starting.dateTime()
        self.starting_time_hours_minutes_seconds = dt.toString(self.window.timeedit_starting.displayFormat())
        self.window.label_simulation_starting.setText(self.starting_time_hours_minutes_seconds)

        res = re.split(':', self.starting_time_hours_minutes_seconds)
        self.starting_hours = res[0]
        self.starting_minutes = res[1]
        self.starting_seconds = res[2]

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
            res = re.split('from: |to: |:| -', item.text())
            edge.append(edge_id)
            edge.append(res[-7])
            edge.append(res[-6])
            edge.append(res[-5])
            edge.append(res[-3])
            edge.append(res[-2])
            edge.append(res[-1])
            edge_times.append(edge)
        for street in self.w.closed_edges:
            closed_edges.append(street)
        self.existing_exp_dic[exp_id] = {
            'traffic': self.traffic_level_str,
            'starting_time': self.starting_time_in_seconds,
            "hours": self.time_hours,
            'minutes': self.time_minutes,
            'seconds': self.time_seconds,
            'intervals': self.intervals,
            'closed_roads': closed_edges,
            'events': edge_times
        }
        with open(os.path.join(os.getcwd(), "Sumo", "outputs", "data"), 'w') as file:
            file.write(json.dumps(self.existing_exp_dic))

    def read_exp_dict(self):
        file_size = os.path.getsize(os.path.join(os.getcwd(), "Sumo", "outputs", "data"))
        if file_size != 0:
            with open(os.path.join(os.getcwd(), "Sumo", "outputs", "data"), "r") as file:
                data = file.read()
                data = json.loads(data)
                self.existing_exp_dic = data

    def extractreroutedvehicles(self):
        traffic = self.window.comboBox_results_veh_traffic_indicator.itemText(
            self.window.comboBox_results_veh_traffic_indicator.currentIndex())

        traffic_indicator = "tripinfo_" + traffic

        for index in self.window.listView_load_results.selectedIndexes():
            item = self.window.listView_load_results.model().itemFromIndex(index)
            res = re.split(' ', item.text())
            loaded_exp_id = res[1]

        # # INPUT
        #time_range = range(0, 10000, 900)  # start,end, aggr frequency
        closed_edges_list = self.closing
        route_file_path = os.path.join(os.getcwd(), "Sumo", "osm.passenger.rou.xml")
        tripinfo_path_wroadworks = os.path.join(os.getcwd(), "Sumo", "outputs", loaded_exp_id+"_R.veh.xml")
        tripinfo_path = os.path.join(os.getcwd(), "Sumo", "outputs", loaded_exp_id+"_O.veh.xml")

        # output
        output_merged_tripinfo_csv_file =  os.path.join(os.getcwd(), "Sumo", "outputs", "vehout_joined.csv")
        # ------------------------------------------------------------------------------------------------

        veh_id = self.load_vehicles_from_file(closed_edges_list, route_file_path)
        reroute_df = self.extract_tripinfo_df(veh_id, tripinfo_path_wroadworks)
        noreroute_df = self.extract_tripinfo_df(veh_id, tripinfo_path)
        reroute_df.set_index("@id", inplace=True)
        noreroute_df.set_index("@id", inplace=True)

        reroute_df.columns = [colname + "_roadworks" for colname in reroute_df.columns]
        reroute_df.join(noreroute_df)
        joined = reroute_df.join(noreroute_df)
        joined = joined.dropna()
        joined.to_csv(output_merged_tripinfo_csv_file, sep=";")

        # maximize occurrences of positive values!
        duration_diff = joined['@duration'].astype('float') - joined['@duration_roadworks'].astype('float')
        perc_veh_late = len(list(filter(lambda v: v > 0, duration_diff.to_list()))) / duration_diff.size
        print('Percentage of late vehicles: {}'.format(perc_veh_late))

    def load_vehicles_from_file(self, closed_edges_id, routes_file):
        """
        Load the vehicles from a SUMO route file.
        :param closed_edges_id:
        :param routes_file: the xml FILE with the vehicle/route definitions
        :return:
        """
        veh_id_to_extract = []
        with open(routes_file) as fd_routes:
            doc = xmltodict.parse(fd_routes.read())
            vehicles_def = doc['routes']['vehicle']
            for vehicle_def in vehicles_def:
                edges_list = set(vehicle_def['route']['@edges'].split(' '))
                #print(edges_list)
                ints = edges_list.intersection(closed_edges_id)
                if len(ints) > 0:
                    veh_id_to_extract.append(vehicle_def['@id'])
        return veh_id_to_extract

    def extract_tripinfo_df(self, veh_id_list, tripinfo_fname):
        with open(tripinfo_fname, encoding='utf-8') as fd_tripinfo:
            doc = xmltodict.parse(fd_tripinfo.read())
            tripinfo = doc['tripinfos']['tripinfo']
            tripinfo_sub = list(filter(lambda ti: ti['@id'] in veh_id_list, tripinfo))
            return pd.DataFrame.from_dict(tripinfo_sub)

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
        self.fringe_factor = "30"
        self.starting_time_in_seconds = "0"
        self.starting_time_hours_minutes_seconds = None
        self.existing_exp_dic = {}
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
        self.read_exp_dict()
        self.p = None
        self.starting_hours = "0"
        self.starting_minutes = "0"
        self.starting_seconds = "0"

        self.window.openStreetButton = self.window.findChild(QPushButton, 'openStreetButton')
        self.window.openStreetButton.clicked.connect(self.on_open_road_button_click)
        self.window.closeStreetButton = self.window.findChild(QPushButton, 'closeStreetButton')
        self.window.closeStreetButton.clicked.connect(self.on_close_road_button_click)
        self.window.label_selected_road_from_map = self.window.findChild(QLabel, 'label_selected_road_from_map')
        self.window.closedStreetListView = self.window.findChild(QListView, 'closedStreetListView')
        self.closed_street_model = QStandardItemModel()
        self.window.closedStreetListView.setModel(self.closed_street_model)
        self.window.label_mlg = self.window.findChild(QLabel, 'label_mlg')
        self.window.label_mlg.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), "img", "mlg.png")))
        self.window.label_ulb = self.window.findChild(QLabel, 'label_ulb')
        self.window.label_ulb.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), "img", "ulb.png")))

        # Maps
        self.window.mapLayout = self.window.findChild(QVBoxLayout, 'mapLayout')
        self.window.MapLayoutsimulation = self.window.findChild(QVBoxLayout, 'mapLayout_simulation')
        self.window.mapLayout_output = self.window.findChild(QVBoxLayout, 'mapLayout_output')

        self.w = FoliumDisplay(geojson_path=os.path.join(os.getcwd(), "qt_ui", "bxl_Tulipe.geojson"))
        self.w.on_edge_selected.connect(self.edge_selected)

        self.w_simulation = FoliumSimulationDisplay(
            geojson_path=os.path.join(os.getcwd(), "qt_ui", "bxl_Tulipe.geojson"))
        self.mapLayout_output = FoliumDisplay2(geojson_path=os.path.join(os.getcwd(), "qt_ui", "geoDF.geojson"))
        self.mapLayout_output.on_edge_selected.connect(self.edge_selected_results)

        self.window.mapLayout.addWidget(self.w)
        self.window.MapLayoutsimulation.addWidget(self.w_simulation)
        self.window.mapLayout_output.addWidget(self.mapLayout_output)

        # Load Network
        self.net = self.w.net_handler.get_net()

        ##### Traffic Simulation
        self.window.timeedit_starting = self.window.findChild(QTimeEdit, 'timeEdit_starting')
        self.window.spinBox_hours = self.window.findChild(QSpinBox, 'spinBox_simulation_hours')
        self.window.spinBox_minutes = self.window.findChild(QSpinBox, 'spinBox_simulation_minutes')
        self.window.spinBox_seconds = self.window.findChild(QSpinBox, 'spinBox_simulation_seconds')
        self.window.spinBox_intervals = self.window.findChild(QSpinBox, 'spinBox_simulation_interval')
        self.window.radioButton_low_traffic = self.window.findChild(QRadioButton, 'radioButton_low_traffic')
        self.window.radioButton_medium_traffic = self.window.findChild(QRadioButton, 'radioButton_medium_traffic')
        self.window.radioButton_heavy_traffic = self.window.findChild(QRadioButton, "radioButton_heavy_traffic")
        self.window.run_simulation_button = self.window.findChild(QPushButton, 'run_simulation_button')
        self.window.run_simulation_button.clicked.connect(self.Animation)

        self.window.timeedit_starting.dateTimeChanged.connect(self.valueChanged_hours)
        self.window.spinBox_hours.valueChanged.connect(self.valueChanged_hours)
        self.window.spinBox_minutes.valueChanged.connect(self.valueChanged_hours)
        self.window.spinBox_seconds.valueChanged.connect(self.valueChanged_hours)
        self.window.spinBox_intervals.valueChanged.connect(self.valueChanged_intervals)
        self.window.radioButton_low_traffic.toggled.connect(self.valueChanged_traffic)
        self.window.radioButton_medium_traffic.toggled.connect(self.valueChanged_traffic)
        self.window.radioButton_heavy_traffic.toggled.connect(self.valueChanged_traffic)

        #self.valueChanged_starting()
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
        self.window.label_simulation_starting = self.window.findChild(QLabel, 'label_simulation_starting')
        self.window.label_simulation_traffic = self.window.findChild(QLabel, 'label_simulation_traffic')
        self.window.label_simulation_intervals = self.window.findChild(QLabel, 'label_simulation_intervals')
        self.window.label_simulation_duration = self.window.findChild(QLabel, 'label_simulation_duration')
        self.window.listView_current_simulation = self.window.findChild(QListView, 'listView_current_simulation')
        self.listView_current_simulation_model = QStandardItemModel()
        self.window.listView_current_simulation.setModel(self.listView_current_simulation_model)

        self.window.label_mlg_2 = self.window.findChild(QLabel, 'label_mlg_3')
        self.window.label_mlg_2.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), "img", "mlg.png")))
        self.window.label_ulb_2 = self.window.findChild(QLabel, 'label_ulb_3')
        self.window.label_ulb_2.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), "img", "ulb.png")))

        ##### Results
        # Select the simulation
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

        ##Maps
        self.window.comboBox_results_maps_time_interval = self.window.findChild(QComboBox,
                                                                                'comboBox_results_maps_time_interval')
        self.window.comboBox_results_maps_traffic_indicator = self.window.findChild(QComboBox,
                                                                                    'comboBox_results_maps_traffic_indicator')
        self.window.generate_map_button = self.window.findChild(QPushButton, 'generate_map_button')
        self.window.generate_map_button.clicked.connect(self.generate_maps_outputs)

        ##Output
        # Results by street
        self.window.comboBox_results_by_street_traffic_indicator = self.window.findChild(QComboBox,
                                                                                         'comboBox_results_by_street_traffic_indicator')
        self.window.selected_street_label = self.window.findChild(QLabel, 'selected_street_label')
        self.window.generate_street_outputs_button = self.window.findChild(QPushButton,
                                                                           'generate_street_outputs_button')
        self.window.generate_street_outputs_button.clicked.connect(self.generate_streets_outputs)

        # Groups
        self.window.comboBox_results_veh_figure = self.window.findChild(QComboBox, 'comboBox_results_veh_figure')
        self.window.comboBox_results_veh_traffic_indicator = self.window.findChild(QComboBox,
                                                                                   'comboBox_results_veh_traffic_indicator')
        self.window.generate_vehicles_button = self.window.findChild(QPushButton, 'generate_vehicles_button')
        self.window.generate_vehicles_button.clicked.connect(self.plot_vehicles)

        # Integrated results
        self.window.comboBox_results_time_interval = self.window.findChild(QComboBox, 'comboBox_results_time_interval')
        self.window.comboBox_results_traffic_indicator = self.window.findChild(QComboBox,
                                                                               'comboBox_results_traffic_indicator')
        self.window.comboBox_results_figures = self.window.findChild(QComboBox, 'comboBox_results_figures')
        self.window.generate_integrate_outputs_button = self.window.findChild(QPushButton,
                                                                              'generate_integrated_outputs_button')
        self.window.generate_integrate_outputs_button.clicked.connect(self.generate_integrated_outputs)

        # Plots
        self.window.export_pdf_button = self.window.findChild(QPushButton, 'export_pdf_button')
        self.window.export_pdf_button.clicked.connect(self.export_pdf)
        self.window.label_plot = self.window.findChild(QLabel, 'label_plot')

        self.window.label_mlg_2 = self.window.findChild(QLabel, 'label_mlg_2')
        self.window.label_mlg_2.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), "img", "mlg.png")))
        self.window.label_ulb_2 = self.window.findChild(QLabel, 'label_ulb_2')
        self.window.label_ulb_2.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), "img", "ulb.png")))
        self.window.without_label = self.window.findChild(QLabel, 'without_label')
        self.window.without_label.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), "img", "Without.png")))
        self.window.without_label = self.window.findChild(QLabel, 'with_label')
        self.window.without_label.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), "img", "With.png")))

        self.list_load_results()

    def handle_clicked(self):
        for index in self.window.listView_load_results.selectedIndexes():
            item = self.window.listView_load_results.model().itemFromIndex(index)
            self.managed_result_model.clear()
            self.managed_result_model.appendRow(QStandardItem(item.text()))

    def show(self):
        self.window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
