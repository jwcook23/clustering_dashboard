import pandas as pd
import numpy as np

from clustering_dashboard import calculate

class updates():

    def __init__(self):
        
        self.selected_details = self.details


    def update_map(self):

        # variable field names
        time = self.columns['time']
        longitude = self.columns['longitude']
        latitude = self.columns['latitude']

        # update boundary box of each cluster
        unique_clusters = self.selected_details['Cluster ID'].dropna().drop_duplicates()
        if len(unique_clusters) > 0:
            self.render_boundary.data_source.data = {
                'xs': self.cluster_boundary.loc[unique_clusters, '_longitude_mercator'].tolist(),
                'ys': self.cluster_boundary.loc[unique_clusters, '_latitude_mercator'].tolist(),
                time: self.details.loc[unique_clusters.index, time].tolist(),
                '_timestamp': self.details.loc[unique_clusters.index, '_timestamp'].tolist()
            }

        # update points
        self.render_points.data_source.data = {
            'Cluster ID': self.selected_details['Cluster ID'].fillna(-1).values,
            'Location ID': self.selected_details['Location ID'].fillna(-1).values,
            'Time ID': self.selected_details['Time ID'].fillna(-1).values,
            'xs': self.selected_details['_longitude_mercator'].values,
            'ys': self.selected_details['_latitude_mercator'].values,
            self.columns['id']: self.selected_details[self.columns['id']].values,
            longitude: self.selected_details[longitude].values,
            latitude: self.selected_details[latitude].values,
            time: self.selected_details[time].values,
            '_timestamp': self.selected_details['_timestamp'].values
        }

        # update map title
        self.update_selected_count()

        # zoom in on current selected data
        zoom = self._zoom_window(self.selected_details[['_longitude_mercator','_latitude_mercator']])
        self.plot_map.x_range.start = zoom.at['_longitude_mercator','min']
        self.plot_map.x_range.end = zoom.at['_longitude_mercator','max']
        self.plot_map.y_range.start = zoom.at['_latitude_mercator','min']
        self.plot_map.y_range.end = zoom.at['_latitude_mercator','max']


    def update_detail(self):

        name = [col.field for col in self.table_detail.columns]
        data = self.selected_details[name].copy()
        id_cols = ['Cluster ID', 'Location ID', 'Time ID']
        data[id_cols] = data[id_cols].fillna(-1)
            
        self.source_detail.data = data
        self.update_selected_count()


    def update_evaluation(self):

        self._histogram_evaluation(
            f"Nearest Cluster ({self.units['distance'].value})",
            self.plot_next_distance,
            self.render_next_distance
        )
        
        self._histogram_evaluation(
            f"Distance ({self.units['distance'].value})",
            self.plot_span_distance,
            self.render_span_distance
        )

        self._histogram_evaluation(
            f"Nearest Cluster ({self.units['time'].value})",
            self.plot_next_date,
            self.render_next_date
        )

        self._histogram_evaluation(
            f"Duration ({self.units['time'].value})",
            self.plot_span_date,
            self.render_span_date
        )


    def update_time(self):
        
        time_summary = self.time_summary[
            self.time_summary.index.isin(self.selected_details['Time ID'])
        ].reset_index()
        self.source_time.data = time_summary.to_dict(orient='list')


    def update_location(self):

        location_summary = self.location_summary[
            self.location_summary.index.isin(self.selected_details['Location ID'])
        ].reset_index()
        self.source_location.data = location_summary.to_dict(orient='list')


    def update_summary(self, summary, source, id_name, indices=[]):

        # filter for selected clusters only if needed
        if len(indices)==0:
            summary = summary[
                summary.index.isin(self.selected_details[id_name])
            ]
        summary = summary.reset_index().copy()

        # replace values of all empty to avoid ValueError: Out of range float values are not JSON compliant
        all_empty = summary.columns[summary.isna().all()]
        summary[all_empty] = '-'

        # highlight id of selected
        summary['_selected_color'] = 'null'
        if len(indices)>0:
            summary.loc[indices, '_selected_color'] = '#ee4729'

        # update the table
        source.data = summary.to_dict(orient='list')


    def update_parameter_estimation(self):

        parameters = {
            'distance_radians': {
                'fig': self.plot_estimate_distance,
                'renderer': self.render_estimate_distance,
                'data': calculate.nearest_point(self.distance_radians, self.units["distance"].value)
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

            title = target['fig'].title.text.split('\n')
            target['fig'].title.text = f'{title[0]}\n{outliers}'


    def update_selected_count(self):

        num_clusters = self.selected_details['Cluster ID'].dropna().nunique()
        self.count_summary.text = f"({num_clusters} selected)"

        num_locations = self.selected_details['Location ID'].dropna().nunique()
        self.count_location.text = f"({num_locations} selected)"

        num_times = self.selected_details['Time ID'].dropna().nunique()
        self.count_time.text = f"({num_times} selected)"


    def _zoom_window(self, df):
        '''Calculate a square zoom window using mercator x and y points.'''

        center = df.median()
        offset = pd.concat([
            (center-df.min()).abs(),
            (center-df.max()).abs()
        ]).max()
        zoom = pd.DataFrame({'min': center-offset, 'max': center+offset})

        return zoom


    def _filter_outliers(self, values):

        outliers = values[values > values.mean() + 3 * values.std()]

        values = values[~values.index.isin(outliers.index)]

        if values.any():
            outliers = f'excluding {len(outliers)} points > {values.max():.3f}'
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

        title = fig.title.text.split('\n')
        fig.title.text = f'{title[0]}\n{outliers}'

        renderer.data_source.data = bins