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
            style={'font-size': '150%', 'font-weight': 'bold'}, width=180
        )
        
        style = {'font-weight': 'bold'}
        title_map = Div(text='Location and Time Clusters', style=style, width=625)
        title_units = Div(text="Units", style=style, width=160)
        title_parameter = Div(text="Parameters", style=style, width=160)
        title_options = Div(text="Display Options")

        title_location = Div(text="Location Summary", style=style)
        self.count_location = Div()
        title_time = Div(text="Time Summary", style=style)
        self.count_time = Div()
        title_summary = Div(text="Cluster Summary", style=style)
        self.count_summary = Div()

        self.update_selected_count()

        space = Div(height=20, width=160)

        self.layout = row(
            column(
                row(
                    column(
                        title_main,
                        title_units,
                        row(self.units['distance'], self.units['time']),
                        space,
                        title_parameter,
                        row(self.parameters['cluster_distance'], self.parameters['date_range'])
                    ),
                    Tabs(tabs=[
                        Panel(child=row(self.plot_estimate_distance, self.plot_estimate_time), title='Parameter Estimation'),
                        Panel(child=row(self.plot_next_distance, self.plot_span_distance), title='Distance Parameter Evaluation'),
                        Panel(child=row(self.plot_next_date, self.plot_span_date), title='Time Parameter Evalulation')
                    ])
                ),
                row(
                    column(
                        title_options,
                        self.options['reset'],
                    ),
                    row(
                        column(row(title_location, self.count_location), self.table_location), 
                        column(row(title_time, self.count_time), self.table_time)
                    )
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