import pandas as pd

from clustering_dashboard.updates import updates
from clustering_dashboard import group, summary

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

        self.location_summary.columns = self.location_summary_columns()
        self.time_summary.columns = self.time_summary_columns()
        self.table_summary.columns = self.overall_summary_columns()
        self.parameter_selected(None, None, None)


    def parameter_selected(self, attr, old, new):

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

        # TODO: rename length to furthest in summary and where ever needed
        # self.cluster_boundary = None

        self._reset_all()


    def cluster_selected(self, attr, old, selected):

        self._select_details()
        self.update_map()
        self.update_detail()
        self.update_location()
        self.update_time()


    def location_selected(self, attr, old, selected):

        self._select_details()
        self.update_map()
        self.update_detail()
        self.update_summary()
        self.update_time()


    def time_selected(self, attr, old, selected):

        self._select_details()
        self.update_map()
        self.update_detail()
        self.update_summary()
        self.update_location()


    def _select_details(self):

        id_summary = self.source_summary.selected.indices
        id_location = self.source_location.selected.indices
        id_time = self.source_time.selected.indices

        if (len(id_location)>0) & (len(id_time)>0):
            selected = (
                self.details['Location ID'].isin(id_location) &
                self.details['Time ID'].isin(id_time)
            )
        elif len(id_location)>0:
            selected = self.details['Location ID'].isin(id_location)
        elif len(id_time)>0:
            selected = self.details['Time ID'].isin(id_time)
        elif len(id_summary)>0:
            selected = self.details['Cluster ID'].isin(id_summary)
        else:
            selected = pd.Series([True]*len(self.details))

        self.selected_details = self.details.loc[selected]


    def _reset_all(self):

        self.source_summary.selected.indices = []
        self.source_location.selected.indices = []
        self.source_time.selected.indices = []

        self.selected_details = self.details

        self.update_evaluation()
        self.update_summary()
        self.update_location()
        self.update_time()
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