import io
import json
import os

import branca
import folium
import folium.plugins
import sumolib
import geopandas as gpd
import pandas as pd
import fiona  # don't remove please

from PySide6.QtCore import Slot, QObject, Signal
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy
from branca.element import Element, JavascriptLink, CssLink
import branca.colormap as cm

"""
taken from: https://stackoverflow.com/questions/68433171/select-points-from-folium-map-in-a-pyqt5-widget
"""

class SUMONetworkHandler(QObject):
    net = None
    on_get_edge_id = Signal(str)  # NOTE: Signals MUST BE class variables to work
    """see https://forum.qt.io/topic/152002/pyside6-signal-to-slot-in-different-class/5"""

    def __init__(self, net_path):
        super(SUMONetworkHandler, self).__init__()
        self.net = sumolib.net.readNet(net_path)

    def get_edge_id(self, lon, lat, zoom_level):
        x, y = self.net.convertLonLat2XY(lon, lat)
        edges = self.net.getNeighboringEdges(x, y, 100)
        # pick the closest edge
        if len(edges) > 0:
            distancesAndEdges = sorted([(dist, edge) for edge, dist in edges], key=lambda x: x[0])
            dist, closestEdge = distancesAndEdges[0]
            self.on_get_edge_id.emit(closestEdge.getID())

    def get_net(self):
        return self.net

class WebEnginePage(QWebEnginePage):
    net_handler = None
    on_edge_selected = Signal(str)
    on_map_clicked = Signal(float, float, int)

    def __init__(self, parent, sumo_net_handler):
        super(WebEnginePage, self).__init__(parent)
        self.parent = parent
        self.net_handler = sumo_net_handler
        self.net_handler.on_get_edge_id.connect(self.edge_selected)

    @Slot(str)
    def edge_selected(self, edge_id):
        self.on_edge_selected.emit(edge_id)

    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        print(msg)  # Check js errors
        # dd = json.loads(msg)
        if 'lat' in msg:
            dd = json.loads(msg)
            # dd = json.loads(msg)["coordinates"]
            self.net_handler.get_edge_id(dd['lng'], dd['lat'], dd['zoom'])
            self.on_map_clicked.emit(dd['lat'], dd['lng'], dd['zoom'])

class FoliumDisplay2(QWidget):
    geojson_path = ""
    on_edge_selected = Signal(str)

    def redraw_folium_map(self, geojson_pathO, geojson_pathR, traffic_indicator, p1, p2, p3, p4, minim, maxim, closing):
        self.folium_map = folium.plugins.DualMap(zoom_start=self.zoom_level, min_zoom=14,
                                                 tiles='cartodbdark_matter',
                                                 location=(self.lon, self.lat), layout="vertical")
        # Add Custom JS to folium map
        self.folium_map = self.add_geojson_map1(self.folium_map, geojson_pathO, traffic_indicator, p1, p2, p3, p4, minim, maxim)
        self.folium_map = self.add_geojson_map2(self.folium_map, geojson_pathR, traffic_indicator, p1, p2, p3, p4, minim, maxim, closing)

        self.folium_map = self.onClickfunctm1(self.folium_map, self.elem1)
        self.folium_map = self.onClickfunctm2(self.folium_map, self.elem2)

        # save map data to data object
        data = io.BytesIO()
        self.folium_map.save(data, close_file=False)
        self.webView.setHtml(data.getvalue().decode())  # give html of folium map to webengine
        # print(data.getvalue().decode())
        return data

    def draw_folium_map(self, ):
        self.folium_map = folium.plugins.DualMap(zoom_start=self.zoom_level, location=(self.lon, self.lat),
                                                 tiles='cartodbpositron',
                                                 layout="vertical", min_zoom=14)#, dragging=False)
        #folium.TileLayer('cartodbpositron').add_to(self.folium_map)
        # save map data to data object
        data = io.BytesIO()
        self.folium_map.save(data, close_file=False)
        self.webView.setHtml(data.getvalue().decode())  # give html of folium map to webengine
        return data

    def __init__(self, geojson_path):
        super().__init__()
        self.folium_map = None
        self.map_name = None
        self.lon = 50.83421264776447
        self.lat = 4.366035461425782
        self.zoom_level = 15

        self.closed_edges = set()
        self.geojson_path = geojson_path
        self.setWindowTitle('Tulipe')
        self.window_width, self.window_height = 2000, 2000
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.net_handler = SUMONetworkHandler(os.path.join(os.getcwd(), "Sumo", "osm.net.xml.gz"))

        self.webView = QWebEngineView()  # start web engine
        page = WebEnginePage(self, self.net_handler)
        page.on_edge_selected.connect(self.edge_selected)
        page.on_map_clicked.connect(self.map_clicked)
        self.webView.setPage(page)

        self.draw_folium_map()
        layout.addWidget(self.webView)

    def get_Map_name(self):
        return self.folium_map.get_name()

    @Slot(float, float, int)
    def map_clicked(self, lon, lat, zoom_level):
        self.lon = lon
        self.lat = lat
        self.zoom_level = zoom_level

    @Slot(str)
    def edge_selected(self, edge_id):
        self.on_edge_selected.emit(edge_id)

    def draw_marker(self, map):
        latitude = 50.83421264776447
        longitude = 4.366035461425782
        folium.Marker(
            location=[latitude, longitude],
            tooltip="Click me!",
            popup="Mt. Hood Meadows",
        ).add_to(map.m1)
        return map

    def add_geojson_map1(self, map, fname, traffic_indicator, p1, p2, p3, p4, minim, maxim):
        traffic = "edge_" + traffic_indicator
        with open(fname) as fO:
            dataO = json.load(fO)
        popup = folium.GeoJsonPopup(fields=["id", "{}".format(traffic)], aliases=['id:', "{}:".format(traffic_indicator)])

        color_map = ["#0F9D58", "#fff757", "#fbbc09", "#E94335", "#822F2B"]
        index = [minim, p1, p2, p3, p4, maxim]

        step = cm.StepColormap(color_map,
                               vmin=minim, vmax=maxim,
                               index=index,
                               caption=traffic_indicator)

        linear1 = cm.LinearColormap(["#0F9D58", "#fff757", "#fbbc09", "#E94335", "#822F2B"],
                                    vmin=minim, vmax=maxim,
                                    tick_labels=[minim, maxim])

        if traffic_indicator == "density":
            linear1.caption = "vehicle density (veh/km)"
        elif traffic_indicator == "occupancy":
            linear1.caption = "occupancy of the streets (%)"
        elif traffic_indicator == "timeLoss":
            linear1.caption = "time loss due to driving slower than desired (s)"
        elif traffic_indicator == "traveltime":
            linear1.caption = "travel time of the street (s))"
        elif traffic_indicator == "waitingTime":
            linear1.caption = "waiting time (s)"
        elif traffic_indicator == "speed":
            linear1.caption = "average speed (m/s)"
        elif traffic_indicator == "speedRelative":
            linear1.caption = "speed relative (average speed / speed limit)"
        elif traffic_indicator == "sampledSeconds":
            linear1.caption = "sampled seconds (veh/s)"

        if traffic == "edge_speed" or traffic == "edge_speedRelative":
            step.colors.reverse()
            linear1.colors.reverse()

        elem = folium.GeoJson(dataO,
                              highlight_function=lambda feature: {"color": "#E8E8E8"},
                              tooltip=folium.features.GeoJsonTooltip(
                                  fields=['id'],
                                  aliases=['id:'],
                              ),
                              popup=popup,
                              popup_keep_highlighted=True,
                              style_function=lambda feature: {
                                  "color": step(feature['properties']['{}'.format(traffic)]),
                                  "weight": 4
                              }
                              )
        #folium.TileLayer('cartodbpositron').add_to(map.m1)
        map.m1.add_child(linear1)
        ##https://github.com/python-visualization/branca/issues/91
        svg_style = '<style>svg#legend {background-color: white;}</style>'
        map.m1.get_root().header.add_child(folium.Element(svg_style))
        elem.add_to(map.m1)
        self.elem1 = elem
        return map

    def onClickfunctm1(self, map, elem):
        my_js = f"""        {self.elem1.get_name()}.on("click",
                                 function (e) {{
                                    var data = e.latlng;
                                    data.zoom = {map.m1.get_name()}.getZoom()
                                    var data_str = `{{"coordinates": ${{JSON.stringify(data)}}}}`;
                                    console.log(JSON.stringify(data));}});"""

        e = Element(my_js)
        html = elem.get_root()
        html.script.get_root().render()
        # Insert new element or custom JS
        html.script._children[e.get_name()] = e
        return map

    def add_geojson_map2(self, map, fname, traffic_indicator, p1, p2, p3, p4, minim, maxim, closing):
        traffic = "edge_" + traffic_indicator
        with open(fname) as fR:
            dataR = json.load(fR)
        popup = folium.GeoJsonPopup(fields=["id", "{}".format(traffic)], aliases=['id:', "{}:".format(traffic_indicator)])

        color_map = ["#0F9D58", "#fff757", "#fbbc09", "#E94335", "#822F2B"]
        index = [minim, p1, p2, p3, p4, maxim]

        step = cm.StepColormap(color_map,
                               vmin=minim, vmax=maxim,
                               index=index,
                               caption=traffic_indicator)

        if traffic == "edge_speed" or traffic == "edge_speedRelative":
            step.colors.reverse()

        #folium.TileLayer('cartodbdark_matter').add_to(map)
        elem = folium.GeoJson(dataR,
                              highlight_function=lambda feature: {"color": "#00FFF7"},
                              tooltip=folium.features.GeoJsonTooltip(
                                  fields=['id'],
                                  aliases=['id:'],
                              ),
                              popup=popup,
                              popup_keep_highlighted=True,
                              style_function=lambda feature: {
                                  "color": step(feature['properties']['{}'.format(traffic)]) if feature['properties']['id'] not in closing else "#D3D3D3",
                                  "weight": 4
                              }
                              )
        #folium.TileLayer('cartodbpositron').add_to(map.m2)
        elem.add_to(map.m2)
        self.elem2 = elem
        return map

    def onClickfunctm2(self, map, elem):
        #print(self.elem2.get_name())
        my_js = f"""        {self.elem2.get_name()}.on("click",
                                 function(e) {{
                                    var data = e.latlng;
                                    data.zoom = {map.m2.get_name()}.getZoom();
                                    var data_str = `{{"coordinates": ${{JSON.stringify(data)}}}}`;
                                    console.log(JSON.stringify(data));
                                    }});

                    //var popup2 = L.popup();
                    //{self.elem2.get_name()}.on('click', 
                    //        function(e) {{  
                    //            popup2.setLatLng(e.latlng)
                    //                  .setContent("Latitude: " + e.latlng)
                    //                  .openOn({self.elem1.get_name()});
                    //            }});
"""

        e = Element(my_js)
        html = elem.get_root()
        html.script.get_root().render()
        # Insert new element or custom JS
        html.script._children[e.get_name()] = e
        return map

    def handleConsoleMessage(self, msg):
        data = json.loads(msg)
        lat = data['coordinates']['lat']
        lng = data['coordinates']['lng']
        coords = f"latitude: {lat} longitude: {lng}"
        self.label.setText(coords)

    def map_to_geojson(self, edgedata_out_csv, output_geojson_path, interval, traffic_indicator):
        """
        Embed the edgedata output values into the network and export the network in a GEOJSON file

        :param road_net_path: the PATH to the SUMO road network XML
        :param edgedata_out_xml: the PATH to the edgedata output XML file
        :param output_geojson_path: the PATH to the output geojson file
        :return:
        """
        # step 1: net to geojson
        import tempfile
        traffic = "edge_" + traffic_indicator
        tempf_geojson = os.path.join(os.getcwd(), "qt_ui", "tempf.geojson") #"C:\\Users\moise\PycharmProjects\pythonProjectDavide\Sumo\osm.net.xml\\tempf.geojson"
        #print(tempf_geojson)
        # tempf_geojson = tempfile.NamedTemporaryFile(suffix='.geojson')
        net2geojson_command = "python \"" + os.path.join(os.environ["SUMO_TOOL"], "net", "net2geojson.py\"") + " -n {} -o {}".format(os.path.join(os.getcwd(), "Sumo", "osm.net.xml.gz"), tempf_geojson)
        os.system(net2geojson_command)
        net_gdf = gpd.read_file(tempf_geojson)
        net_gdf['index'] = net_gdf['id']
        net_gdf = net_gdf.set_index('index')

        edgedata_df = pd.read_csv(edgedata_out_csv, sep=";")

        edgedata_df = edgedata_df.loc[edgedata_df['interval_id'] == interval]
        edgedata_df = edgedata_df.loc[:,
                      ['edge_id',
                       traffic]]
        edgedata_df = edgedata_df.set_index('edge_id').fillna(0)
        df3 = net_gdf.join(edgedata_df).fillna(0)
        p1 = df3[traffic].quantile(0.25)
        p2 = df3[traffic].quantile(0.5)
        p3 = df3[traffic].quantile(0.75)
        p4 = df3[traffic].quantile(0.9)
        minim = df3[traffic].min()
        maxim = df3[traffic].max()
        df3.to_file(output_geojson_path)
        return p1, p2, p3, p4, minim, maxim
