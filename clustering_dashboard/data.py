import os
import json

import pandas as pd

from clustering_dashboard import convert, calculate


class data():

    def __init__(self):
        
        self.load_settings()
        self.load_data()

        self.details[['Cluster ID', 'Location ID', 'Time ID']] = None

        # pre-calculate comparison of location and time
        self.distance_radians = calculate.distance_matrix(self.details, self.columns['latitude'], self.columns['longitude'])
        self.duration_seconds = calculate.duration_matrix(self.details, self.columns['time'])

        # convert timestamp to integer for color bar heatmap
        self.details['_timestamp'] = self.details[self.columns['time']].apply(lambda x: int(x.timestamp()*1000))

        # convert fo mercator for map display
        latitude_mercator, longitude_mercator = convert.latlon_to_mercator(
            self.details[self.columns['latitude']],
            self.details[self.columns['longitude']]
        )
        self.details['_latitude_mercator'] = latitude_mercator
        self.details['_longitude_mercator'] = longitude_mercator


    def load_settings(self):

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'settings.json')) as fh:
            settings = json.load(fh)

        self.file_path = settings['file_path']
        self.columns = pd.Series(settings['column_names'])
        self.additional_summary = settings['additional_summary']


    def load_data(self):

        self.details = pd.read_parquet(self.file_path)
        self.column_id = self.details.index.name

        self.details = self.details.reset_index()
