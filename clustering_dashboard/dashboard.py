# bokeh serve --show clustering_dashboard/dashboard.py

from bokeh.plotting import curdoc, output_file, show

from clustering_dashboard.layouts import layouts

class dashboard(layouts):

    def __init__(self, filename=None):

        if filename is None:
            self.document = curdoc()
            self.filename = None
        else:
            self.document = None
            self.filename = filename

        layouts.__init__(self)

        if filename is None:
            self.document.add_root(self.layout_parameters)
        else:
            output_file(self.filename)
            show(self.layout_parameters)
            # show(page.layout_dashboard)
        

if __name__.startswith('bokeh_app'):
    page = dashboard()
elif __name__ == '__main__':
    page = dashboard(static_filename='test.html')
    