# bokeh serve --show clustering_dashboard/dashboard.py

from bokeh.plotting import curdoc, output_file, show
from bokeh.layouts import row, column
from bokeh.models import Div, Panel, Tabs

from clustering_dashboard.figures import figures

class dashboard(figures):

    def __init__(self):

        figures.__init__(self)

        self.page_layout()
        self.landing_page()


    def page_layout(self):

        title_main = Div(
            text='Clustering Dashboard',
            style={'font-size': '150%', 'font-weight': 'bold'}, width=210
        )

        bold = {'font-weight': 'bold'}

        title_distance_input = Div(text='Distance Length', style=bold)
        title_time_input = Div(text='Time Duration', style=bold)
        
        title_map = Div(text='Location and Time Clusters', style=bold, width=625)

        title_location_summary = Div(text="Location Summary", style=bold)
        self.count_location = Div()
        title_time_summary = Div(text="Time Summary", style=bold)
        self.count_time = Div()
        title_summary = Div(text="Cluster Summary", style=bold)
        self.count_summary = Div()

        self.update_selected_count()

        space = Div(height=20, width=100)

        self.layout = row(
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

if __name__.startswith('bokeh_app'):
    page = dashboard()
    curdoc().add_root(page.layout)
elif __name__ == '__main__':
    page = dashboard()
    output_file("test.html")
    show(page.layout)