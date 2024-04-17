import io
import json
import os
import folium
import sumolib
from PySide6.QtCore import Slot, QObject, Signal

from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy
from branca.element import Element
import branca.colormap as cm

"""
taken from: https://stackoverflow.com/questions/68433171/select-points-from-folium-map-in-a-pyqt5-widget
"""


class WebEnginePage(QWebEnginePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        print(msg)  # Check js errors
        if 'coordinates' in msg:
            self.parent.handleConsoleMessage(msg)


class FoliumOutputDisplay(QWidget):
    geojson_path = ""

    def redraw_folium_map(self, ):
        self.folium_map = folium.Map(zoom_start=self.zoom_level, location=(self.lon, self.lat))

        # Add Custom JS to folium map
        self.folium_map = self.add_geojson(self.folium_map, self.geojson_path)

        # save map data to data object
        data = io.BytesIO()
        self.folium_map.save(data, close_file=False)
        self.webView.setHtml(data.getvalue().decode())  # give html of folium map to webengine
        return data

    def draw_folium_map(self, ):
        self.folium_map = folium.Map(zoom_start=self.zoom_level, location=(self.lon, self.lat))

        # Add Custom JS to folium map
        #self.folium_map = self.add_geojson(self.folium_map, self.geojson_path)

        # save map data to data object
        data = io.BytesIO()
        self.folium_map.save(data, close_file=False)
        self.webView.setHtml(data.getvalue().decode())  # give html of folium map to webengine
        return data

    def __init__(self, geojson_path):
        super().__init__()
        self.lon = 50.83421264776447
        self.lat = 4.366035461425782
        self.zoom_level = 14

        self.closed_edges = set()
        self.geojson_path = geojson_path
        self.setWindowTitle('Tulipe')
        self.window_width, self.window_height = 2000, 2000
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.webView = QWebEngineView()  # start web engine
        page = WebEnginePage(self)
        self.webView.setPage(page)

        self.draw_folium_map()
        layout.addWidget(self.webView)

    def add_geojson(self, map, fname):
        with open(fname) as f:
            data = json.load(f)
        popup = folium.GeoJsonPopup(fields=["id","occupancy"])

        step = cm.StepColormap(["green", "yellow", "red"], vmin=0, vmax=1, index=[0.1, 0.3, 0.7, 1],
                               caption="step")

        folium.TileLayer('cartodbdark_matter').add_to(map)
        elem = folium.GeoJson(data,
                              highlight_function=lambda feature: {"color": "orange"},
                              tooltip=folium.features.GeoJsonTooltip(
                                  fields=['id'],
                                  aliases=['Edge ID:'],
                              ),
                              popup=popup,
                              popup_keep_highlighted=True,
                              style_function=lambda feature: {
                                  "color": step(feature['properties']['occupancy']),
                                  "weight": 4
                                  # "dashArray": "5, 5",
                              }
                              )
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
