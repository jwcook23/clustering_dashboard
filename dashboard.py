# bokeh serve --show dashboard.py

import json
import os
import argparse
import ast

import pandas as pd
import numpy as np
from bokeh.plotting import figure, curdoc
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.layouts import row, column
from bokeh.models import (
    ColumnDataSource, DataTable, TableColumn, HoverTool, Div,
    DateFormatter, StringFormatter, NumberFormatter, 
    Panel, Tabs
)

from callbacks import updates
import group
import geo

class dashboard(updates):

    def __init__(self):


        self.load_settings()
        self.load_data()

        updates.__init__(self)

        self.address = geo.convert_to_mercator(self.address, self.columns['latitude'], self.columns['longitude'])
        self.distance = geo.calc_distance(self.address, self.columns['latitude'], self.columns['longitude'])

        self.calculate_defaults()
        self.cluster_evaluation()
        self.summary_table()
        self.map_plot()
        self.cluster_detail()
        self.page_layout()

        # display all clusters
        self.table_callback(None, None, self.cluster_summary.index)

    def load_settings(self):

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'settings.json')) as fh:
            settings = json.load(fh)

        self.file_path = settings['file_path']
        self.columns = pd.Series(settings['column_names'])
        self.additional_summary = settings['additional_summary']


    def load_data(self):

        self.address = pd.read_parquet(self.file_path)
        self.column_id = self.address.index.name


    def calculate_defaults(self):

        self.selected_cluster = None

        # set zoom box as range of coordinates
        points = self.address[['Longitude_mercator','Latitude_mercator']].rename(columns={'Longitude_mercator': 'x', 'Latitude_mercator': 'y'})
        self.default_zoom = self.zoom_window(points)

        # summary based on parameters
        self.cluster_summary, self.cluster_boundary, self.cluster_id = group.get_clusters(
            self.address, self.parameters['max_cluster_distance_miles'],
            self.distance, self.columns['date'], self.parameters['date_range'],
            self.additional_summary
        )


    def is_date(self, values):

        return (values.dt.hour==0).all()


    def cluster_evaluation(self):

        self.next_cluster = figure(
            title="Distance Between Clusters", width=225, height=200,
            toolbar_location=None
        )

        hist, edges = np.histogram(self.cluster_summary['Next Cluster (miles)'])

        source = ColumnDataSource(dict(
                left=edges[:-1],
                right=edges[1:],
                top=hist,
                bottom=[0]*len(hist),
            )
        )

        self.render_evaluation = self.next_cluster.quad(
            'left', 'right', 'top', 'bottom', source=source, 
            fill_color="skyblue", line_color="white"
        )


    def format_table(self, df):

        formatters = {
            'int': NumberFormatter(nan_format='-'),
            'float': NumberFormatter(nan_format='-'),
            'date': DateFormatter(format="%m/%d/%Y", nan_format='-'),
            'timestamp': DateFormatter(format="%m/%d/%Y %H:%M:%S", nan_format='-'),
            'string': StringFormatter(nan_format='-')
        }

        columns = []
        for col,values in df.items():
            if pd.api.types.is_integer_dtype(values):
                columns += [TableColumn(field=col, formatter=formatters['int'])]
            elif pd.api.types.is_float_dtype(values):
                columns += [TableColumn(field=col, formatter=formatters['float'])]
            elif pd.api.types.is_datetime64_dtype(values):
                if self.is_date(values):
                    fmt = formatters['date']
                else:
                    fmt = formatters['timestamp']
                columns += [TableColumn(field=col, formatter=fmt)]
            elif pd.api.types.is_string_dtype(values):
                columns += [TableColumn(field=col, formatter=formatters['string'])]

        return columns

    
    def format_hover(self):

        latitude = self.columns['latitude']
        longitude = self.columns['longitude']
        features = [
            (self.column_id, f"@{self.column_id}"),
            (f"({latitude}/{longitude})", f"(@{latitude},@{longitude})"),
        ]
        formatters = {}
        for col,values in self.address.drop(columns=[latitude, longitude, 'Latitude_mercator', 'Longitude_mercator']).items():
            if pd.api.types.is_datetime64_dtype(values):
                if self.is_date(values):
                    features += [(col, f'@{col}'+"{%F}")]
                else:
                    features += [(col, f'@{col}')]
                formatters[f"@{col}"] = 'datetime'
            else:
                features += [(col, f'@{col}')]

        return features, formatters


    def map_plot(self):

        # generate map
        tile_provider = get_provider(CARTODBPOSITRON)
        self.plot_map = figure(
            x_range=self.default_zoom.loc['x'], y_range=self.default_zoom.loc['y'],
            x_axis_type="mercator", y_axis_type="mercator", title=None,
            height=625, width=900,
            toolbar_location='right',
            x_axis_label=self.columns['longitude'], y_axis_label = self.columns['latitude'],
            tools='pan, wheel_zoom, zoom_out, zoom_in, tap, reset',
            active_drag = 'pan', active_scroll = 'wheel_zoom', active_tap = 'tap'
        )
        self.plot_map.add_tile(tile_provider)

        # render address points
        source_points = ColumnDataSource(data=dict(x=[], y=[]))
        self.render_points = self.plot_map.circle('x','y', source=source_points, fill_color='red', line_color=None, size=10, legend_label='Location')
        features, formatters = self.format_hover()
        self.plot_map.add_tools(HoverTool(
            tooltips=features,
            formatters=formatters,
            renderers=[self.render_points])
        )

        # render boundary of clusters
        self.render_boundary = self.plot_map.multi_polygons(xs=[],ys=[], line_color=None, alpha=0.3, color='red', legend_label='Cluster')

        self.plot_map.legend.location = "top_right"


    def summary_table(self):

        columns = self.format_table(self.cluster_summary)

        self.source_summary = ColumnDataSource(data=dict())
        self.source_summary.data = self.cluster_summary.to_dict(orient='list')
        self.table_summary = DataTable(source=self.source_summary, columns=columns, autosize_mode='fit_columns', height=300, width=550)
        self.source_summary.selected.on_change('indices', self.table_callback)


    def cluster_detail(self):

        ignore = self.columns.loc[['latitude','longitude']].tolist()
        ignore += ['Longitude_mercator','Latitude_mercator']
        columns = self.format_table(self.address.drop(columns=ignore))

        self.source_detail = ColumnDataSource(data=dict())
        self.table_detail = DataTable(source=self.source_detail, columns=columns, autosize_mode='fit_columns', height=625, width=900)        


    def page_layout(self):

        self.title_map = Div(style={'font-size': '150%'}, width=450)
        self.update_titles()

        title_parameter = Div(text="Cluster Parameters", height=20, width=160)
        title_summary = Div(text="Cluster Summary")

        self.layout = row(
            column(
                row(column(title_parameter, self.options['date']), self.parameters['max_cluster_distance_miles'], self.parameters['date_range']),
                self.next_cluster,
                row(title_summary, self.options['display']),
                self.table_summary
            ),
            column(
                self.title_map,
                Tabs(tabs=[
                    Panel(child=self.plot_map, title='Location Plot'), 
                    Panel(child=self.table_detail, title='Location Detail')
                ])
            )
        )


# initialize server app
page = dashboard()
curdoc().add_root(page.layout)

parser = argparse.ArgumentParser()
parser.add_argument('--debug', type=ast.literal_eval, required=False, default=False)
args = parser.parse_args()
if args.debug:
    # TODO: move to tests
    from bokeh.events import Event
    from bokeh.plotting import output_file, show

    # plot largest
    # page.table_callback(None, None, [0])

    # # enable date clustering
    # page.date_callback([0])

    # # display nearby points
    # dropdown = Event()
    # dropdown.item = '1) Display nearby points in any cluster.'
    # page.display_callback(dropdown)

    # adjuster parameter
    page.parameters['max_cluster_distance_miles'].value = 0.01
    page.reset_callback(None, None, None)

    # # plot second largest
    # page.table_callback(None, None, [1])

    output_file("test.html")
    show(page.layout)