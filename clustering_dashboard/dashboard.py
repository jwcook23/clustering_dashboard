# bokeh serve --show clustering_dashboard/dashboard.py

# TODO: data cube for details to show nested features

from pathlib import Path

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
            directory = Path(filepath).parents[0]
            Path(directory).mkdir(parents=True, exist_ok=True)
            output_file(filepath)
            show(self.layout_parameters)
        

if __name__.startswith('bokeh_app'):
    page = dashboard()
    