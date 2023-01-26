from bokeh.events import MenuItemClick
from bokeh.plotting import show

from clustering_dashboard.dashboard import dashboard


def test_steps():

    page = dashboard("tests/test.html")

    page._load_data("tests/Sample10Records.parquet")
    
    page._id_selected(MenuItemClick(page.column_options['id'], item='TripID'))
    page._latitude_selected(MenuItemClick(page.column_options['latitude'], item='Latitude'))
    page._longitude_selected(MenuItemClick(page.column_options['id'], item='Longitude'))
    page._time_selected(MenuItemClick(page.column_options['time'], item='Pickup Time'))

    page.units['time'].value = 'days'

    # page.units['distance'].value = 'miles'
    page.parameters['cluster_distance'].value = 0.25
    # page.units['time'].value = 'minutes'
    page.parameters['cluster_time'].value = 30
    page.parameter_selected(None, None, None)

    page.cluster_selected(None, None, [0])

    show(page.layout_dashboard)

    # TODO: add tests for all callbacks and clicks
