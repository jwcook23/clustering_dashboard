import pytest

from bokeh.plotting import show

from clustering_dashboard.dashboard import dashboard

import data

@pytest.fixture(scope='module')
def sample():

    data.df.to_parquet('tests/Sample10Records.parquet')

    db = dashboard("tests/test.html")

    db._load_data("tests/Sample10Records.parquet")

    yield db


def test_steps(sample):
    
    sample.column_options['id'].value = 'TripID'
    sample.column_options['latitude'].value = 'Latitude'
    sample.column_options['longitude'].value = 'Longitude'
    sample.column_options['time'].value = 'Pickup Time'
    sample._columns_selected(None, None, None)

    sample.units['distance'].value = 'miles'
    sample.units['time'].value = 'minutes'
    sample.parameters['cluster_distance'].value = 0.25
    sample.parameters['cluster_time'].value = 5
    sample.reset_all()

    # sample.source_summary.selected.indices = [0]
    # sample.table_row_selected(None, None, None)

    start = sample.summary_first.start+sample.summary_first.step
    end = sample.summary_first.end
    sample.summary_first.value = (start,end)
    sample.filter_cluster_summary(None, None, None)
    # sample.summary_points.value = 3
    # sample.filter_cluster_summary(None, None, None)

    sample.source_summary.selected.indices = [1]

    show(sample.layout_dashboard)

    # TODO: add tests for all callbacks and clicks
