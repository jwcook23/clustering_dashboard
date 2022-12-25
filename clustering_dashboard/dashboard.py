# bokeh serve --show clustering_dashboard/dashboard.py

import json
import os

import pandas as pd
from bokeh.plotting import curdoc
from bokeh.layouts import row, column
from bokeh.models import (
    TableColumn, Div, DateFormatter, StringFormatter, 
    NumberFormatter, Panel, Tabs
)

from clustering_dashboard.figures import figures
from clustering_dashboard import calculate

class dashboard(figures):

    def __init__(self):

        self.set_format()

        figures.__init__(self)
       
        self.page_layout()


    def set_format(self):

        self.display_format = {
            'id': NumberFormatter(format='0'),
            'int': NumberFormatter(nan_format='-'),
            'float': NumberFormatter(nan_format='-', format='0.00'),
            'time': DateFormatter(format="%m/%d/%Y", nan_format='-'),
            'timestamp': DateFormatter(format="%m/%d/%Y %H:%M:%S", nan_format='-'),
            'string': StringFormatter(nan_format='-')
        }


    def is_date(self, values):

        return (values.dt.hour==0).all()


    def filter_outliers(self, values):

        outliers = values[values > values.mean() + 3 * values.std()]

        values = values[~values.index.isin(outliers.index)]

        if values.any():
            outliers = f'excluding {len(outliers)} points\n> {values.max():.3f}'
        else:
            outliers = 'no data'

        return values, outliers


    def format_table(self, df, column_widths=None):

        columns = []
        for col,values in df.items():

            if column_widths:
                width = column_widths[col]
            else:
                width = 100

            if pd.api.types.is_integer_dtype(values):
                if 'ID' in col:
                    columns += [TableColumn(field=col, formatter=self.display_format['id'], width=width)]
                else:
                    columns += [TableColumn(field=col, formatter=self.display_format['int'], width=width)]
            elif pd.api.types.is_float_dtype(values):
                columns += [TableColumn(field=col, formatter=self.display_format['float'], width=width)]
            elif pd.api.types.is_datetime64_dtype(values):
                if self.is_date(values):
                    fmt = self.display_format['time']
                else:
                    fmt = self.display_format['timestamp']
                columns += [TableColumn(field=col, formatter=fmt, width=width)]
            elif pd.api.types.is_string_dtype(values):
                columns += [TableColumn(field=col, formatter=self.display_format['string'], width=width)]
            else:
                columns += [TableColumn(field=col, formatter=self.display_format['string'], width=width)]

        return columns

    
    def format_hover(self):

        latitude = self.columns['latitude']
        longitude = self.columns['longitude']
        time = self.columns['time']
        features = [
            ('Cluster ID', "@{Cluster ID}"),
            ('Location ID', "@{Location ID}"),
            ('Time ID', "@{Time ID}"),
            (self.column_id, "@{"+self.column_id+"}"),
            (f"({latitude}/{longitude})", "(@{"+latitude+"},@{"+longitude+"})"),
            (time, "@{"+time+"}{%F}")
        ]
        formatters = {"@{"+time+"}": 'datetime'}
        # formatters = {}
        # for col,values in self.address.drop(columns=[latitude, longitude, '_latitude_mercator', '_longitude_mercator']).items():
        #     if pd.api.types.is_datetime64_dtype(values):
        #         if self.is_date(values):
        #             features += [(col, f'@{col}'+"{%F}")]
        #         else:
        #             features += [(col, f'@{col}')]
        #         formatters[f"@{col}"] = 'datetime'
        #     else:
        #         features += [(col, f'@{col}')]

        return features, formatters


    def page_layout(self):

        # self.title_main = Div(style={'font-size': '150%', 'font-weight': 'bold'}, width=170)
        self.title_map = Div(style={'font-size': '150%', 'font-weight': 'bold'}, width=625)
        self.update_titles()

        title_units = Div(text="Unit Selection", style={'font-weight': 'bold'}, height=20, width=160)
        title_parameter = Div(text="Cluster Parameters", style={'font-weight': 'bold'}, height=20, width=160)
        space = Div(height=20, width=160)
        title_summary = Div(text="Cluster Summary*", style={'font-weight': 'bold'})
        id_description = Div(text="*lower IDs have larger size")

        self.layout = row(
            column(
                row(
                    column(
                        title_units,
                        row(self.units['distance'], self.units['time']),
                        space,
                        title_parameter,
                        self.parameters['cluster_distance'], 
                        self.parameters['date_range']
                    ),
                    Tabs(tabs=[
                        Panel(child=row(self.plot_estimate_distance, self.plot_estimate_time), title='Parameter Estimation'),
                        Panel(child=row(self.plot_next_distance, self.plot_span_distance), title='Distance Parameter Evaluation'),
                        Panel(child=row(self.plot_next_date, self.plot_span_date), title='Time Parameter Evalulation')
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