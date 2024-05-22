import io
import json
import os
import folium
import sumolib


from PySide6.QtCore import Slot, QObject, Signal

from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy
from branca.element import Element, JavascriptLink

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
        #dd = json.loads(msg)
        if 'lat' in msg:
            dd = json.loads(msg)
            # dd = json.loads(msg)["coordinates"]
            self.net_handler.get_edge_id(dd['lng'], dd['lat'], dd['zoom'])
            self.on_map_clicked.emit(dd['lat'], dd['lng'], dd['zoom'])


class FoliumDisplay(QWidget):
    geojson_path = ""
    on_edge_selected = Signal(str)

    def redraw_folium_map(self, ):
        self.folium_map = folium.Map(zoom_start=self.zoom_level, min_zoom=14, location=(self.lon, self.lat),
                                     tiles='cartodbpositron')
        self.folium_map.get_root().header.add_child(
            JavascriptLink('https://github.com/jieter/Leaflet.Sync/L.Map.Sync.js'))
        # Add Custom JS to folium map
        self.folium_map = self.add_geojson(self.folium_map, self.geojson_path)
        # save map data to data object

        data = io.BytesIO()
        self.folium_map.save(data, close_file=False)
        self.webView.setHtml(data.getvalue().decode())  # give html of folium map to webengine
        #print(data.getvalue().decode())
        return data

    def __init__(self, geojson_path):
        super().__init__()
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
        self.net_handler = SUMONetworkHandler(os.path.join(os.getcwd(), "Sumo", "osm.net.xml.gz")) #'C:\\Users\moise\PycharmProjects\pythonProjectDavide\Sumo\osm.net.xml\osm.net.xml') #os.environ['BXL_NET'])

        self.webView = QWebEngineView()  # start web engine
        page = WebEnginePage(self, self.net_handler)
        page.on_edge_selected.connect(self.edge_selected)
        page.on_map_clicked.connect(self.map_clicked)
        self.webView.setPage(page)

        self.redraw_folium_map()
        #folium.TileLayer('Mapbox Control Room').add_to(self.folium_map)
        layout.addWidget(self.webView)

    @Slot(float, float, int)
    def map_clicked(self, lon, lat, zoom_level):
        self.lon = lon
        self.lat = lat
        self.zoom_level = zoom_level

    @Slot(str)
    def edge_selected(self, edge_id):
        self.on_edge_selected.emit(edge_id)

    def add_geojson(self, map, fname):
        with open(fname, encoding='utf-8') as f:
            data = json.load(f)
        popup = folium.GeoJsonPopup(fields=["id", "name"])
        elem = folium.GeoJson(data,
                              highlight_function=lambda feature: {"color": "orange"},
                              tooltip=folium.features.GeoJsonTooltip(
                                  fields=['id', 'name'],
                                  aliases=['Edge ID:', 'Name:'],
                              ),
                              popup=popup,
                              popup_keep_highlighted=True,
                              style_function=lambda feature: {
                                  "color": "#1a73e8" if feature['properties']['id'] not in self.closed_edges else "red",
                                  "weight": 4 if feature['properties']['id'] not in self.closed_edges else 5
                                  # "dashArray": "5, 5",
                              }
                              )
        #folium.TileLayer('cartodbpositron').add_to(map)
        elem.add_to(map)
        my_js = f"""{elem.get_name()}.on("click",
                                 function (e) {{
                                    var data = e.latlng;
                                    data.zoom = {map.get_name()}.getZoom()
                                    var data_str = `{{"coordinates": ${{JSON.stringify(data)}}}}`;
                                    console.log(JSON.stringify(data));
                                    }});"""

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

    def add_customjs(self, map):
        #map.get_root().html.add_child(JavascriptLink('./L.Map.Sync.js'))

        # my_js = f"""{map.get_name()}.on("click",
        # #          function(e) {{
        # #             var data = e.latlng;
        # #             data.zoom = {map.get_name()}.getZoom()
        # #             var data_str = `{{"coordinates": ${{JSON.stringify(data)}}}}`;
        # #             console.log(JSON.stringify(data));
        #             }});"""
        # #
        # e = Element(my_js)
        # html = map.get_root()
        # html.script.get_root().render()
        # # Insert new element or custom JS
        # html.script._children[e.get_name()] = e
        return map