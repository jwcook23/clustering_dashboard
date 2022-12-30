from bokeh.events import Event
from bokeh.plotting import output_file, show

import pytest

from clustering_dashboard.dashboard import dashboard

@pytest.fixture(scope='module')
def db():

    page = dashboard()
    output_file("test.html")

    page.units['distance'].value = 'miles'
    page.units['time'].value = 'hours'
    page.parameters['cluster_distance'].value = 0.25
    page.parameters['date_range'].value = 6

    yield page
    show(page.layout)


def test_steps(db):

    # db.cluster_selected(None, None, [0])

    # db.source_summary.selected.indices = [0]
    db.source_location.selected.indices = [0]
    db.source_time.selected.indices = [0]

    # db.location_selected(None, None, [0])
    # db.time_selected(None, None, [0])



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