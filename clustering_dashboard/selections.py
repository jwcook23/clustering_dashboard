import pandas as pd

from clustering_dashboard.updates import updates
from clustering_dashboard import group

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


    def parameter_selected(self, attr, old, new):

        if self.parameters['cluster_distance'].value is None or self.parameters['date_range'].value is None:
            return

        self.cluster_summary, self.location_summary, self.time_summary, self.cluster_boundary, self.details = group.get_clusters(
            self.details, self.parameters['cluster_distance'],
            self.distance, self.columns['time'], self.units["time"].value, self.units["distance"].value,
            self.parameters['date_range'],
            self.additional_summary
        )
        self.selected_details = self.details
        self.update_evaluation()
        self.update_summary()
        # self.cluster_selected(None, None, self.cluster_summary.index)
        self.update_map()
        self.update_detail()


    def cluster_selected(self, attr, old, selected):

        self._select_details()
        self.update_map()
        self.update_detail()

    def location_selected(self, attr, old, selected):

        # TODO: how are they multiple Location IDs and Time IDs both of 0?

        self._select_details()
        self.update_map()
        self.update_detail()


    def time_selected(self, attr, old, selected):

        self._select_details()
        self.update_map()
        self.update_detail()


    def relation_selected(self, event):
        
        if event.item=='reset display':
            self.parameter_selected(None, None, None)
            return None
        elif event.item=='same location':
            self._same_location()
        elif event.item=='same time':
            self._same_date()

        self.update_summary()
        self.update_map()
        self.update_detail()


    def _select_details(self):

        # TODO: update titles to show what is selected
        # TODO: add a reset button

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