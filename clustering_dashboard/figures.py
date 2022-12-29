import pandas as pd
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.transform import linear_cmap
from bokeh.models import (
    ColumnDataSource, DataTable, HoverTool, ColorBar, 
    DatetimeTickFormatter, TableColumn, Dropdown, Select, 
    NumericInput, TableColumn, DateFormatter, StringFormatter, NumberFormatter
)

from clustering_dashboard.data import data
from clustering_dashboard.selections import selections

class figures(data, selections):

    def __init__(self):

        self._set_format()

        data.__init__(self)
        selections.__init__(self)

        self.units = {}
        self.units_distance()
        self.units_time()

        self.parameters = {}
        self.parameter_distance()
        self.parameter_time()

        self.options = {}
        self.related_clusters()

        self.parameter_estimate()
        self.distance_evaluation()
        self.time_evaluation()
        self.summary_id()
        self.summary_table()
        self.cluster_map()
        self.cluster_detail()


    def units_distance(self):

        self.units['distance'] = Select(title='Distance:', value="miles", options=["miles", "feet", "kilometers"], height=25, width=75)
        self.units['distance'].on_change('value', self.parameter_selected)


    def units_time(self):

        self.units['time'] = Select(title='Time:', value="hours", options=["days", "hours", "minutes"], height=25, width=75)
        self.units['time'].on_change('value', self.parameter_selected)


    def parameter_distance(self):

        self.parameters['cluster_distance'] = NumericInput(value=None, mode='float', title=f'Location Distance ({self.units["distance"].value}):', height=50, width=160)
        self.parameters['cluster_distance'].on_change('value', self.parameter_selected)

    def parameter_time(self):

        self.parameters['date_range'] = NumericInput(value=None, mode='float', title=f'Time Duration ({self.units["time"].value}):', height=50, width=160)
        self.parameters['date_range'].on_change('value', self.parameter_selected)


    def related_clusters(self):

        menu = [
            ("1) Reset display.", "reset display"),
            ("2) Display clusters with same Location ID.", "same location"),
            ("3) Display clusters with same Time ID.", "same time")
        ]
        self.options['display'] = Dropdown(label="related clusters", button_type="default", menu=menu, height=25, width=150)
        self.options['display'].on_click(self.relation_selected)


    def parameter_estimate(self):

        self.plot_estimate_distance, self.render_estimate_distance = self._plot_line(
            'Distance between Clusters', 'Point', self.units["distance"].value
        )
        self.plot_estimate_time, self.render_estimate_time = self._plot_line(
            'Time between Clusters', 'Point', self.units["time"].value
        )


    def distance_evaluation(self):
        self.plot_next_distance, self.render_next_distance = self._plot_histogram(
            'Distance between Clusters', self.units["distance"].value, '# Clusters'
        )

        self.plot_span_distance, self.render_span_distance = self._plot_histogram(
            'Distance in Cluster', self.units["distance"].value, '# Clusters'
        )


    def time_evaluation(self):

        self.plot_next_date, self.render_next_date = self._plot_histogram(
            'Time between Clusters', self.units["time"].value, '# Clusters'
        )

        self.plot_span_date, self.render_span_date = self._plot_histogram(
            'Time in Cluster', self.units["time"].value, '# Clusters'
        )


    def summary_id(self):

        self.table_location, self.source_location = self._id_table('Location ID')
        self.source_location.selected.on_change('indices', self.location_selected)
        
        self.table_time, self.source_time = self._id_table('Time ID')
        self.source_time.selected.on_change('indices', self.time_selected)


    def summary_table(self):

        columns = [
            TableColumn(field="# Points", formatter=self.display_format['int'], width=50),
            TableColumn(field="Location ID", formatter=self.display_format['id'], width=70),
            TableColumn(field="Time ID", formatter=self.display_format['id'], width=50),
            TableColumn(field=f"Nearest ({self.units['distance'].value})", formatter=self.display_format['float'], width=90),
            TableColumn(field=f"Length ({self.units['distance'].value})", formatter=self.display_format['float'], width=80),
            TableColumn(field='Time (first)', formatter=self.display_format['timestamp'], width=120),
            TableColumn(field=f"Length ({self.units['time'].value})", formatter=self.display_format['float'], width=80),
            TableColumn(field=f"Nearest ({self.units['time'].value})", formatter=self.display_format['float'], width=80)
        ]

        self.source_summary = ColumnDataSource(data=dict())
        self.table_summary = DataTable(
            source=self.source_summary, columns=columns, index_header='Cluster ID', index_width=60,
            autosize_mode='none', height=300, width=700)
        self.source_summary.selected.on_change('indices', self.cluster_selected)


    def cluster_detail(self):

        ignore = self.columns.loc[['latitude','longitude']].tolist()
        ignore += ['_longitude_mercator','_latitude_mercator']
        columns = self._format_table(self.details.drop(columns=ignore))

        self.source_detail = ColumnDataSource(data=dict())
        self.table_detail = DataTable(source=self.source_detail, columns=columns, autosize_mode='fit_columns', height=625, width=625)        


    def cluster_map(self):

        points = self.details[['_longitude_mercator','_latitude_mercator']].rename(columns={'_longitude_mercator': 'x', '_latitude_mercator': 'y'})
        self.default_zoom = self._zoom_window(points)

        # generate map
        self.plot_map = figure(
            x_range=self.default_zoom.loc['x'], y_range=self.default_zoom.loc['y'],
            x_axis_type="mercator", y_axis_type="mercator", title=None,
            height=625, width=625,
            x_axis_label=self.columns['longitude'], y_axis_label = self.columns['latitude'],
            toolbar_location='right', tools='pan, wheel_zoom, zoom_out, zoom_in, reset',
            active_drag = 'pan', active_scroll = 'wheel_zoom'
        )
        tile_provider = get_provider(CARTODBPOSITRON)
        self.plot_map.add_tile(tile_provider)

        # add color scale for time
        cmap = linear_cmap(field_name='_timestamp', palette='Turbo256', low=min(self.details['_timestamp']), high=max(self.details['_timestamp']))
        color_bar = ColorBar(color_mapper=cmap['transform'], 
            # title=self.columns['time'], 
            formatter=DatetimeTickFormatter()
        )
        self.plot_map.add_layout(color_bar, 'above')        

        # render loction points
        source = ColumnDataSource(data=dict(xs=[], ys=[], time=[], _timestamp=[]))
        self.render_points = self.plot_map.circle('xs','ys', source=source, fill_color=cmap, line_color=None, size=10, legend_label='Location')
        features, formatters = self._format_hover()
        self.plot_map.add_tools(HoverTool(
            tooltips=features,
            formatters=formatters,
            renderers=[self.render_points])
        )

        # render boundary of clusters
        source = ColumnDataSource(data=dict(xs=[], ys=[], time=[], _timestamp=[]))
        self.render_boundary = self.plot_map.multi_polygons('xs', 'ys', source=source, color=cmap, alpha=0.3, line_color=None, legend_label='Cluster')

        self.plot_map.legend.location = "top_right"


    def _set_format(self):

        self.display_format = {
            'id': NumberFormatter(format='0'),
            'int': NumberFormatter(nan_format='-'),
            'float': NumberFormatter(nan_format='-', format='0.00'),
            'time': DateFormatter(format="%m/%d/%Y", nan_format='-'),
            'timestamp': DateFormatter(format="%m/%d/%Y %H:%M:%S", nan_format='-'),
            'string': StringFormatter(nan_format='-')
        }


    def _format_table(self, df, column_widths=None):

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
                if self._isdate(values):
                    fmt = self.display_format['time']
                else:
                    fmt = self.display_format['timestamp']
                columns += [TableColumn(field=col, formatter=fmt, width=width)]
            elif pd.api.types.is_string_dtype(values):
                columns += [TableColumn(field=col, formatter=self.display_format['string'], width=width)]
            else:
                columns += [TableColumn(field=col, formatter=self.display_format['string'], width=width)]

        return columns

    
    def _format_hover(self):

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
        # for col,values in self.details.drop(columns=[latitude, longitude, '_latitude_mercator', '_longitude_mercator']).items():
        #     if pd.api.types.is_datetime64_dtype(values):
        #         if self._isdate(values):
        #             features += [(col, f'@{col}'+"{%F}")]
        #         else:
        #             features += [(col, f'@{col}')]
        #         formatters[f"@{col}"] = 'datetime'
        #     else:
        #         features += [(col, f'@{col}')]

        return features, formatters


    def _isdate(self, values):

        return (values.dt.hour==0).all()


    def _figure_common(self, title, xlabel, ylabel):

        fig = figure(
            title=title, width=275, height=225,
            y_axis_label = ylabel, x_axis_label=xlabel,
            toolbar_location='right', tools='pan, box_zoom, reset',
            active_drag = 'box_zoom'
        )

        return fig


    def _plot_line(self, title, xlabel, ylabel):

        fig = self._figure_common(title, xlabel, ylabel)

        source = ColumnDataSource({'x': [], 'y': []})

        renderer = fig.line('x','y', source=source)
     
        return fig, renderer


    def _plot_histogram(self, title, xlabel, ylabel):

        fig = self._figure_common(title, xlabel, ylabel)

        source = ColumnDataSource({'left': [], 'right': [], 'top': [], 'bottom': []})

        renderer = fig.quad(
            'left', 'right', 'top', 'bottom', source=source, 
            fill_color="skyblue", line_color="white"
        )

        return fig, renderer


    def _id_table(self, id_column):

        columns = [
            TableColumn(field="# Clusters", formatter=self.display_format['int'], width=70),
            TableColumn(field="# Unassigned Points", formatter=self.display_format['int'], width=120),            
        ]

        source = ColumnDataSource(data=dict())
        summary = DataTable(
            source=source, columns=columns, index_header=id_column, index_width=60,
            autosize_mode='none', height=100, width=270
        )
        return summary, source