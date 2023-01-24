import base64
import io

import pandas as pd
from bokeh.models import Div, FileInput, Dropdown, Panel, Tabs
from bokeh.layouts import row, column

from clustering_dashboard.figures import figures


class layouts(figures):

    def __init__(self):

        self.generate_parameters()


    def generate_parameters(self):

        title_main = Div(
            text='Clustering Dashboard File Selection',
            style={'font-size': '150%', 'font-weight': 'bold'}, width=400
        )

        # BUG: allow csv files
        file_types = Div(
            text='Select a comma seperated value (.csv) or parquet (.parquet) file.'
        )

        self.file_input = FileInput(accept='.csv,.parquet')
        self.file_input.on_change('value', self._file_selected)

        title_columns = Div(
            text = 'Select columns from input file.'
        )

        self.column_options = {
            'id': Dropdown(label="Select ID Column", width=200),
            'latitude': Dropdown(label="Select Latitude Column", width=200),
            'longitude': Dropdown(label="Select Longitude Column", width=200),
            'time': Dropdown(label="Select Time Column", width=200)
        }
        self.columns = pd.Series({col:None for col in self.column_options.keys()})
        self.column_options['id'].on_click(self._id_selected)
        self.column_options['latitude'].on_click(self._latitude_selected)
        self.column_options['longitude'].on_click(self._longitude_selected)
        self.column_options['time'].on_click(self._time_selected)

        self.layout_parameters = column(
            title_main,
            file_types,
            self.file_input,
            title_columns,
            self.column_options['id'],
            self.column_options['latitude'],
            self.column_options['longitude'], 
            self.column_options['time']
        )

    def _load_data(self, buffer_or_path):

        self.details = pd.read_parquet(buffer_or_path)

        if self.details.index.name is not None:
            self.details = self.details.reset_index()

        for col in self.column_options.values():
            col.menu = list(self.details.columns)

        # TODO: allow creation of id column
        # self.column_options.menu['id'] += [None]


    def _file_selected(self, attr, old, new):

        decoded = base64.b64decode(new)
        buffer = io.BytesIO(decoded)

        self._load_data(buffer)


    def _id_selected(self, event):

        self.columns.at['id'] = event.item
        self._columns_selected()


    def _latitude_selected(self, event):

        self.columns.at['latitude'] = event.item
        self._columns_selected()


    def _longitude_selected(self, event):

        self.columns.at['longitude'] = event.item
        self._columns_selected()


    def _time_selected(self, event):

        self.columns.at['time'] = event.item
        self.details[self.columns['time']] = pd.to_datetime(self.details[self.columns['time']])
        self._columns_selected()


    def _columns_selected(self):

        if self.columns.notna().all():

            figures.__init__(self)

            self.generate_dashboard()
            self.landing_page()

            if self.document is not None:
                self.document.remove_root(self.layout_parameters)
                self.document.add_root(self.layout_dashboard)


    def generate_dashboard(self):

        title_main = Div(
            text='Clustering Dashboard',
            style={'font-size': '150%', 'font-weight': 'bold'}, width=210
        )

        bold = {'font-weight': 'bold'}

        title_distance_input = Div(text='Distance Length', style=bold)
        title_time_input = Div(text='Time Duration', style=bold)
        
        title_map = Div(text='Location and Time Clusters', style=bold, width=625)

        title_location_summary = Div(text="Location Cluster Summary", style=bold)
        self.count_location = Div()
        title_time_summary = Div(text="Time Cluster Summary", style=bold)
        self.count_time = Div()
        title_summary = Div(text="Overall Cluster Summary", style=bold)
        self.count_summary = Div()

        self.update_selected_count()

        space = Div(height=20, width=100)

        self.layout_dashboard = row(
            column(
                row(
                    column(
                        title_main,
                        row(
                            column(title_distance_input, self.units['distance'], space, self.parameters['cluster_distance']),
                            column(title_time_input, self.units['time'], space, self.parameters['cluster_time'])
                        ),
                        self.options['reset']
                    ),
                    Tabs(tabs=[
                        Panel(child=row(self.plot_estimate_distance, self.plot_estimate_time), title='Parameter Estimation'),
                        Panel(child=row(self.plot_next_distance, self.plot_span_distance), title='Distance Parameter Evaluation'),
                        Panel(child=row(self.plot_next_date, self.plot_span_date), title='Time Parameter Evalulation')
                    ])
                ),
                row(
                    column(row(title_location_summary, self.count_location), self.table_location), 
                    column(row(title_time_summary, self.count_time), self.table_time)
                ),
                column(row(title_summary, self.count_summary), self.table_summary)
            ),
            column(
                title_map,
                Tabs(tabs=[
                    Panel(child=self.plot_map, title='Location and Time Plot'), 
                    Panel(child=self.table_detail, title='Record Detail')
                ])
            )
        )