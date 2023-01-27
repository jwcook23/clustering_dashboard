from bokeh.events import Event
from bokeh.plotting import show

from clustering_dashboard.dashboard import dashboard


def test_steps():

    page = dashboard("tests/test.html")

    page._load_data("tests/Sample10Records.parquet")
    
    page.column_options['id'].value = 'TripID'
    page.column_options['latitude'].value = 'Latitude'
    page.column_options['longitude'].value = 'Longitude'
    page.column_options['time'].value = 'Pickup Time'
    page._columns_selected(None, None, None)

    page.units['time'].value = 'days'
    page.parameters['cluster_distance'].value = 0.25
    page.parameters['cluster_time'].value = 30
    page.parameter_selected(None, None, None)

    page.source_summary.selected.indices = [0]
    page.table_row_selected(None, None, None)

    show(page.layout_dashboard)

    # TODO: add tests for all callbacks and clicks
