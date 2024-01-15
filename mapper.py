import pandas as pd
import os
import regex as re
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import numpy as np
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point
from os.path import exists
import warnings
import requests
import sys
import plotly.io as pio
from zipfile import ZipFile
from array import array
from pandas import json_normalize
import argparse


# Configuration for the map being output
map_settings = {
    "nat_toggle": True,  # show specific countries or world
    "nat_label_toggle": False,  # show national labels
    "subnat_toggle": False,  # show subnational regions (provinces, states, eg)
    "subnat_label_toggle": False,  # show subnat labels
    "subnat_highlight_toggle": False,  # specify and highlight a subnat
    "city_toggle": True,  # show cities
    "chloro_toggle": False,  # apply a chloro map
    "csv_toggle": False,  # apply data from a csv file
    "irregular_marker_toggle": False,  # map irregular features onto the map using custom lon/lats (csv or otherwise)
    "irregular_feature_toggle": False,  # rue if exists(Path(__file__).parent / 'features/feature_1.geojson') else False #Draw custom highways, etc.; checks features directory
}

map_content = {
    "country_list": [],  # Countries to be displayed
    # Format: [city name, label position]
    "city_list": [],
    # Note: Works with either the name of a province or the name of a country, in which case all provinces of said country will be mapped.
    "subnat_list": [],
    # Format: [label, direction, extent, size_override (0 for unchanged)] / Direction: 'top-right', 'bottom-right', 'right', 'top', etc. / Size: multiplier for adjustment (eg 2 = 2x)
    # Note: For more finicky adjustments run the same country through the list twice.
    "label_adjusts": [[]],
    # CSV list - nats and subnats for which the csv data will apply to.
    "csv_list": [],
    # Irregular features comes in dict form for easy importing of outside data sources. / Format as list of dictionaries with name/lon/lat/position (label)
    "irregular_markers": [],
}

map_styling = {
    "background_color": "#ede7f1",
    "nat_border_opacity": 1,
    "nat_border_width": 1,
    "nat_border_color": "#282828",
    "subnat_border_opacity": 0.5,
    "subnat_border_width": 0.5,
    "subnat_border_color": "#282828",
    # CITIES / MARKERS
    "city_text_size": 20,
    "city_text_color": "#241f20",
    "marker_size": 15,
    "marker_color": "#241f20",
    # FEATURES
    "feature_color": "rgba(202, 52, 51, 0.5)",
    "feature_fill_opacity": 0.25,
    "feature_border_opacity": 0.75,
    "feature_border_width": 1,
    "feature_border_color": "#282828",
    # LABELS
    "nat_label_opacity": 0.7,
    "nat_label_size": 30,
    "nat_label_color": "#282828",
    "subnat_label_opacity": 0.5,
    "subnat_label_size": 35,
    "subnat_label_color": "#282828",
}


class MapBuilder:
    def __init__(self, token: str, settings: dict, content: dict, styling: dict):
        # Mapbox token from environmental variable
        self.token = token
        self.config = settings
        self.content = content
        self.styling = styling

        # Label DF (For all labeled features including nat, subnat, cities, irregular features)
        self.label_df = pd.DataFrame(
            columns=["name", "centroid", "size", "position", "code", "type"]
        )

        # Load Natural Earth data (serves as template for custom maps)
        map_path = Path(__file__).parent / "maps/"
        city_db_path = Path(__file__).parent / "city_db/"
        with open(
            map_path / "naturalearth.geojson", "r", encoding="utf-8"
        ) as geojson_file:
            self.countries = json.load(geojson_file)
        with open(
            map_path / "naturalearth_countries.geojson", "r", encoding="utf-8"
        ) as geojson_file:
            self.borders = json.load(geojson_file)

        # Store a collection of the specific geojson data we're using so as to avoid re-iterating the NaturalEarth set.
        init_slice = []
        for i in self.borders["features"]:
            if i["properties"]["ADMIN"] in self.content["country_list"]:
                init_slice.append(i)
        self.nat_db = {"type": ["FeatureCollection"], "features": init_slice}

        init_slice = []
        for i in self.countries["features"]:
            if i["properties"]["admin"] in self.content["country_list"]:
                init_slice.append(i)
        self.subnat_db = {"type": ["FeatureCollection"], "features": init_slice}

        # Loads geojsons from the features directory
        if self.config["irregular_feature_toggle"] == True:
            self.features = []
            files = os.listdir(Path(__file__).parent / "features")
            for x in files:
                if "feature_" in x:
                    with open(
                        Path(__file__).parent / f"features/{x}", "r", encoding="utf-8"
                    ) as geojson_file:
                        self.features.append(json.load(geojson_file))

        # Loads csv file(s) from csv directory
        if self.config["chloro_toggle"] == True:
            self.csvs = []
            files = os.listdir(Path(__file__).parent / "csv")
            for x in files:
                if "csv_" in x:
                    with open(
                        Path(__file__).parent / f"csv/{x}", "r", encoding="utf-8-sig"
                    ) as csv_file:
                        self.csvs.append(pd.read_csv(csv_file, sep=","))
            # Loads geojson file(s) from features directory
            self.geojsons = []
            geoj_path = Path(__file__).parent / "features"
            files = os.listdir(geoj_path)
            for x in files:
                if "geojson_" in x:
                    with open(
                        geoj_path / "geojson_1.geojson", "r", encoding="utf-8"
                    ) as geojson_file:
                        self.geojsons.append(json.load(geojson_file))

        # CITY DATA
        def city_data_builder():
            def _iso_code_grabber():
                """Initializes necessary data for mapping of cities"""
                # List of ISO codes to be used for mapping cities and notable locations (city_list)
                self.iso_list = pd.read_csv(
                    city_db_path / "cities.csv", encoding="utf-8"
                )
                self.iso_codes = []

                # Get ISO codes if cities being displayed
                if (
                    self.config["city_toggle"] == True
                    and self.config["nat_toggle"] == True
                ):
                    for column, row in self.iso_list.iterrows():
                        if row["Name"] in self.content["country_list"]:
                            self.iso_codes.append(row["Code"])

            def _city_loader():
                """Checks for local municipal geodata and if missing downloads it. Lean=True to save load times by only importing major settlements"""

                def __city_db_formatter(input_csv):
                    """Formats and loads municipal data as a full df. Returns feature class P (populated places)"""
                    df = pd.read_csv(
                        input_csv,
                        encoding="utf-8",
                        sep="\t",
                        low_memory=False,
                        names=columns,
                    )
                    df = df.drop(
                        columns=[
                            "geonameid",
                            "elevation",
                            "dem",
                            "timezone",
                            "modification date",
                            "admin4 code",
                        ]
                    )
                    return df.loc[df["feature class"] == "P"]

                def __city_extractor(input_df):
                    """Gets the specific cities required and saves them to the class method"""
                    city_list = [x[0] for x in self.content["city_list"]]
                    input_df = input_df[input_df["asciiname"].isin(city_list)]
                    return input_df

                columns = [
                    "geonameid",
                    "name",
                    "asciiname",
                    "alternatenames",
                    "latitude",
                    "longitude",
                    "feature class",
                    "feature code",
                    "country code",
                    "cc2",
                    "admin1 code",
                    "admin2 code",
                    "admin3 code",
                    "admin4 code",
                    "population",
                    "elevation",
                    "dem",
                    "timezone",
                    "modification date",
                ]

                out_df = pd.DataFrame(columns=columns).drop(
                    columns=[
                        "geonameid",
                        "elevation",
                        "dem",
                        "timezone",
                        "modification date",
                        "admin4 code",
                    ]
                )

                for i in range(0, len(self.iso_codes)):
                    fname = str(self.iso_codes[i]) + ".zip"
                    save_dir = city_db_path / self.iso_codes[i]
                    full_path = save_dir / fname
                    # Check for pre-existing dictionary
                    if exists(save_dir):
                        pass
                    # Download data if not found
                    else:
                        download_url = (
                            "https://download.geonames.org/export/dump/"
                            + str(self.iso_codes[i])
                            + ".zip"
                        )
                        save_dir = city_db_path / self.iso_codes[i]
                        os.mkdir(city_db_path / self.iso_codes[i])

                        # Download the zip
                        r = requests.get(download_url, stream=True)
                        with open(full_path, "wb") as file:
                            for chunk in r.iter_content(chunk_size=128):
                                file.write(chunk)

                        # Extract the zip
                        with ZipFile(save_dir / fname, "r") as zf:
                            zf.extractall(save_dir)
                        os.remove(save_dir / fname)

                    # Extract and instantiate specific city data in content settings
                    c_fname = str(self.iso_codes[i]) + ".txt"
                    entry = __city_extractor(__city_db_formatter(save_dir / c_fname))
                    if entry.shape[0] > 0:
                        out_df = pd.concat([out_df, entry], axis=0)
                    else:
                        pass

                return out_df

            # Initialize city data
            _iso_code_grabber()
            self.city_db = (
                _city_loader()
            )  # This will be setting the class-instantiated city db (for later plotting)

        # Initialize relevant functions
        if self.config["city_toggle"] == True:
            city_data_builder()

    def draw_map(self, in_df=None, in_geo=None):
        """Main function to output final map"""

        def _lat_cruncher(input: json):
            """Converts geojson to list of lon/lat"""
            points = []
            out_list = []
            for feature in input["features"]:
                if feature["geometry"]["type"] == "Polygon":
                    points.extend(feature["geometry"]["coordinates"][0])
                    points.append([None, None])  # Marks the end of a polygon
                elif feature["geometry"]["type"] == "MultiPolygon":
                    for polyg in feature["geometry"]["coordinates"]:
                        points.extend(polyg[0])
                        points.append([None, None])  # End of polygon
                elif feature["geometry"]["type"] == "MultiLineString":
                    points.extend(feature["geometry"]["coordinates"])
                    points.append([None, None])
                elif feature["geometry"]["type"] == "LineString":
                    points.extend(feature["geometry"]["coordinates"])
                    points.append([None, None])
                else:
                    pass
            lons, lats = zip(*points)
            out_list = [lons, lats]
            return out_list

        def _get_geodata(input_json: json):
            """Get center position in a given feature (generally a country) for label placement; coordinate stored in-class"""
            gpd_df = gpd.GeoDataFrame.from_features(input_json["features"])
            area = float(gpd_df.area)
            points = gpd_df.centroid
            lon = float(points.x)
            lat = float(points.y)
            points = [lon, lat]
            return points, area

        def _draw_labels():

            # Clean up label df
            self.label_df.index = self.label_df["name"]
            self.label_df.drop(columns=["name"], inplace=True)

            if self.config["nat_label_toggle"] == True:
                for index, row in self.label_df.iterrows():
                    if row["type"] == "nat":
                        fig.add_scattermapbox(
                            lat=[row["centroid"][1]],
                            lon=[row["centroid"][0]],
                            showlegend=False,
                            mode="text",
                            text=index.upper(),
                            fillcolor=self.styling["nat_label_color"],
                            opacity=self.styling["nat_label_opacity"],
                            textposition="middle center",
                            # Adjusts nat labels on the basis of country size
                            textfont=dict(
                                size=self.styling["nat_label_size"] * 1.5
                                if row["size"] > 150
                                else self.styling["nat_label_size"]
                                if row["size"] > 110
                                else (self.styling["nat_label_size"] * 0.8)
                                if row["size"] > 80
                                else (self.styling["nat_label_size"] * 0.65)
                                if row["size"] > 50
                                else (self.styling["nat_label_size"] * 0.45)
                                if row["size"] > 30
                                else (self.styling["nat_label_size"] * 0.35)
                                if row["size"] > 10
                                else 10,
                                color=self.styling["nat_label_color"],
                            ),
                        ),
            else:
                pass

            # Adjusts subnat labels on the basis of size
            if (
                self.config["subnat_label_toggle"] == True
                and len(self.content["subnat_list"]) > 0
            ):
                for x in self.content["subnat_list"]:
                    if x not in self.content["country_list"]:

                        fig.add_scattermapbox(
                            lat=[self.label_df.loc[x]["centroid"][1]],
                            lon=[self.label_df.loc[x]["centroid"][0]],
                            showlegend=False,
                            mode="text",
                            text=x.upper(),
                            fillcolor=self.styling["subnat_label_color"],
                            opacity=self.styling["subnat_label_opacity"],
                            textposition="middle center",
                            # Adjusts on the basis of country size
                            textfont=dict(
                                size=self.styling["subnat_label_size"] * 1.5
                                if self.label_df.loc[x]["size"] > 150
                                else self.styling["subnat_label_size"]
                                if self.label_df.loc[x]["size"] > 110
                                else (self.styling["subnat_label_size"] * 0.9)
                                if self.label_df.loc[x]["size"] > 80
                                else (self.styling["subnat_label_size"] * 0.80)
                                if self.label_df.loc[x]["size"] > 50
                                else (self.styling["subnat_label_size"] * 0.60)
                                if self.label_df.loc[x]["size"] > 30
                                else (self.styling["subnat_label_size"] * 0.50)
                                if self.label_df.loc[x]["size"] > 10
                                else 10,
                                color=self.styling["subnat_label_color"],
                            ),
                        ),

            if (
                self.config["subnat_label_toggle"] == True
                and len(self.content["subnat_list"]) == 0
            ):
                for index, row in self.label_df.iterrows():
                    if row["type"] == "subnat":
                        fig.add_scattermapbox(
                            lat=[row["centroid"][1]],
                            lon=[row["centroid"][0]],
                            showlegend=False,
                            mode="text",
                            text=index.upper(),
                            fillcolor=self.styling["subnat_label_color"],
                            opacity=self.styling["subnat_label_opacity"],
                            textposition="middle center",
                            # Adjusts on the basis of country size
                            textfont=dict(
                                size=self.styling["subnat_label_size"] * 1.5
                                if row["size"] > 150
                                else self.styling["subnat_label_size"]
                                if row["size"] > 110
                                else (self.styling["subnat_label_size"] * 0.9)
                                if row["size"] > 80
                                else (self.styling["subnat_label_size"] * 0.80)
                                if row["size"] > 50
                                else (self.styling["subnat_label_size"] * 0.60)
                                if row["size"] > 30
                                else (self.styling["subnat_label_size"] * 0.50)
                                if row["size"] > 10
                                else 10,
                                color=self.styling["subnat_label_color"],
                            ),
                        ),

        def _draw_countries(outline=False):
            """Draws external (national) borders."""

            def __crunch_countries():
                """Crunch the data for countries to be drawn; derives lon/lat pairs from geojson"""
                countries_slice = []
                labels_slice = []
                exclusion_list = []
                for i in self.nat_db["features"]:
                    # Outputs the lon/lat pairs for countries in the country_list and also stores their centroid point in-class for future reference

                    if (
                        i["properties"]["ADMIN"] in self.content["country_list"]
                        and i["properties"]["ADMIN"] not in exclusion_list
                    ):
                        i["id"] = i["properties"]["ADMIN"]
                        countries_slice.append(i)

                        # Store centroids in class df for labels
                        points, area = _get_geodata(
                            {"type": ["FeatureCollection"], "features": [i]}
                        )
                        new_entry = {
                            "name": str(i["properties"]["ADMIN"]),
                            "centroid": points,
                            "size": area,
                            "position": "middle-right",
                            "type": "nat",
                        }

                        labels_slice.append(new_entry)

                        # Avoid double-counting when multiple countries in country_list
                        exclusion_list.append(i["properties"]["ADMIN"])

                self.label_df = pd.concat(
                    [self.label_df, pd.DataFrame(labels_slice)],
                    ignore_index=True,
                    axis=0,
                )

                # Return a json containing geometry of specified countries
                return _lat_cruncher(
                    {"type": "FeatureCollection", "features": countries_slice}
                )

            if outline == False:
                self.external_borders = __crunch_countries()

                # Add external borders to overall figure
                fig.add_scattermapbox(
                    lat=self.external_borders[1],
                    lon=self.external_borders[0],
                    showlegend=False,
                    mode="lines",
                    fillcolor=self.styling["background_color"],
                    fill="toself"
                    if self.config["chloro_toggle"] == False
                    and self.config["subnat_toggle"] == False
                    else "none",
                    opacity=self.styling["nat_border_opacity"],
                    line=dict(
                        width=self.styling["nat_border_width"],
                        color=self.styling["nat_border_color"],
                    ),
                )

            if outline == True:
                # Add external borders to overall figure
                fig.add_scattermapbox(
                    lat=self.external_borders[1],
                    lon=self.external_borders[0],
                    showlegend=False,
                    mode="lines",
                    fillcolor=self.styling["background_color"],
                    fill="none",
                    opacity=self.styling["nat_border_opacity"],
                    line=dict(
                        width=self.styling["nat_border_width"],
                        color=self.styling["nat_border_color"],
                    ),
                )

        def _draw_subnats():
            """Draws sub-national (regional/provincial/state) borders"""

            def __crunch_subnats():
                """Crunch the data for countries to be drawn; derives lon/lat pairs from geojson"""
                subnats_slice = []
                exclusion_list = []
                labels_slice = []
                for i in self.subnat_db["features"]:
                    if len(self.content["subnat_list"]) > 0:
                        if (
                            i["properties"]["name"] in self.content["subnat_list"]
                            or i["properties"]["admin"] in self.content["subnat_list"]
                        ) and i["properties"]["name"] not in exclusion_list:
                            i["id"] = i["properties"]["admin"]
                            subnats_slice.append(i)

                            # Store centroids in class df for labels
                            points, area = _get_geodata(
                                {"type": ["FeatureCollection"], "features": [i]}
                            )

                            new_entry = {
                                "name": i["properties"]["name_en"],
                                "centroid": points,
                                "size": area,
                                "position": "middle-right",
                                "code": i["properties"]["iso_3166_2"].replace("-", ""),
                                "type": "subnat",
                            }

                            labels_slice.append(new_entry)
                    else:
                        if (
                            i["properties"]["admin"] in self.content["country_list"]
                            and i["properties"]["name"] not in exclusion_list
                        ):
                            i["id"] = i["properties"]["admin"]

                            subnats_slice.append(i)

                            # Store centroids in class df for labels
                            points, area = _get_geodata(
                                {"type": ["FeatureCollection"], "features": [i]}
                            )

                            new_entry = {
                                "name": i["properties"]["name_en"],
                                "centroid": points,
                                "size": area,
                                "position": "middle-right",
                                "code": i["properties"]["iso_3166_2"].replace("-", ""),
                                "type": "subnat",
                            }

                            labels_slice.append(new_entry)

                    # Avoid double-counting when multiple countries in country_list
                    exclusion_list.append(i["properties"]["name"])

                self.label_df = pd.concat(
                    [self.label_df, pd.DataFrame(labels_slice)],
                    ignore_index=False,
                    axis=0,
                )

                # Return a json containing geometry of specified countries
                return _lat_cruncher(
                    {"type": "FeatureCollection", "features": subnats_slice}
                )

            # Checks toggles and draws subnats
            if (
                self.config["subnat_toggle"] == True
                or len(self.content["subnat_list"]) > 0
            ):

                internal_borders = __crunch_subnats()

                # Add internal borders to figure
                fig.add_scattermapbox(
                    lat=internal_borders[1],
                    lon=internal_borders[0],
                    showlegend=False,
                    mode="lines",
                    fillcolor=self.styling["background_color"],
                    fill="toself" if self.config["chloro_toggle"] == False else "none",
                    opacity=self.styling["subnat_border_opacity"],
                    line=dict(
                        width=self.styling["subnat_border_width"],
                        color=self.styling["subnat_border_color"],
                    ),
                )

            else:
                pass

        def _draw_markers():
            """Draws cities and other notable features"""

            def __crunch_markers():
                """Crunch the data for cities to be drawn; derives lon/lat pairs from custom db initialized at class init (self.city_db)"""
                out_df = pd.DataFrame(
                    columns=["name", "type", "lon", "lat", "position"]
                )
                cities_slice = []

                for x in self.content["city_list"]:
                    # The city DB contains a variety of feature codes based on size of a population center. This goes for the largest one by moving down the hierarchy

                    if any(
                        self.city_db.loc[self.city_db["name"] == x[0]]["feature code"]
                        == "PPLC"
                    ):
                        cities_slice.append(
                            {
                                "name": x[0],
                                "type": "city",
                                "lon": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPLC")
                                    ]["longitude"]
                                ),
                                "lat": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPLC")
                                    ]["latitude"]
                                ),
                                "position": x[1],
                            }
                        )
                        continue

                    if any(
                        self.city_db.loc[self.city_db["name"] == x[0]]["feature code"]
                        == "PPLA"
                    ):
                        cities_slice.append(
                            {
                                "name": x[0],
                                "type": "city",
                                "lon": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPLA")
                                    ]["longitude"]
                                ),
                                "lat": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPLA")
                                    ]["latitude"]
                                ),
                                "position": x[1],
                            }
                        )
                        continue

                    if any(
                        self.city_db.loc[self.city_db["name"] == x[0]]["feature code"]
                        == "PPLA2"
                    ):
                        cities_slice.append(
                            {
                                "name": x[0],
                                "type": "city",
                                "lon": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPLA2")
                                    ]["longitude"]
                                ),
                                "lat": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPLA2")
                                    ]["latitude"]
                                ),
                                "position": x[1],
                            }
                        )
                        continue

                    if any(
                        self.city_db.loc[self.city_db["name"] == x[0]]["feature code"]
                        == "PPLA3"
                    ):
                        cities_slice.append(
                            {
                                "name": x[0],
                                "type": "city",
                                "lon": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPLA3")
                                    ]["longitude"]
                                ),
                                "lat": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPLA3")
                                    ]["latitude"]
                                ),
                                "position": x[1],
                            }
                        )
                        continue

                    if any(
                        self.city_db.loc[self.city_db["name"] == x[0]]["feature code"]
                        == "PPLA4"
                    ):
                        cities_slice.append(
                            {
                                "name": x[0],
                                "type": "city",
                                "lon": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPLA4")
                                    ]["longitude"]
                                ),
                                "lat": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPLA4")
                                    ]["latitude"]
                                ),
                                "position": x[1],
                            }
                        )
                        continue

                    if any(
                        self.city_db.loc[self.city_db["name"] == x[0]]["feature code"]
                        == "PPL"
                    ):
                        cities_slice.append(
                            {
                                "name": x[0],
                                "type": "city",
                                "lon": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPL")
                                    ]["longitude"]
                                ),
                                "lat": float(
                                    self.city_db.loc[
                                        (self.city_db["name"] == x[0])
                                        & (self.city_db["feature code"] == "PPL")
                                    ]["latitude"]
                                ),
                                "position": x[1],
                            }
                        )
                        continue

                out_df = pd.concat(
                    [out_df, pd.DataFrame(cities_slice)], ignore_index=False, axis=0
                )

                return out_df

            city_coords = __crunch_markers()

            for index, row in city_coords.iterrows():

                fig.add_scattermapbox(
                    lat=[row["lat"]],
                    lon=[row["lon"]],
                    showlegend=False,
                    mode="markers+text",
                    marker=go.scattermapbox.Marker(
                        size=self.styling["marker_size"],
                        symbol="circle",
                        allowoverlap=False,
                        color=self.styling["marker_color"],
                    ),
                    textposition=row["position"],
                    text=row["name"],
                    textfont=dict(
                        size=self.styling["city_text_size"],
                        color=self.styling["city_text_color"],
                    ),
                    fillcolor=self.styling["background_color"],
                )

            # Map irregular features if there are any
            if len(self.content["irregular_markers"]) > 0:
                for x in self.content["irregular_markers"]:

                    fig.add_scattermapbox(
                        lat=[x["lat"]],
                        lon=[x["lon"]],
                        showlegend=False,
                        mode="markers+text",
                        marker=go.scattermapbox.Marker(
                            size=self.styling["marker_size"],
                            symbol="circle",
                            allowoverlap=False,
                            color=self.styling["marker_color"],
                        ),
                        textposition=x["position"],
                        text=x["name"],
                        textfont=dict(
                            size=self.styling["city_text_size"],
                            color=self.styling["city_text_color"],
                        ),
                        fillcolor=self.styling["background_color"],
                    )

            else:
                pass

        def _draw_irregulars():
            """Draws irregular features (imported geojson files from the features sub-directory)"""

            def __crunch_irregulars():
                """Prepares geojson data; takes a class list of geojsons (self.features) and outputs list of lon/lat pairs"""
                features_out = []
                for geo in self.features:
                    features_out.append(
                        _lat_cruncher(
                            {"type": "FeatureCollection", "features": geo["features"]}
                        )
                    )
                return features_out

            if self.config["irregular_feature_toggle"] == True:
                # Map irregulars (allows for multiple features
                for x in __crunch_irregulars():
                    fig.add_scattermapbox(
                        lat=x[1],
                        lon=x[0],
                        showlegend=False,
                        mode="lines",
                        fillcolor=self.styling["feature_color"],
                        fill="toself",
                        opacity=self.styling["feature_border_opacity"],
                        line=dict(
                            width=self.styling["feature_border_width"],
                            color=self.styling["feature_border_color"],
                        ),
                    )

                # Draw an additional top layer of external borders to clean the map up; thickens the borders to hide imperfections
                fig.add_scattermapbox(
                    lat=self.external_borders[1],
                    lon=self.external_borders[0],
                    showlegend=False,
                    mode="lines",
                    fillcolor=self.styling["background_color"],
                    fill="none",
                    opacity=self.styling["nat_border_opacity"],
                    line=dict(
                        width=(self.styling["nat_border_width"] * 1.5),
                        color=self.styling["nat_border_color"],
                    ),
                )
            else:
                pass

        def _draw_chloro():
            """Uses data from csv files located in csv directory to draw a chloro layer. Assumption that the csv file has the following headers: admin, admin1, date.  Code col is what to match, date col is date"""

            working_geo = in_geo
            working_df = in_df

            trace = go.Figure(
                go.Choroplethmapbox(
                    geojson=in_geo,
                    locations=in_df.index,
                    z=in_df["mw"],
                    colorscale="YlOrRd",
                )
            )

            fig.add_traces(trace.data[0])

        def _label_adjuster():
            """As a final step, this function iterates over the fig object and adjusts labels specified in self.content['label_adjusts']"""

            def __shifter(in_lon, in_lat, direction, degree):
                """Adjusts lon, lat pairs for labels based on direction and degree"""

                diagonals = degree / 2

                if direction == "top":
                    in_lat += degree
                elif direction == "top left":
                    in_lat += diagonals
                    in_lon -= diagonals
                elif direction == "top right":
                    in_lat += diagonals
                    in_lon += diagonals
                elif direction == "bottom":
                    in_lat -= degree
                elif direction == "bottom left":
                    in_lat -= diagonals
                    in_lon -= diagonals
                elif direction == "bottom right":
                    in_lat -= diagonals
                    in_lon += diagonals
                elif direction == "right":
                    in_lon += degree
                elif direction == "left":
                    in_lon -= degree
                return in_lon, in_lat

            if len(self.content["label_adjusts"]) > 0:
                exclusion_list = []
                for no, x in enumerate(fig.data):
                    if x.mode == "text" and x.text not in exclusion_list:
                        for y in self.content["label_adjusts"]:
                            if y[0].upper().replace("_", " ") == x.text:
                                adjusted_lon, adjusted_lat = __shifter(
                                    fig.data[no].lon[0], fig.data[no].lat[0], y[1], y[2]
                                )
                                fig.data[no].lon = [adjusted_lon]
                                fig.data[no].lat = [adjusted_lat]
                                if y[3] != 0:
                                    fig.data[no].textfont["size"] = (
                                        fig.data[no].textfont["size"] * y[3]
                                    )
                                else:
                                    pass
                            else:
                                pass

                        exclusion_list.append(x.text)

            else:
                pass

        # Initialize base template (uses a mapbox style for background)
        fig = go.Figure()

        # Execute drawing functions to build the map
        if self.config["chloro_toggle"] == False:

            _draw_countries()
            _draw_subnats()
            _draw_countries(outline=True)
            _draw_labels()
            _draw_irregulars()
            _draw_markers()
            _label_adjuster()

            fig.update_layout(
                coloraxis_showscale=True,
                margin={"l": 0, "r": 0, "b": 0, "t": 25},
                title="<b><i>Map<i><b>",
                title_x=0.5,
                font_family="Helvetica",
                showlegend=True,
                legend_title=dict(text="MW"),
                mapbox=go.layout.Mapbox(
                    style="mapbox://styles/zbon/ckshpu8fb091a17p951bwv9hx",
                    zoom=4.12,
                    accesstoken=self.token,
                    center_lat=self.label_df.loc[
                        self.content["country_list"][0], "centroid"
                    ][1],
                    center_lon=self.label_df.loc[
                        self.content["country_list"][0], "centroid"
                    ][0],
                ),
            )

        fig.show()
        # print(fig.data)


if __name__ == "__main__":
    # load config
    map_token = os.getenv("MAP_TOKEN")

    if not map_token:
        print(
            "Missing env values for MAP_TOKEN; Mapbox token required to create base map"
        )
        sys.exit(1)

    pd.set_option("mode.chained_assignment", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_colwidth", None)
    warnings.filterwarnings("ignore")

    def commandline_interpreter():

        # Label positions
        if "-labelpos" in sys.argv:
            label_index = sys.argv.index("-labelpos")
            new_city_list = []
            for x in sys.argv[label_index + 1].split("+"):
                splitd = x.split(">")
                new_city_list.append([splitd[0], splitd[1].replace("_", " ")])
            map_content["city_list"] = new_city_list

        # Format: [label, direction, extent, size_override (0 for unchanged)]
        if "-labeladjust" in sys.argv:
            label_index = sys.argv.index("-labeladjust")
            # Check the input because this is a complicated one.
            for y in sys.argv[label_index + 1].split("+"):
                if y.count(">") != 3:
                    print("Input error on -labeladjust; please try again.")
                    sys.exit()
                else:
                    pass

            new_adjust_list = []
            for x in sys.argv[label_index + 1].split("+"):
                splitd = x.split(">")
                new_adjust_list.append(
                    [
                        splitd[0],
                        splitd[1].replace("_", " "),
                        float(splitd[2]),
                        float(splitd[3]),
                    ]
                )
            map_content["label_adjusts"] = new_adjust_list

    # commandline_interpreter()
    def command_line():
        global map_token

        def p():
            """Creates parser and arguments"""
            parser = argparse.ArgumentParser(
                description="Command-line arguments for outputting a custom map."
            )
            parser.add_argument(
                "--mapboxtoken",
                help="Specify a custom Mapbox token to override the MAP_TOKEN class variable",
            )
            parser.add_argument(
                "--snats",
                action="store_true",
                help="Display subnational borders for states/provinces (default off)",
            )
            parser.add_argument(
                "--snatlabels",
                action="store_true",
                help="Display subnational labels (default off)",
            )
            parser.add_argument(
                "--natlabels",
                action="store_true",
                help="Display national-level labels (default off)",
            )
            parser.add_argument(
                "--natlist",
                help="Specify which countries to include on map; SYNTAX: 'country1+country2+country3'; use _ for spaces ('United_States_of_America'); ",
            )
            parser.add_argument(
                "--snatlist",
                help="Specify which provinces to include on map; SYNTAX: 'snat1+snat2+snat3'; use _ for spaces ('British_Columbia'); ",
            )
            parser.add_argument(
                "--citylist",
                help="Specify which cities to include on map; SYNTAX: 'city1+city2+city3'; use _ for spaces ('Addis_Ababa'); ",
            )
            parser.add_argument(
                "--cmarker",
                help="Place a custom point on the map by lon/lat; SYNTAX: 'name>lon>lat>label_position' EXAMPLE: 'Taj_Mahal>78.04206>27.17389>middle_right'",
            )
            parser.add_argument(
                "--labelpos",
                help="Changes label position of a city or feature ; SYNTAX: 'city+label_position'; EXAMPLE: 'Vancouver>middle_right+Kamloops>bottom_left' ; NOTE: Label position options include 'top right' 'bottom right' 'top left' 'middle left' 'top center', etc.",
            )
            parser.add_argument(
                "--labeladjust",
                help="Changes the size and position of subnat and nat labels; SYNTAX: 'label_name>label_position>shift_extent+size'; EXAMPLE: 'United_States_of_America>top_left>10>2+Canada>bottom_left>4>1'; NOTE:Label shifting extent is approximately 4 per inch ; label size is a multiplier of current value (for example, 2 is 2x) ; countries can be repeated for finishing touches",
            )
            parser.add_argument(
                "--background_color",
                help="Override the background color of the map (formatted as color code; default #ede7f1)",
            )
            parser.add_argument(
                "--nat_border_opacity",
                help="Override opacity of national borders (default 1)",
            )
            parser.add_argument(
                "--nat_border_width",
                help="Override width of national borders (default 1)",
            )
            parser.add_argument(
                "--nat_border_color",
                help="Override color of national borders (default #282828)",
            )
            parser.add_argument(
                "--subnat_border_opacity",
                help="Override opacity of subnational borders (default 0.5)",
            )
            parser.add_argument(
                "--subnat_border_width",
                help="Override width of subnational borders (default 0.5)",
            )
            parser.add_argument(
                "--subnat_border_color",
                help="Override color of subnational borders (default #282828)",
            )
            parser.add_argument(
                "--city_text_size",
                help="Override text size of city labels (default 12)",
            )
            parser.add_argument(
                "--city_text_color",
                help="Override text color for city labels (default #241f20)",
            )
            parser.add_argument(
                "--marker_size", help="Override size of marker for cities (default 8)"
            )
            parser.add_argument(
                "--marker_color",
                help="Override color of marker for cities (default #241f20)",
            )
            parser.add_argument(
                "--nat_label_opacity",
                help="Override opacity of national labels (default 0.7)",
            )
            parser.add_argument(
                "--nat_label_size",
                help="Override text size for national labels (default 30)",
            )
            parser.add_argument(
                "--nat_label_color",
                help="Overide color for national labels (default #282828)",
            )
            parser.add_argument(
                "--subnat_label_opacity",
                help="Override opacity for subnational labels (default 0.5)",
            )
            parser.add_argument(
                "--subnat_label_size",
                help="Override text size for subnational labels (default 15)",
            )
            parser.add_argument(
                "--subnat_label_color",
                help="Override color for subnational labels (default #282828)",
            )
            parser.add_argument(
                "--feature_color",
                help="Color of custom feature; Format this as a rgba color code to adjust opacity (default rgba(202, 52, 51, 0.5)",
            )
            parser.add_argument(
                "--feature_fill_opacity",
                help="Opacity of custom feature (default 0.25)",
            )
            parser.add_argument(
                "--feature_border_opacity",
                help="Border opacity of custom feature (default 0.75)",
            )
            parser.add_argument(
                "--feature_border_width",
                help="Border width of custom feature (default 1)",
            )
            parser.add_argument(
                "--feature_border_color",
                help="Border color of custom feature (default #282828)",
            )

            return parser.parse_args()

        args = p()

        # Apply the arguments
        if args.mapboxtoken:
            map_token = args.mapboxtoken

        # Toggles
        map_settings["subnat_toggle"] = args.snats
        map_settings["subnat_label_toggle"] = args.snatlabels
        map_settings["nat_label_toggle"] = args.natlabels

        # Features
        if args.natlist:
            map_content["country_list"] = args.natlist.replace("_", " ").split("+")
        if args.snatlist:
            map_content["subnat_list"] = args.snatlist.replace("_", " ").split("+")
        if args.citylist:
            city_names = args.citylist.replace("_", " ").split("+")
            map_content["city_list"] = [[x, "middle right"] for x in city_names]
        if args.cmarker:
            cfeature_list = []
            for x in args.cmarker.split("+"):
                splitd = x.split(">")
                cfeature_list.append(
                    {
                        "name": splitd[0].replace("_", " "),
                        "lon": float(splitd[1]),
                        "lat": float(splitd[2]),
                        "position": splitd[3].replace("_", " "),
                    }
                )
            map_content["irregular_markers"] = cfeature_list

        # Label shifts
        if args.labelpos:
            new_list = map_content["city_list"]
            for x in args.labelpos.split("+"):
                city_name = x.split(">")[0]
                city_position = x.split(">")[1].replace("_", " ")
                for no, y in enumerate(map_content["city_list"]):
                    if city_name in y:
                        del new_list[no]
                        new_list.append([city_name, city_position])
                        continue
                    else:
                        pass

        if args.labeladjust:
            # Check the input because this is a complicated one.
            for y in args.labeladjust.split("+"):
                if y.count(">") != 3:
                    print("Input error on -labeladjust; please try again.")
                    sys.exit()
                else:
                    pass

            new_adjust_list = []
            for x in args.labeladjust.split("+"):
                splitd = x.split(">")
                new_adjust_list.append(
                    [
                        splitd[0],
                        splitd[1].replace("_", " "),
                        float(splitd[2]),
                        float(splitd[3]),
                    ]
                )
            map_content["label_adjusts"] = new_adjust_list

        # Formatting
        if args.background_color:
            map_styling["background_color"] = args.background_color
        if args.nat_border_opacity:
            map_styling["nat_border_opacity"] = float(args.nat_border_opacity)
        if args.nat_border_width:
            map_styling["nat_border_width"] = float(args.nat_border_width)
        if args.nat_border_color:
            map_styling["nat_border_color"] = args.nat_border_color
        if args.subnat_border_opacity:
            map_styling["subnat_border_opacity"] = float(args.subnat_border_opacity)
        if args.subnat_border_width:
            map_styling["subnat_border_width"] = float(args.subnat_border_width)
        if args.subnat_border_color:
            map_styling["subnat_border_color"] = args.subnat_border_color
        # Cities/Markers formatting
        if args.city_text_size:
            map_styling["city_text_size"] = float(args.city_text_size)
        if args.city_text_color:
            map_styling["city_text_color"] = args.city_text_color
        if args.marker_size:
            map_styling["marker_size"] = float(args.marker_size)
        if args.marker_color:
            map_styling["marker_color"] = args.marker_color
        # Labels
        if args.nat_label_opacity:
            map_styling["nat_label_opacity"] = float(args.nat_label_opacity)
        if args.nat_label_size:
            map_styling["nat_label_size"] = float(args.nat_label_size)
        if args.nat_label_color:
            map_styling["nat_label_color"] = args.nat_label_color
        if args.subnat_label_opacity:
            map_styling["subnat_label_opacity"] = float(args.subnat_label_opacity)
        if args.subnat_label_size:
            map_styling["subnat_label_size"] = float(args.subnat_label_size)
        if args.subnat_label_color:
            map_styling["subnat_label_color"] = args.subnat_label_color
        # Custom Feature Styling
        if args.feature_color:
            map_styling["feature_color"] = args.feature_color
        if args.feature_fill_opacity:
            map_styling["feature_fill_opacity"] = float(args.feature_fill_opacity)
        if args.feature_border_opacity:
            map_styling["feature_border_opacity"] = float(args.feature_border_opacity)
        if args.feature_border_width:
            map_styling["feature_border_width"] = float(args.feature_border_width)
        if args.feature_border_color:
            map_styling["feature_border_color"] = args.feature_border_color

    command_line()
    m = MapBuilder(map_token, map_settings, map_content, map_styling)
    m.draw_map()
