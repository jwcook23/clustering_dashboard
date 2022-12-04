import pandas as pd
import numpy as np
from bokeh.models import Slider, Dropdown, CheckboxGroup

import group

class updates():

    def __init__(self):
        
        self.parameters = {}
        self.options = {}

        self.parameters['max_cluster_distance_miles'] = Slider(start=0.01, end=1, value=0.01, step=0.01, title="Point Distance (miles)", height=50, width=160)
        self.parameters['max_cluster_distance_miles'].on_change('value_throttled', self.parameter_callback)

        self.parameters['date_range'] = Slider(start=1, end=10, value=1, step=1, title=f"{self.columns['date']} (days between)", height=50, width=160)
        self.parameters['date_range'].on_change('value_throttled', self.parameter_callback)
        self.parameters['date_range'].visible = True

        menu = [
            ("1) Reset display.", "reset display"),
            ("2) Display clusters at same location.", "same location"),
            ("3) Display clusters at same date.", "same date")
        ]
        self.options['display'] = Dropdown(label="Display Options", button_type="default", menu=menu, height=25, width=160)
        self.options['display'].on_click(self.display_callback)

        self.options['date'] = CheckboxGroup(labels=['include date clustering'], active=[0], height=20, width=160)
        self.options['date'].on_click(self.date_callback)


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

        unique_clusters = self.selected_cluster.dropna().drop_duplicates()
        data_boundary.update({
            'xs': self.cluster_boundary.loc[unique_clusters, 'Longitude_mercator'].tolist(),
            'ys': self.cluster_boundary.loc[unique_clusters, 'Latitude_mercator'].tolist()
        })

        if len(unique_clusters)==1:

            # update address using selected cluster
            longitude = self.columns['longitude']
            latitude = self.columns['latitude']
            date = self.columns['date']
            data_point.update({
                'x': self.address.loc[show_ids, 'Longitude_mercator'].values,
                'y': self.address.loc[show_ids, 'Latitude_mercator'].values,
                self.column_id: show_ids,
                longitude: self.address.loc[show_ids, longitude].values,
                latitude: self.address.loc[show_ids, latitude].values,
                date: self.address.loc[show_ids, date].values
            })
            data_point.update({
                col: self.address.loc[show_ids, col].values for col in self.address.columns.drop([longitude,latitude,date])
            })

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
        
        hist, edges = np.histogram(self.cluster_summary['Nearest (miles)'])

        self.render_evaluation.data_source.data = {
            'left': edges[:-1],
            'right': edges[1:],
            'top': hist,
            'bottom': [0]*len(hist)
        }


    def update_summary(self):

        cols = [x.field for x in self.table_summary.columns]
        data = self.cluster_summary[cols]
        self.source_summary.data = data.to_dict(orient='list')


    def update_titles(self):

        if self.selected_cluster is None:
            selected_list = 'select cluster summary to display'
        else:

            selected_list = self.selected_cluster.drop_duplicates().sort_values()

            if len(selected_list)==len(self.cluster_summary):
                selected_list = 'All Clusters'
            else:
                selected_list = selected_list.astype('str').replace('<NA>','None').tolist()
                selected_list = 'Cluster ID = '+', '.join(selected_list)

        self.title_map.text = f"Location Clusters: {selected_list}"


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

        self.filter_clusters()
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

        self.cluster_summary = self.cluster_summary[
            self.cluster_summary.index.isin(self.selected_cluster)
        ].reset_index(drop=True)

        self.cluster_boundary = self.cluster_boundary[
            self.cluster_boundary.index.isin(self.selected_cluster)
        ]

        self.cluster_id = self.cluster_id.loc[self.selected_cluster.index]


    def parameter_callback(self, attr, old, new):

        self.cluster_summary, self.cluster_boundary, self.cluster_id = group.get_clusters(
            self.address, self.parameters['max_cluster_distance_miles'],
            self.distance, self.columns['date'], self.parameters['date_range'],
            self.additional_summary
        )
        self.update_evaluation()
        self.update_summary()
        self.table_callback(None, None, self.cluster_summary.index)