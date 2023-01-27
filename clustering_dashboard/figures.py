import pandas as pd
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.transform import linear_cmap
from bokeh.models import (
    ColumnDataSource, DataTable, HoverTool, ColorBar, 
    DatetimeTickFormatter, TableColumn, Button, Select, 
    NumericInput, TableColumn, DateFormatter, StringFormatter, NumberFormatter,
    HTMLTemplateFormatter
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
        self.set_options()

        self.parameter_estimate()
        self.distance_evaluation()
        self.time_evaluation()
        self.location_cluster_summary()
        self.time_cluster_summary()
        self.overall_cluster_summary()
        self.cluster_map()
        self.cluster_detail()


    def units_distance(self):

        self.units['distance'] = Select(title='Units:', value="miles", options=["miles", "feet", "kilometers"], height=25, width=100)
        self.units['distance'].on_change('value', self.units_selected)


    def units_time(self):

        self.units['time'] = Select(title='Units:', value="minutes", options=["days", "hours", "minutes"], height=25, width=100)
        self.units['time'].on_change('value', self.units_selected)


    def parameter_distance(self):

        self.parameters['cluster_distance'] = NumericInput(value=None, mode='float', title='Parameter:', height=50, width=100)
        self.parameters['cluster_distance'].on_change('value', self.parameter_selected)


    def parameter_time(self):

        self.parameters['cluster_time'] = NumericInput(value=None, mode='float', title='Parameter:', height=50, width=100)
        self.parameters['cluster_time'].on_change('value', self.parameter_selected)


    def set_options(self):

        self.options['reset'] = Button(label="Reset Table Selections", button_type="default", width=200, height=30)
        self.options['reset'].on_click(self._reset_all)


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


    def location_summary_columns(self):

        columns = [
            TableColumn(field="Location ID", formatter=self.highlight_cell, width=70),
            TableColumn(field="# Clusters", formatter=self.display_format['int'], width=70),
            TableColumn(field=f"Distance ({self.units['distance'].value})", 
                formatter=self.display_format['float'], width=100
            ),
            TableColumn(field=f"Nearest Cluster ({self.units['distance'].value})", 
                formatter=self.display_format['float'], width=120
            )
        ]

        return columns


    def location_cluster_summary(self):

        columns = self.location_summary_columns()

        self.source_location = ColumnDataSource(data=dict())
        self.table_location = DataTable(
            source=self.source_location, columns=columns, index_position=None,
            autosize_mode='none', height=100, width=380
        )
        
        self.source_location.selected.on_change('indices', self.table_row_selected)
        

    def time_summary_columns(self):

        columns = [
            TableColumn(field='Time ID', formatter=self.highlight_cell, width=50),
            TableColumn(field="# Clusters", formatter=self.display_format['int'], width=70),
            TableColumn(field=f"Duration ({self.units['time'].value})", 
                formatter=self.display_format['float'], width=100
            ),
            TableColumn(field=f"Nearest Cluster ({self.units['time'].value})", 
                formatter=self.display_format['float'], width=130
            )         
        ]

        return columns


    def time_cluster_summary(self):

        columns = self.time_summary_columns()

        self.source_time = ColumnDataSource(data=dict())
        self.table_time = DataTable(
            source=self.source_time, columns=columns, index_position=None,
            autosize_mode='none', height=100, width=380
        )

        self.source_time.selected.on_change('indices', self.table_row_selected)


    def overall_summary_columns(self):

        columns = [
            TableColumn(field="Cluster ID", formatter=self.highlight_cell, width=60),
            TableColumn(field="# Points", formatter=self.display_format['int'], width=50),
            TableColumn(field='Time (first)', formatter=self.display_format['timestamp'], width=120),
            TableColumn(field=f"Distance ({self.units['distance'].value})", formatter=self.display_format['float'], width=90),
            TableColumn(field=f"Duration ({self.units['time'].value})", formatter=self.display_format['float'], width=100),
            TableColumn(field=f"Nearest Cluster ({self.units['distance'].value})", formatter=self.display_format['float'], width=130),
            TableColumn(field=f"Nearest Cluster ({self.units['time'].value})", formatter=self.display_format['float'], width=130)
        ]

        return columns


    def overall_cluster_summary(self):

        columns = self.overall_summary_columns()

        self.source_summary = ColumnDataSource(data=dict())
        self.table_summary = DataTable(
            source=self.source_summary, columns=columns, index_position=None,
            autosize_mode='none', height=300, width=770)
        self.source_summary.selected.on_change('indices', self.table_row_selected)


    def cluster_detail(self):

        ignore = self.columns.loc[['latitude','longitude']].tolist()
        ignore += self.details.columns[self.details.columns.str.startswith('_')].tolist()
        columns = self._format_table(self.details.drop(columns=ignore))

        self.source_detail = ColumnDataSource(data=dict())
        self.table_detail = DataTable(source=self.source_detail, columns=columns, autosize_mode='none', height=625, width=625)        


    def cluster_map(self):

        points = self.details[['_longitude_mercator','_latitude_mercator']].rename(columns={'_longitude_mercator': 'x', '_latitude_mercator': 'y'})
        self.default_zoom = self._zoom_window(points)

        # generate map
        # TODO: use distance_radians as axis type
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

        template = """                
            <div style="background:<%= _selected_color %>;">
                &ensp;
                <%= value %>
            </div>
            """
        self.highlight_cell = HTMLTemplateFormatter(template=template)

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
            (self.columns['id'], "@{"+self.columns['id']+"}"),
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
