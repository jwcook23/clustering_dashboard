import os
import json

import pandas as pd

from clustering_dashboard import convert, calculate


class data():

    def __init__(self):
        
        self.load_settings()
        self.load_data()

        self.address['_timestamp'] = self.address[self.columns['time']].apply(lambda x: int(x.timestamp()*1000))

        self.distance = calculate.distance_matrix(self.address, self.columns['latitude'], self.columns['longitude'])

        self.map_display()


    def load_settings(self):

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'settings.json')) as fh:
            settings = json.load(fh)

        self.file_path = settings['file_path']
        self.columns = pd.Series(settings['column_names'])
        self.additional_summary = settings['additional_summary']


    def load_data(self):

        self.address = pd.read_parquet(self.file_path)
        self.column_id = self.address.index.name

        self.address = self.address.reset_index()


    def map_display(self):

        latitude = self.address[self.columns['latitude']]
        longitude = self.address[self.columns['longitude']]
        
        latitude_mercator, longitude_mercator = convert.latlon_to_mercator(latitude, longitude)
        self.address['_latitude_mercator'] = latitude_mercator
        self.address['_longitude_mercator'] = longitude_mercator