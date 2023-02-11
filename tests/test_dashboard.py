import pytest

from bokeh.plotting import show

from clustering_dashboard.dashboard import dashboard

import data


@pytest.fixture(scope='module')
def sample_allrecords(request):

    file_name = request.param

    db = dashboard(f"tests/output/{file_name}.html")

    db._load_data("C:/Users/jacoo/Desktop/Temp/CabData.parquet")

    db.column_options['id'].value = 'TripID'
    db.column_options['latitude'].value = 'Latitude'
    db.column_options['longitude'].value = 'Longitude'
    db.column_options['time'].value = 'Pickup Time'
    db._columns_selected(None, None, None)

    db.units['distance'].value = 'miles'
    db.units['time'].value = 'minutes'
    db.parameters['cluster_distance'].value = 0.25
    db.parameters['cluster_time'].value = 30
    db.reset_all()

    return db


@pytest.fixture(scope='module')
def sample_10records(request):

    data.df.to_parquet('tests/sample_10records.parquet')

    file_name = request.param

    db = dashboard(f"tests/output/{file_name}.html")

    db._load_data("tests/sample_10records.parquet")

    db.column_options['id'].value = 'TripID'
    db.column_options['latitude'].value = 'Latitude'
    db.column_options['longitude'].value = 'Longitude'
    db.column_options['time'].value = 'Pickup Time'
    db._columns_selected(None, None, None)

    db.units['distance'].value = 'miles'
    db.units['time'].value = 'minutes'
    db.parameters['cluster_distance'].value = 0.25
    db.parameters['cluster_time'].value = 5
    db.reset_all()

    return db


@pytest.mark.parametrize('sample_10records', [('test_crossfilter_sliders')], indirect=True)
def test_crossfilter_sliders(sample_10records):
    
    sample = sample_10records

    start = sample.summary_first.start+sample.summary_first.step
    end = sample.summary_first.end
    sample.summary_first.value = (start,end)
    sample.filter_cluster_summary(None, None, None)

    sample.source_summary.selected.indices = [1]

    show(sample.layout_dashboard)


@pytest.mark.parametrize('sample_10records', [('test_crossfilter_tables')], indirect=True)
def test_crossfilter_tables(sample_10records):

    sample = sample_10records

    sample.source_location.selected.indices = [1]

    show(sample.layout_dashboard)


@pytest.mark.parametrize('sample_allrecords', [('test_large_file')], indirect=True)
def test_large_file(sample_allrecords):

    sample = sample_allrecords

    sample.source_location.selected.indices = [1]

    show(sample.layout_dashboard)