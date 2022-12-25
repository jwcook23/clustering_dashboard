import pandas as pd
import numpy as np
from bokeh.models import Label, ColumnDataSource

from clustering_dashboard import group, calculate

class callbacks():

    def __init__(self):
        
        self.selected_cluster = None


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

        data_boundary = {
            'xs': [],
            'ys': []
        }
        data_point = {
            'xs': [],
            'ys': [],
        }

        time = self.columns['time']

        unique_clusters = self.selected_cluster.dropna().drop_duplicates()
        data_boundary.update({
            'xs': self.cluster_boundary.loc[unique_clusters, '_longitude_mercator'].tolist(),
            'ys': self.cluster_boundary.loc[unique_clusters, '_latitude_mercator'].tolist(),
            time: self.address.loc[unique_clusters.index, time].tolist(),
            '_timestamp': self.address.loc[unique_clusters.index, '_timestamp'].tolist()
        })

        # update address using selected cluster
        show_ids = self.selected_cluster.index
        longitude = self.columns['longitude']
        latitude = self.columns['latitude']
        data_point.update({
            'Cluster ID': self.cluster_id.loc[show_ids, 'Cluster ID'].fillna(-1).values,
            'Location ID': self.cluster_id.loc[show_ids, 'Location ID'].fillna(-1).values,
            'Time ID': self.cluster_id.loc[show_ids, 'Time ID'].fillna(-1).values,
            'xs': self.cluster_id.loc[show_ids, '_longitude_mercator'].values,
            'ys': self.cluster_id.loc[show_ids, '_latitude_mercator'].values,
            self.column_id: show_ids,
            longitude: self.cluster_id.loc[show_ids, longitude].values,
            latitude: self.cluster_id.loc[show_ids, latitude].values,
            time: self.cluster_id.loc[show_ids, time].values,
            '_timestamp': self.cluster_id.loc[show_ids, '_timestamp'].values
        })
        # data_point.update({
        #     col: self.address.loc[show_ids, col].values for col in self.address.columns.drop([longitude,latitude,time])
        # })

        # update map title
        self.update_titles()

        # plot updated data
        self.render_boundary.data_source.data = data_boundary
        self.render_points.data_source.data = data_point

        # update range to selected
        zoom = self.zoom_window(self.address.loc[show_ids,['_longitude_mercator','_latitude_mercator']])
        self.plot_map.x_range.start = zoom.at['_longitude_mercator','min']
        self.plot_map.x_range.end = zoom.at['_longitude_mercator','max']
        self.plot_map.y_range.start = zoom.at['_latitude_mercator','min']
        self.plot_map.y_range.end = zoom.at['_latitude_mercator','max']


    def update_detail(self):

        if self.selected_cluster is None:
            data = dict()
        else:
            cluster = self.cluster_id[self.cluster_id['Cluster ID'].isin(self.selected_cluster)].index
            name = [col.field for col in self.table_detail.columns]
            data = self.address.loc[cluster, name]
            
        self.source_detail.data = data
        self.update_titles()


    def histogram_evaulation(self, column, fig, renderer):

        data = self.cluster_summary[column]

        data, outliers = self.filter_outliers(data)

        hist, edges = np.histogram(data.dropna(), bins='fd')

        bins = dict(
                left=edges[:-1],
                right=edges[1:],
                top=hist,
                bottom=[0]*len(hist),
            )

        xpos = bins['right'].max()
        if np.isnan(xpos):
            xpos = 1
        ypos = bins['top'].max()

        renderer.data_source.data = bins
        fig.add_layout(Label(text=outliers, x=xpos, y=ypos, text_align='right', text_baseline='top'))


    def update_evaluation(self):

        self.histogram_evaulation(
            f'Nearest ({self.units["distance"].value})',
            self.plot_next_distance,
            self.render_next_distance
        )
        
        self.histogram_evaulation(
            f'Length ({self.units["distance"].value})',
            self.plot_span_distance,
            self.render_span_distance
        )

        self.histogram_evaulation(
            f'Nearest ({self.units["time"].value})',
            self.plot_next_date,
            self.render_next_date
        )

        self.histogram_evaulation(
            f'Length ({self.units["time"].value})',
            self.plot_span_date,
            self.render_span_date
        )


    def update_summary(self):

        cluster_summary = self.filter_clusters()

        # replace values of all empty to avoid ValueError: Out of range float values are not JSON compliant
        all_empty = cluster_summary.columns[~cluster_summary.any()]
        cluster_summary[all_empty] = '-'

        cols = [x.field for x in self.table_summary.columns]
        data = cluster_summary[cols]
        self.source_summary.data = data.to_dict(orient='list')


    def update_parameter_estimation(self):

        parameters = {
            'distance': {
                'fig': self.plot_estimate_distance,
                'render': self.render_estimate_distance,
                'data': calculate.nearest_point(self.distance, self.units["distance"].value)
            },
            'time': {
                'fig': self.plot_estimate_time,
                'renderer': self.render_estimate_time,
                'data': calculate.nearest_time(self.address[self.columns['time']], self.units["time"].value)
            }
        }

        for target in parameters.values():

            values = target['data'].sort_values()
            values, outliers = self.filter_outliers(values)
            
            source = ColumnDataSource({
                'x': range(0, len(values)),
                'y': values.values
            })
            target['renderer'].source = source

            label = Label(text=outliers, x=len(values), y=values.max(), text_align='right', text_baseline='top')
            target['fig'].add_layout(label)


    def update_titles(self):

        if self.selected_cluster is None:
            selected_title = 'select cluster summary to display'
        else:

            selected_title = f'{self.selected_cluster.nunique()} clusters displayed'

        self.title_map.text = f"Location and Time Clusters: {selected_title}"


    def table_callback(self, attr, old, selected_cluster):

        self.selected_cluster = self.cluster_id.loc[
            self.cluster_id['Cluster ID'].isin(selected_cluster), 
            'Cluster ID'
        ]
        self.update_map()
        self.update_detail()


    def display_callback(self, event):
        
        if event.item=='reset display':
            self.calculate_callback(None, None, None)
            return None
        elif event.item=='same location':
            self.same_location()
        elif event.item=='same time':
            self.same_date()

        self.update_summary()
        self.update_map()
        self.update_detail()


    def date_callback(self, event):

        if event == [0]:
            self.parameters['date_range'].visible = True
        else:
            self.parameters['date_range'].visible = False

        self.calculate_callback(None, None, None)


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
            'Time ID'
        ]
        self.selected_cluster = self.cluster_id.loc[
            self.cluster_id['Time ID'].isin(same),
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


    def calculate_callback(self, attr, old, new):

        if self.parameters['cluster_distance'].value is None or self.parameters['date_range'].value is None:
            return

        self.cluster_summary, self.cluster_boundary, self.cluster_id = group.get_clusters(
            self.address, self.parameters['cluster_distance'],
            self.distance, self.columns['time'], self.units["time"].value, self.units["distance"].value,
            self.parameters['date_range'],
            self.additional_summary
        )
        self.selected_cluster = None
        self.update_evaluation()
        self.update_summary()
        self.table_callback(None, None, self.cluster_summary.index)