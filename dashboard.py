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
from bokeh.transform import linear_cmap
from bokeh.models import (
    ColumnDataSource, DataTable, TableColumn, HoverTool, Div,
    DateFormatter, StringFormatter, NumberFormatter, DatetimeTickFormatter,
    Panel, Tabs, ColorBar, Label
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
        self.address['_timestamp'] = self.address['Pickup Time'].apply(lambda x: int(x.timestamp()*1000))

        self.distance = geo.calc_distance(self.address, self.columns['latitude'], self.columns['longitude'])

        self.find_nearest()

        self.calculate_defaults()

        self.plot_estimate_distance, self.render_estimate_distance = self.parameter_estimation(
            'Distance between Clusters', 'Point', 'miles', 'Nearest Point (miles)'
        )
        self.plot_estimate_time, self.render_estimate_time = self.parameter_estimation(
            'Time between Clusters', 'Point', 'days', 'Nearest Date (days)'
        )

        self.plot_next_distance, self.render_next_distance = self.cluster_evaluation(
            'Distance between Clusters', 'miles', '# Clusters', 'Nearest (miles)'
        )
        self.plot_span_distance, self.render_span_distance = self.cluster_evaluation(
            'Distance in Cluster', 'miles', '# Clusters', 'Length (miles)'
        )
        self.plot_next_date, self.render_next_date = self.cluster_evaluation(
            'Time between Clusters', 'days', '# Clusters', 'Nearest (days)'
        )
        self.plot_span_date, self.render_span_date = self.cluster_evaluation(
            'Time in Cluster', 'days', '# Clusters', 'Length (days)'
        )
        
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

    def find_nearest(self):

        # nearest point location
        self.distance.mask = np.eye(self.distance.shape[0], dtype=bool)
        np.fill_diagonal(self.distance.mask, True)
        self.address['Nearest Point (miles)'] = self.distance.min(axis=0) * 3958
        self.distance.mask = False
        
        # nearest date occurance
        column = self.columns['date']
        nearest = self.address[[column]].sort_values(column)
        nearest['Next'] = abs(nearest[column]-nearest[column].shift(1))
        nearest['Previous'] = abs(nearest[column]-nearest[column].shift(-1))
        nearest['Nearest Date (days)'] = nearest[['Next','Previous']].min(axis='columns')
        nearest['Nearest Date (days)'] = nearest['Nearest Date (days)'].dt.total_seconds()/60/60/24
        self.address = self.address.merge(nearest[['Nearest Date (days)']], left_index=True, right_index=True)


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


    def histogram_evaulation(self, data):

        hist, edges = np.histogram(data.dropna(), bins='fd')

        bins = dict(
                left=edges[:-1],
                right=edges[1:],
                top=hist,
                bottom=[0]*len(hist),
            )

        return bins


    def parameter_figure(self, title, xlabel, ylabel):

        fig = figure(
            title=title, width=275, height=225,
            y_axis_label = ylabel, x_axis_label=xlabel,
            toolbar_location='right', tools='pan, box_zoom, reset',
            active_drag = 'box_zoom'
        )

        return fig

    
    def filter_outliers(self, values):

        outliers = values[values > values.mean() + 3 * values.std()]

        values = values[~values.index.isin(outliers.index)]

        outliers = f'{len(outliers)} points\n> {values.max():.3f}'

        return values, outliers


    def parameter_estimation(self, title, xlabel, ylabel, column):
               
        values = self.address[column].sort_values()
        
        values, outliers = self.filter_outliers(values)

        fig = self.parameter_figure(title, xlabel, ylabel)

        source = ColumnDataSource({
            'x': range(0, len(values)),
            'y': values.values
        })

        renderer = fig.line('x','y', source=source)
        fig.add_layout(Label(text=outliers, x=len(values), y=values.max(), text_align='right', text_baseline='top'))
     
        return fig, renderer


    def cluster_evaluation(self, title, xlabel, ylabel, column):

        fig = self.parameter_figure(title, xlabel, ylabel)

        values = self.cluster_summary[column]

        values, outliers = self.filter_outliers(values)

        bins = self.histogram_evaulation(values)

        source = ColumnDataSource(bins)

        renderer = fig.quad(
            'left', 'right', 'top', 'bottom', source=source, 
            fill_color="skyblue", line_color="white"
        )
        fig.add_layout(Label(text=outliers, x=values.max(), y=bins['top'].max(), text_align='right', text_baseline='top'))

        return fig, renderer


    def format_table(self, df, column_widths=None):

        formatters = {
            'int': NumberFormatter(nan_format='-'),
            'float': NumberFormatter(nan_format='-', format='0.00'),
            'date': DateFormatter(format="%m/%d/%Y", nan_format='-'),
            'timestamp': DateFormatter(format="%m/%d/%Y %H:%M:%S", nan_format='-'),
            'string': StringFormatter(nan_format='-')
        }

        columns = []
        for col,values in df.items():

            if column_widths:
                width = column_widths[col]
            else:
                width = 100

            if pd.api.types.is_integer_dtype(values):
                columns += [TableColumn(field=col, formatter=formatters['int'], width=width)]
            elif pd.api.types.is_float_dtype(values):
                columns += [TableColumn(field=col, formatter=formatters['float'], width=width)]
            elif pd.api.types.is_datetime64_dtype(values):
                if self.is_date(values):
                    fmt = formatters['date']
                else:
                    fmt = formatters['timestamp']
                columns += [TableColumn(field=col, formatter=fmt, width=width)]
            elif pd.api.types.is_string_dtype(values):
                columns += [TableColumn(field=col, formatter=formatters['string'], width=width)]
            else:
                columns += [TableColumn(field=col, formatter=formatters['string'], width=width)]

        return columns

    
    def format_hover(self):

        latitude = self.columns['latitude']
        longitude = self.columns['longitude']
        date = self.columns['date']
        features = [
            (self.column_id, "@{"+self.column_id+"}"),
            (f"({latitude}/{longitude})", "(@{"+latitude+"},@{"+longitude+"})"),
            (date, "@{"+date+"}{%F}")
        ]
        formatters = {"@{"+date+"}": 'datetime'}
        # formatters = {}
        # for col,values in self.address.drop(columns=[latitude, longitude, 'Latitude_mercator', 'Longitude_mercator']).items():
        #     if pd.api.types.is_datetime64_dtype(values):
        #         if self.is_date(values):
        #             features += [(col, f'@{col}'+"{%F}")]
        #         else:
        #             features += [(col, f'@{col}')]
        #         formatters[f"@{col}"] = 'datetime'
        #     else:
        #         features += [(col, f'@{col}')]

        return features, formatters


    def map_plot(self):

        # generate map
        self.plot_map = figure(
            x_range=self.default_zoom.loc['x'], y_range=self.default_zoom.loc['y'],
            x_axis_type="mercator", y_axis_type="mercator", title=None,
            height=625, width=625,
            x_axis_label=self.columns['longitude'], y_axis_label = self.columns['latitude'],
            toolbar_location='right', tools='pan, box_zoom, zoom_out, zoom_in, reset',
            active_drag = 'pan'
        )
        tile_provider = get_provider(CARTODBPOSITRON)
        self.plot_map.add_tile(tile_provider)

        # add color scale for date
        cmap = linear_cmap(field_name='_timestamp', palette='Turbo256', low=min(self.address['_timestamp']), high=max(self.address['_timestamp']))
        color_bar = ColorBar(color_mapper=cmap['transform'], 
            # title=self.columns['date'], 
            formatter=DatetimeTickFormatter()
        )
        self.plot_map.add_layout(color_bar, 'above')        

        # render address points
        source = ColumnDataSource(data=dict(x=[], y=[], date=[], _timestamp=[]))
        self.render_points = self.plot_map.circle('x','y', source=source, fill_color=cmap, line_color=None, size=10, legend_label='Location')
        features, formatters = self.format_hover()
        self.plot_map.add_tools(HoverTool(
            tooltips=features,
            formatters=formatters,
            renderers=[self.render_points])
        )

        # render boundary of clusters
        source = ColumnDataSource(data=dict(x=[], y=[], date=[], _timestamp=[]))
        self.render_boundary = self.plot_map.multi_polygons('xs', 'ys', source=source, color=cmap, alpha=0.3, line_color=None, legend_label='Cluster')

        self.plot_map.legend.location = "top_right"


    def summary_table(self):

        column_widths = {
            '# Points': 50,
            'Location ID': 70,
            'Date ID': 50, 
            'Nearest (miles)': 90, 
            'Length (miles)': 80, 
            'Time (first)': 120, 
            'Length (days)': 80, 
            'Nearest (days)': 80
        }

        columns = self.format_table(self.cluster_summary, column_widths)

        self.source_summary = ColumnDataSource(data=dict())
        self.source_summary.data = self.cluster_summary.to_dict(orient='list')
        self.table_summary = DataTable(
            source=self.source_summary, columns=columns, index_header='Cluster ID', index_width=60,
            autosize_mode='none', height=300, width=700)
        self.source_summary.selected.on_change('indices', self.table_callback)


    def cluster_detail(self):

        ignore = self.columns.loc[['latitude','longitude']].tolist()
        ignore += ['Longitude_mercator','Latitude_mercator']
        columns = self.format_table(self.address.drop(columns=ignore))

        self.source_detail = ColumnDataSource(data=dict())
        self.table_detail = DataTable(source=self.source_detail, columns=columns, autosize_mode='fit_columns', height=625, width=625)        


    def page_layout(self):

        self.title_main = Div(style={'font-size': '150%', 'font-weight': 'bold'}, width=170)
        self.title_map = Div(style={'font-size': '150%', 'font-weight': 'bold'}, width=625)
        self.update_titles()

        title_parameter = Div(text="Cluster Parameters", style={'font-weight': 'bold'}, height=20, width=160)
        title_summary = Div(text="Cluster Summary*", style={'font-weight': 'bold'})
        id_description = Div(text="*lower IDs have larger size")

        self.layout = row(
            column(
                row(
                    column(
                        self.title_main,
                        title_parameter, 
                        self.parameters['max_cluster_distance_miles'], 
                        self.parameters['date_range']
                    ),
                    Tabs(tabs=[
                        Panel(child=row(self.plot_estimate_distance, self.plot_estimate_time), title='Parameter Estimation'),
                        Panel(child=row(self.plot_next_distance, self.plot_span_distance), title='Distance Parameter Evaluation'),
                        Panel(child=row(self.plot_next_date, self.plot_span_date), title='Date Parameter Evalulation')
                    ])
            ),
                row(title_summary, self.options['display']),
                id_description,
                self.table_summary
            ),
            column(
                self.title_map,
                Tabs(tabs=[
                    Panel(child=self.plot_map, title='Location and Time Plot'), 
                    Panel(child=self.table_detail, title='Record Detail')
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

    # plot second largest
    page.table_callback(None, None, [1])

    # # enable date clustering
    # page.date_callback([0])

    # display nearby points
    dropdown = Event()
    dropdown.item = 'same location'
    page.display_callback(dropdown)

    # adjuster parameter
    # page.parameters['max_cluster_distance_miles'].value = 0.01
    # page.parameter_callback(None, None, None)

    # # plot second largest
    # page.table_callback(None, None, [1])

    output_file("test.html")
    show(page.layout)