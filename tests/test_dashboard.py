from bokeh.events import Event
from bokeh.plotting import output_file, show

import pytest

from clustering_dashboard.dashboard import dashboard

@pytest.fixture(scope='module')
def db():
    page = dashboard()
    output_file("test.html")
    yield page
    show(page.layout)


def test_parameter_select(db):

    db.units['distance'].value = 'miles'
    db.units['time'].value = 'hours'
    db.parameters['cluster_distance'].value = 0.25
    db.parameters['date_range'].value = 6


def test_cluster_select():

    pass



# plot second largest
# page.cluster_selected(None, None, [0])


# # display nearby points
# dropdown = Event()
# dropdown.item = 'same location'
# page.relation_selected(dropdown)

# # reset display
# dropdown = Event()
# dropdown.item = 'reset display'
# page.relation_selected(dropdown)

# adjuster parameter
# page.parameters['cluster_distance'].value = 0.01
# page.parameter_callback(None, None, None)

# # plot second largest
# page.cluster_selected(None, None, [1])