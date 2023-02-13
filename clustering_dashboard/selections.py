import pandas as pd

from clustering_dashboard.updates import updates
from clustering_dashboard import group, summary, convert

class selections(updates):

    def __init__(self):

        updates.__init__(self)


    def landing_page(self):

        self.cluster_summary = None
        self.location_summary = None
        self.time_summary = None
        self.cluster_boundary = None
        
        self.update_parameter_estimation()
        self.update_map()
        # clear cluster summary
        # clear cluster detail
        # clear cluster evaluation


    def units_selected(self, attr, old, new):

        self.plot_estimate_distance.yaxis.axis_label = self.units["distance"].value
        self.plot_estimate_time.yaxis.axis_label = self.units["time"].value
        self.update_parameter_estimation()

        self.plot_next_distance.xaxis.axis_label = self.units["distance"].value
        self.plot_span_distance.xaxis.axis_label = self.units["distance"].value
        self.plot_next_date.xaxis.axis_label = self.units["time"].value
        self.plot_span_date.xaxis.axis_label = self.units["time"].value
            
        self.reset_all()


    def reset_click(self, event):

        self.reset_all()


    def reset_change(self, attr, old, new):

        self.reset_all()


    def reset_all(self):

        if self.parameters['cluster_distance'].value is None or self.parameters['cluster_time'].value is None:
            return

        self.details = group.get_clusters(
            self.details,
            self.distance_radians, self.units['distance'].value, self.parameters['cluster_distance'].value,
            self.duration_seconds, self.units['time'].value, self.parameters['cluster_time'].value
        )

        self.location_summary = summary.get_location_summary(
            self.details, self.distance_radians, self.units['distance'].value
        )
        
        self.time_summary = summary.get_time_summary(
            self.details, self.duration_seconds, self.units['time'].value
        )

        self.cluster_summary, self.details, self.cluster_boundary = summary.get_cluster_summary(
            self.details, 
            self.distance_radians, self.units['distance'].value, 
            self.duration_seconds, self.units['time'].value,
            self.columns['time']
        )
        self.update_summary_points()
        self.update_summary_first()

        self.table_location.columns = self.location_summary_columns()
        self.table_time.columns = self.time_summary_columns()
        self.table_summary.columns = self.overall_summary_columns()

        self.source_summary.selected.indices = []
        self.source_location.selected.indices = []
        self.source_time.selected.indices = []

        self.selected_details = self.details

        self.update_evaluation()
        self.location_summary = self.update_summary(self.location_summary, self.source_location, 'Location ID')
        self.time_summary = self.update_summary(self.time_summary, self.source_time, 'Time ID')
        self.cluster_summary = self.update_summary(self.cluster_summary, self.source_summary, 'Cluster ID')
        self.update_map()
        self.update_detail()


    def update_summary_points(self):

        values = self.cluster_summary['# Points'].agg(['min','max'])
        self.summary_points.start = values['min']
        self.summary_points.end = values['max']
        self.summary_points.value = values['min']


    def update_summary_first(self):

        values = self.cluster_summary['Time (first)'].agg(['min','max'])
        self.summary_first.value=(values['min'], values['max'])
        self.summary_first.start = values['min']
        self.summary_first.end = values['max']
        self.summary_first.step = int(convert.time_to_seconds(self.parameters['cluster_time'].value, self.units['time'].value)*1000)


    def filter_cluster_summary(self, attr, old, new):

        indices = self.cluster_summary.index[
            (
                (self.cluster_summary['Time (first)']>=pd.Timestamp(self.summary_first.value[0]*1000000)) &
                (self.cluster_summary['Time (first)']<=pd.Timestamp(self.summary_first.value[1]*1000000))
            ) & (
                self.cluster_summary['# Points'] >= self.summary_points.value
            )
        ]

        self.cluster_summary = self.update_summary(self.cluster_summary, self.source_summary, 'Cluster ID', indices_filter=indices)

        self.update_summary_points()
        self.update_summary_first()


    def table_row_selected(self, attr, old, new):

        id_location = self.source_location.selected.indices
        id_time = self.source_time.selected.indices
        id_summary = self.source_summary.selected.indices

        if len(id_location)>0:
            # highlight location table
            self.location_summary = self.update_summary(self.location_summary, self.source_location, 'Location ID', indices_highlight=id_location)
            selected = self.details['Location ID'].isin(id_location)
            # cross filter time table
            indices_filter = self.details.loc[selected,'Time ID'].dropna().unique()
            self.time_summary = self.update_summary(self.time_summary, self.source_time, 'Time ID', indices_filter=indices_filter)
            # cross filter summary table
            indices_filter = self.details.loc[selected,'Cluster ID'].dropna().unique()
            self.time_summary = self.update_summary(self.cluster_summary, self.source_summary, 'Cluster ID', indices_filter=indices_filter)
        if len(id_time)>0:
            # highlight time table
            self.time_summary = self.update_summary(self.time_summary, self.source_time, 'Time ID', indices_highlight=id_time)
            selected = self.details['Time ID'].isin(id_time)
            # cross filter location table
            indices_filter = self.details.loc[selected,'Location ID'].dropna().unique()
            self.location_summary = self.update_summary(self.location_summary, self.source_location, 'Location ID', indices_filter=indices_filter)
            # cross filter summary table
            indices_filter = self.details.loc[selected,'Cluster ID'].dropna().unique()
            self.time_summary = self.update_summary(self.cluster_summary, self.source_summary, 'Cluster ID', indices_filter=indices_filter)
        if len(id_summary)>0:
            # highlight summary table
            self.cluster_summary = self.update_summary(self.cluster_summary, self.source_summary, 'Cluster ID', indices_highlight=id_summary)
            selected = self.details['Cluster ID'].isin(id_summary)
            # cross filter time table
            indices_filter = self.details.loc[selected,'Time ID'].dropna().unique()
            self.time_summary = self.update_summary(self.time_summary, self.source_time, 'Time ID', indices_filter=indices_filter)
            # cross filter location table
            indices_filter = self.details.loc[selected,'Location ID'].dropna().unique()
            self.location_summary = self.update_summary(self.location_summary, self.source_location, 'Location ID', indices_filter=indices_filter)            

        selected = (
            self.details['Location ID'].isin(self.location_summary.iloc[id_location].index) |
            self.details['Time ID'].isin(self.time_summary.iloc[id_time].index) |
            self.details['Cluster ID'].isin(self.cluster_summary.iloc[id_summary].index)
        )
        self.selected_details = self.details.loc[selected]

        self.update_map()
        self.update_detail()


    def _same_location(self):
            
        same = self.details.loc[
            self.details['Cluster ID'].isin(self.selected_details),
            'Location ID'
        ]
        self.selected_details = self.details.loc[
            self.details['Location ID'].isin(same),
            'Cluster ID'
        ]


    def _same_date(self):

        same = self.details.loc[
            self.details['Cluster ID'].isin(self.selected_details),
            'Time ID'
        ]
        self.selected_details = self.details.loc[
            self.details['Time ID'].isin(same),
            'Cluster ID'
        ] 