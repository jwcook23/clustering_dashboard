import pandas as pd
import numpy as np
from bokeh.models import Dropdown, CheckboxGroup, NumericInput

import group

class updates():

    def __init__(self):
        
        self.parameters = {}
        self.options = {}

        self.parameters['max_cluster_distance_miles'] = NumericInput(value=0.01, mode='float', title="Location Distance (miles)", height=50, width=160)
        self.parameters['max_cluster_distance_miles'].on_change('value', self.parameter_callback)

        self.parameters['date_range'] = NumericInput(value=1, mode='float', title=f"Time Duration ({self.units_time})", height=50, width=160)
        self.parameters['date_range'].on_change('value', self.parameter_callback)
        self.parameters['date_range'].visible = True

        menu = [
            ("1) Reset display.", "reset display"),
            ("2) Display clusters with same Location ID.", "same location"),
            ("3) Display clusters with same Date ID.", "same date")
        ]
        self.options['display'] = Dropdown(label="display other cluster options", button_type="default", menu=menu, height=25, width=200)
        self.options['display'].on_click(self.display_callback)


    def zoom_window(self, df):
        '''Calculate a square zoom window using mercator x and y points.'''

        center = df.median()
        offset = pd.concat([
            (center-df.min()).abs(),
            (center-df.max()).abs()
        ]).max()
        zoom = pd.DataFrame({'min': center-offset, 'max': center+offset})

        return zoom


    def update_map(self):
        '''Plot location point and boundary when making a selection in the summary table.'''

        show_ids = self.selected_cluster.index

        data_boundary = {
            'xs': [],
            'ys': []
        }
        data_point = {
            'x': [],
            'y': [],
        }

        date = self.columns['date']

        unique_clusters = self.selected_cluster.dropna().drop_duplicates()
        data_boundary.update({
            'xs': self.cluster_boundary.loc[unique_clusters, 'Longitude_mercator'].tolist(),
            'ys': self.cluster_boundary.loc[unique_clusters, 'Latitude_mercator'].tolist(),
            date: self.address.loc[unique_clusters.index, date].tolist(),
            '_timestamp': self.address.loc[unique_clusters.index, '_timestamp'].tolist()
        })

        # update address using selected cluster
        longitude = self.columns['longitude']
        latitude = self.columns['latitude']
        data_point.update({
            'x': self.address.loc[show_ids, 'Longitude_mercator'].values,
            'y': self.address.loc[show_ids, 'Latitude_mercator'].values,
            self.column_id: show_ids,
            longitude: self.address.loc[show_ids, longitude].values,
            latitude: self.address.loc[show_ids, latitude].values,
            date: self.address.loc[show_ids, date].values,
            '_timestamp': self.address.loc[show_ids, '_timestamp'].values
        })
        # data_point.update({
        #     col: self.address.loc[show_ids, col].values for col in self.address.columns.drop([longitude,latitude,date])
        # })

        # update map title
        self.update_titles()

        # plot updated data
        self.render_boundary.data_source.data = data_boundary
        self.render_points.data_source.data = data_point

        # update range to selected
        zoom = self.zoom_window(self.address.loc[show_ids,['Longitude_mercator','Latitude_mercator']])
        self.plot_map.x_range.start = zoom.at['Longitude_mercator','min']
        self.plot_map.x_range.end = zoom.at['Longitude_mercator','max']
        self.plot_map.y_range.start = zoom.at['Latitude_mercator','min']
        self.plot_map.y_range.end = zoom.at['Latitude_mercator','max']


    def update_detail(self):

        if self.selected_cluster is None:
            data = dict()
        else:
            cluster = self.cluster_id[self.cluster_id['Cluster ID'].isin(self.selected_cluster)].index
            name = [col.field for col in self.table_detail.columns]
            data = self.address.loc[cluster, name]
            
        self.source_detail.data = data
        self.update_titles()


    def update_evaluation(self):
        
        bins = self.histogram_evaulation(self.cluster_summary['Nearest (miles)'])
        self.render_next_distance.data_source.data = bins

        bins = self.histogram_evaulation(self.cluster_summary['Length (miles)'])
        self.render_span_distance.data_source.data = bins

        bins = self.histogram_evaulation(self.cluster_summary[f'Nearest ({self.units_time})'])
        self.render_next_date.data_source.data = bins

        bins = self.histogram_evaulation(self.cluster_summary[f'Length ({self.units_time})'])
        self.render_span_date.data_source.data = bins


    def update_summary(self):

        cluster_summary = self.filter_clusters()

        cols = [x.field for x in self.table_summary.columns]
        data = cluster_summary[cols]
        self.source_summary.data = data.to_dict(orient='list')


    def update_titles(self):

        if self.selected_cluster is None:
            selected_title = 'select cluster summary to display'
        else:

            selected_title = f'{self.selected_cluster.nunique()} clusters displayed'

        self.title_map.text = f"Location and Time Clusters: {selected_title}"

        self.title_main.text = f'{len(self.cluster_summary)} Total Clusters'


    def table_callback(self, attr, old, selected_cluster):

        self.selected_cluster = self.cluster_id.loc[
            self.cluster_id['Cluster ID'].isin(selected_cluster), 
            'Cluster ID'
        ]
        self.update_map()
        self.update_detail()


    def display_callback(self, event):
        
        if event.item=='reset display':
            self.parameter_callback(None, None, None)
            return None
        elif event.item=='same location':
            self.same_location()
        elif event.item=='same date':
            self.same_date()

        self.update_summary()
        self.update_map()
        self.update_detail()


    def date_callback(self, event):

        if event == [0]:
            self.parameters['date_range'].visible = True
        else:
            self.parameters['date_range'].visible = False

        self.parameter_callback(None, None, None)


    def same_location(self):
            
            same = self.cluster_id.loc[
                self.cluster_id['Cluster ID'].isin(self.selected_cluster),
                'Location ID'
            ]
            self.selected_cluster = self.cluster_id.loc[
                self.cluster_id['Location ID'].isin(same),
                'Cluster ID'
            ]


    def same_date(self):

            same = self.cluster_id.loc[
                self.cluster_id['Cluster ID'].isin(self.selected_cluster),
                'Date ID'
            ]
            self.selected_cluster = self.cluster_id.loc[
                self.cluster_id['Date ID'].isin(same),
                'Cluster ID'
            ]            

    def filter_clusters(self):

        if self.selected_cluster is None:
            cluster_summary = self.cluster_summary
        else:
            cluster_summary = self.cluster_summary[
                self.cluster_summary.index.isin(self.selected_cluster)
            ].reset_index(drop=True)

            self.cluster_boundary = self.cluster_boundary[
                self.cluster_boundary.index.isin(self.selected_cluster)
            ]
            self.cluster_id = self.cluster_id.loc[self.selected_cluster.index]

        return cluster_summary


    def parameter_callback(self, attr, old, new):

        self.cluster_summary, self.cluster_boundary, self.cluster_id = group.get_clusters(
            self.address, self.parameters['max_cluster_distance_miles'],
            self.distance, self.columns['date'], self.units_time, self.parameters['date_range'],
            self.additional_summary
        )
        self.selected_cluster = None
        self.update_evaluation()
        self.update_summary()
        self.table_callback(None, None, self.cluster_summary.index)