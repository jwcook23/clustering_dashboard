import numpy as np
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.transform import linear_cmap
from bokeh.models import (
    ColumnDataSource, Label, DataTable,
    HoverTool, ColorBar, DatetimeTickFormatter, TableColumn,
    Dropdown, Select, NumericInput
)

from clustering_dashboard.data import data
from clustering_dashboard.callbacks import callbacks

class figures(data, callbacks):

    def __init__(self):

        data.__init__(self)
        callbacks.__init__(self)

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
        self.summary_table()
        self.cluster_map()
        self.cluster_detail()


    def units_distance(self):

        self.units['distance'] = Select(title='Distance:', value="miles", options=["miles", "feet", "kilometers"], height=25, width=75)
        self.units['distance'].on_change('value', self.calculate_callback)


    def units_time(self):

        self.units['time'] = Select(title='Time:', value="hours", options=["days", "hours", "minutes"], height=25, width=75)
        self.units['time'].on_change('value', self.calculate_callback)


    def parameter_distance(self):

        self.parameters['cluster_distance'] = NumericInput(value=None, mode='float', title=f'Location Distance ({self.units["distance"].value}):', height=50, width=160)
        self.parameters['cluster_distance'].on_change('value', self.calculate_callback)

    def parameter_time(self):

        self.parameters['date_range'] = NumericInput(value=None, mode='float', title=f'Time Duration ({self.units["time"].value}):', height=50, width=160)
        self.parameters['date_range'].on_change('value', self.calculate_callback)


    def related_clusters(self):

        menu = [
            ("1) Reset display.", "reset display"),
            ("2) Display clusters with same Location ID.", "same location"),
            ("3) Display clusters with same Time ID.", "same time")
        ]
        self.options['display'] = Dropdown(label="display related clusters", button_type="default", menu=menu, height=25, width=200)
        self.options['display'].on_click(self.display_callback)


    def common_figure(self, title, xlabel, ylabel):

        fig = figure(
            title=title, width=275, height=225,
            y_axis_label = ylabel, x_axis_label=xlabel,
            toolbar_location='right', tools='pan, box_zoom, reset',
            active_drag = 'box_zoom'
        )

        return fig


    def estimation_figure(self, title, xlabel, ylabel):

        fig = self.common_figure(title, xlabel, ylabel)

        source = ColumnDataSource({
            'x': [],
            'y': []
        })

        renderer = fig.line('x','y', source=source)
     
        return fig, renderer


    def evaluation_figure(self, title, xlabel, ylabel):

        fig = self.common_figure(title, xlabel, ylabel)
        source = ColumnDataSource({'left': [], 'right': [], 'top': [], 'bottom': []})
        renderer = fig.quad(
            'left', 'right', 'top', 'bottom', source=source, 
            fill_color="skyblue", line_color="white"
        )

        return fig, renderer


    def parameter_estimate(self):

        self.plot_estimate_distance, self.render_estimate_distance = self.estimation_figure(
            'Distance between Clusters', 'Point', self.units["distance"].value
        )
        self.plot_estimate_time, self.render_estimate_time = self.estimation_figure(
            'Time between Clusters', 'Point', self.units["time"].value
        )


    def distance_evaluation(self):
        self.plot_next_distance, self.render_next_distance = self.evaluation_figure(
            'Distance between Clusters', self.units["distance"].value, '# Clusters'
        )

        self.plot_span_distance, self.render_span_distance = self.evaluation_figure(
            'Distance in Cluster', self.units["distance"].value, '# Clusters'
        )


    def time_evaluation(self):

        self.plot_next_date, self.render_next_date = self.evaluation_figure(
            'Time between Clusters', self.units["time"].value, '# Clusters'
        )

        self.plot_span_date, self.render_span_date = self.evaluation_figure(
            'Time in Cluster', self.units["time"].value, '# Clusters'
        )


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
        self.source_summary.selected.on_change('indices', self.table_callback)


    def cluster_detail(self):

        ignore = self.columns.loc[['latitude','longitude']].tolist()
        ignore += ['_longitude_mercator','_latitude_mercator']
        columns = self.format_table(self.address.drop(columns=ignore))

        self.source_detail = ColumnDataSource(data=dict())
        self.table_detail = DataTable(source=self.source_detail, columns=columns, autosize_mode='fit_columns', height=625, width=625)        


    def cluster_map(self):

        points = self.address[['_longitude_mercator','_latitude_mercator']].rename(columns={'_longitude_mercator': 'x', '_latitude_mercator': 'y'})
        self.default_zoom = self.zoom_window(points)

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
        cmap = linear_cmap(field_name='_timestamp', palette='Turbo256', low=min(self.address['_timestamp']), high=max(self.address['_timestamp']))
        color_bar = ColorBar(color_mapper=cmap['transform'], 
            # title=self.columns['time'], 
            formatter=DatetimeTickFormatter()
        )
        self.plot_map.add_layout(color_bar, 'above')        

        # render address points
        source = ColumnDataSource(data=dict(xs=[], ys=[], time=[], _timestamp=[]))
        self.render_points = self.plot_map.circle('xs','ys', source=source, fill_color=cmap, line_color=None, size=10, legend_label='Location')
        features, formatters = self.format_hover()
        self.plot_map.add_tools(HoverTool(
            tooltips=features,
            formatters=formatters,
            renderers=[self.render_points])
        )

        # render boundary of clusters
        source = ColumnDataSource(data=dict(xs=[], ys=[], time=[], _timestamp=[]))
        self.render_boundary = self.plot_map.multi_polygons('xs', 'ys', source=source, color=cmap, alpha=0.3, line_color=None, legend_label='Cluster')

        self.plot_map.legend.location = "top_right"

