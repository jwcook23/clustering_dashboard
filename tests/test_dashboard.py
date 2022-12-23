from bokeh.events import Event
from bokeh.plotting import output_file, show

from clustering_dashboard import dashboard

def test_parameter_select():

    page = dashboard()
    output_file("test.html")
    show(page.layout)

# plot second largest
# page.table_callback(None, None, [0])

# # enable time clustering
# page.date_callback([0])

# # display nearby points
# dropdown = Event()
# dropdown.item = 'same location'
# page.display_callback(dropdown)

# # reset display
# dropdown = Event()
# dropdown.item = 'reset display'
# page.display_callback(dropdown)

# adjuster parameter
# page.parameters['cluster_distance'].value = 0.01
# page.parameter_callback(None, None, None)

# # plot second largest
# page.table_callback(None, None, [1])