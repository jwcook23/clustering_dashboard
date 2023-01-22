import pandas as pd
import pytest

from clustering_dashboard import calculate, group


@pytest.fixture(scope='module')
def sample():

    data = pd.read_csv('tests/Sample10Records.csv')
    data['Pickup Time'] = pd.to_datetime(data['Pickup Time'])

    units = {
        'distance': 'miles',
        'time': 'minutes'
    }
    thresholds = {
        'distance': 0.25,
        'time': 5
    }
    labels = {
        'Location ID': pd.Series([0,0,pd.NA,pd.NA,0,0,pd.NA,0,1,1], dtype='Int64'),
        'Time ID': pd.Series([0,0,pd.NA,1,1,1,1,0,0,0], dtype='Int64'),
        'Cluster ID': pd.Series([0,0,pd.NA,pd.NA,1,1,pd.NA,0,2,2], dtype='Int64')
    }

    yield {'data': data, 'units': units, 'thresholds': thresholds, 'labels': labels}


def test_distance(sample):

    distance_radians = calculate.distance_matrix(sample['data'], 'Latitude', 'Longitude')
    distance_criteria = group.compare_distance(distance_radians, sample['units']['distance'], sample['thresholds']['distance'])

    cluster_label = group.assign_id(distance_criteria)

    # uncomment to manually verify the labels
    # from clustering_dashboard import convert
    # manual = convert.radians_to_distance(distance_radians, 'miles')
    assert cluster_label.equals(sample['labels']['Location ID'])



def test_time(sample):

    duration_seconds = calculate.duration_matrix(sample['data'], 'Pickup Time')
    time_criteria = group.compare_time(duration_seconds, sample['units']['time'], sample['thresholds']['time'])

    cluster_label =group.assign_id(time_criteria)    

    assert cluster_label.equals(sample['labels']['Time ID'])


def test_multifeature(sample):


    distance_radians = calculate.distance_matrix(sample['data'], 'Latitude', 'Longitude')
    distance_criteria = group.compare_distance(distance_radians, sample['units']['distance'], sample['thresholds']['distance'])

    duration_seconds = calculate.duration_matrix(sample['data'], 'Pickup Time')
    time_criteria = group.compare_time(duration_seconds, sample['units']['time'], sample['thresholds']['time'])

    cluster_label = group.assign_id([distance_criteria, time_criteria])

    assert cluster_label.equals(sample['labels']['Cluster ID'])