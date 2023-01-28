# bokeh serve --show clustering_dashboard/dashboard.py

# TODO: slider filter for cluster # Points
# TODO: slider filter for cluster Time (first)
# TODO: data cube for details to show nested features

from bokeh.plotting import curdoc, output_file, show

from clustering_dashboard.layouts import layouts

class dashboard(layouts):

    def __init__(self, filepath=None):

        if filepath is None:
            self.document = curdoc()
        else:
            self.document = None

        layouts.__init__(self)

        if filepath is None:
            self.document.add_root(self.layout_parameters)
        else:
            output_file(filepath)
            show(self.layout_parameters)
        

if __name__.startswith('bokeh_app'):
    page = dashboard()
    