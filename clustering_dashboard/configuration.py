import base64
import io

import pandas as pd

from clustering_dashboard.figures import figures
from clustering_dashboard import convert, calculate


class configuration(figures):

    def __init__(self):

        pass

    def _load_data(self, buffer_or_path):

        self.details = pd.read_parquet(buffer_or_path)

        dropdown = ['']+list(self.details.columns)
        if self.details.index.name is not None:
            dropdown += [self.details.index.name]
        for col in self.column_options.values():
            col.options = dropdown

        # TODO: allow creation of id column
        # self.column_options.menu['id'] += [None]


    def _file_selected(self, attr, old, new):

        decoded = base64.b64decode(new)
        buffer = io.BytesIO(decoded)

        self._load_data(buffer)


    def _columns_selected(self, attr, old, new):

        for col in self.column_options.keys():
            self.columns.at[col] = self.column_options[col].value


        if (self.columns.str.len()>0).all():

            self._prepare_details()

            figures.__init__(self)

            self.generate_dashboard()
            self.landing_page()

            if self.document is not None:
                self.document.remove_root(self.layout_parameters)
                self.document.add_root(self.layout_dashboard)


    def _prepare_details(self):

        self.details[['Cluster ID', 'Location ID', 'Time ID']] = None

        self.details[self.columns['time']] = pd.to_datetime(self.details[self.columns['time']])
        self.details = self.details.sort_values(by=self.columns['time'])
        if self.details.index.name == self.columns['id']:
            self.details = self.details.reset_index()

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