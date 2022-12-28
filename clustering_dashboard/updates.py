import pandas as pd
import numpy as np
from bokeh.models import Label

from clustering_dashboard import calculate

class updates():

    def __init__(self):
        
        self.selected_cluster = None


    def update_map(self):

        # variable field names
        time = self.columns['time']
        longitude = self.columns['longitude']
        latitude = self.columns['latitude']

        # update boundary box of each cluster
        if self.selected_cluster is not None:
            unique_clusters = self.selected_cluster.dropna().drop_duplicates()
            self.render_boundary.data_source.data = {
                'xs': self.cluster_boundary.loc[unique_clusters, '_longitude_mercator'].tolist(),
                'ys': self.cluster_boundary.loc[unique_clusters, '_latitude_mercator'].tolist(),
                time: self.details.loc[unique_clusters.index, time].tolist(),
                '_timestamp': self.details.loc[unique_clusters.index, '_timestamp'].tolist()
            }

        # update points
        if self.selected_cluster is None:
            show_ids = self.details.index
        else:
            show_ids = self.selected_cluster.index
        self.render_points.data_source.data = {
            'Cluster ID': self.details.loc[show_ids, 'Cluster ID'].fillna(-1).values,
            'Location ID': self.details.loc[show_ids, 'Location ID'].fillna(-1).values,
            'Time ID': self.details.loc[show_ids, 'Time ID'].fillna(-1).values,
            'xs': self.details.loc[show_ids, '_longitude_mercator'].values,
            'ys': self.details.loc[show_ids, '_latitude_mercator'].values,
            self.column_id: show_ids,
            longitude: self.details.loc[show_ids, longitude].values,
            latitude: self.details.loc[show_ids, latitude].values,
            time: self.details.loc[show_ids, time].values,
            '_timestamp': self.details.loc[show_ids, '_timestamp'].values
        }

        # update map title
        self.update_titles()

        # zoom in on current selected data
        zoom = self._zoom_window(self.details.loc[show_ids,['_longitude_mercator','_latitude_mercator']])
        self.plot_map.x_range.start = zoom.at['_longitude_mercator','min']
        self.plot_map.x_range.end = zoom.at['_longitude_mercator','max']
        self.plot_map.y_range.start = zoom.at['_latitude_mercator','min']
        self.plot_map.y_range.end = zoom.at['_latitude_mercator','max']


    def update_detail(self):

        if self.selected_cluster is None:
            data = dict()
        else:
            cluster = self.details[self.details['Cluster ID'].isin(self.selected_cluster)].index
            name = [col.field for col in self.table_detail.columns]
            data = self.details.loc[cluster, name]
            
        self.source_detail.data = data
        self.update_titles()


    def update_evaluation(self):

        self._histogram_evaluation(
            f'Nearest ({self.units["distance"].value})',
            self.plot_next_distance,
            self.render_next_distance
        )
        
        self._histogram_evaluation(
            f'Length ({self.units["distance"].value})',
            self.plot_span_distance,
            self.render_span_distance
        )

        self._histogram_evaluation(
            f'Nearest ({self.units["time"].value})',
            self.plot_next_date,
            self.render_next_date
        )

        self._histogram_evaluation(
            f'Length ({self.units["time"].value})',
            self.plot_span_date,
            self.render_span_date
        )


    def update_summary(self):

        cluster_summary = self._filter_clusters()

        # update summary of location id
        self.source_location.data = self.location_summary.to_dict(orient='list')

        # # update summary of time id
        self.source_time.data = self.time_summary.to_dict(orient='list')

        # update summary table
        # BUG: replace values of all empty to avoid ValueError: Out of range float values are not JSON compliant
        all_empty = cluster_summary.columns[~cluster_summary.any()]
        cluster_summary[all_empty] = '-'
        cols = [x.field for x in self.table_summary.columns]
        data = cluster_summary[cols]
        self.source_summary.data = data.to_dict(orient='list')


    def update_parameter_estimation(self):

        parameters = {
            'distance': {
                'fig': self.plot_estimate_distance,
                'renderer': self.render_estimate_distance,
                'data': calculate.nearest_point(self.distance, self.units["distance"].value)
            },
            'time': {
                'fig': self.plot_estimate_time,
                'renderer': self.render_estimate_time,
                'data': calculate.nearest_time(self.details[self.columns['time']], self.units["time"].value)
            }
        }

        for target in parameters.values():

            values = target['data'].sort_values()
            values, outliers = self._filter_outliers(values)
            
            source = {
                'x': range(0, len(values)),
                'y': values.values
            }
            target['renderer'].data_source.data = source

            label = Label(text=outliers, x=len(values), y=values.max(), text_align='right', text_baseline='top')
            target['fig'].add_layout(label)


    def update_titles(self):

        if self.selected_cluster is None:
            selected_title = 'select cluster summary to display'
        else:

            selected_title = f'{self.selected_cluster.nunique()} clusters displayed'

        self.title_map.text = f"Location and Time Clusters: {selected_title}"          


    def _zoom_window(self, df):
        '''Calculate a square zoom window using mercator x and y points.'''

        center = df.median()
        offset = pd.concat([
            (center-df.min()).abs(),
            (center-df.max()).abs()
        ]).max()
        zoom = pd.DataFrame({'min': center-offset, 'max': center+offset})

        return zoom


    def _filter_clusters(self):

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


    def _filter_outliers(self, values):

        outliers = values[values > values.mean() + 3 * values.std()]

        values = values[~values.index.isin(outliers.index)]

        if values.any():
            outliers = f'excluding {len(outliers)} points\n> {values.max():.3f}'
        else:
            outliers = 'no data'

        return values, outliers


    def _histogram_evaluation(self, column, fig, renderer):

        data = self.cluster_summary[column]

        data, outliers = self._filter_outliers(data)

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