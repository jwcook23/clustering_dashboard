from clustering_dashboard.updates import updates
from clustering_dashboard import group

class selections(updates):

    def __init__(self):

        updates.__init__(self)


    def landing_page():
        pass


    def parameter_selected(self, attr, old, new):

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
        self.cluster_selected(None, None, self.cluster_summary.index)


    def cluster_selected(self, attr, old, selected_cluster):

        self.selected_cluster = self.cluster_id.loc[
            self.cluster_id['Cluster ID'].isin(selected_cluster), 
            'Cluster ID'
        ]
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


    def _same_location(self):
            
        same = self.cluster_id.loc[
            self.cluster_id['Cluster ID'].isin(self.selected_cluster),
            'Location ID'
        ]
        self.selected_cluster = self.cluster_id.loc[
            self.cluster_id['Location ID'].isin(same),
            'Cluster ID'
        ]


    def _same_date(self):

        same = self.cluster_id.loc[
            self.cluster_id['Cluster ID'].isin(self.selected_cluster),
            'Time ID'
        ]
        self.selected_cluster = self.cluster_id.loc[
            self.cluster_id['Time ID'].isin(same),
            'Cluster ID'
        ] 