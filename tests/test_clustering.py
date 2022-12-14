# https://pypi.org/project/hdbscan/
# https://medium.com/@sylvainma/multi-feature-geo-clustering-with-dbscan-4857c6b932e2


import pandas as pd
import numpy as np
import pytest

from clustering_dashboard import calculate, group


@pytest.fixture(scope='module')
def sample():

    data = pd.read_csv('tests/Sample10Records.csv')
    data['Pickup Time'] = pd.to_datetime(data['Pickup Time'])

    thresholds = {
        'miles': 0.25,
        'minutes': 5
    }
    labels = {
        'Location ID': np.array([0,0,1,2,0,0,3,0,4,4]),
        'Time ID': np.array([0,0,1,2,2,2,2,0,0,0]),
        'Cluster ID': np.array([0,0,1,2,3,3,4,0,5,5])
    }

    yield {'data': data, 'thresholds': thresholds, 'labels': labels}


def test_distance(sample):

    distance_radians = calculate.distance_matrix(sample['data'], 'Latitude', 'Longitude')
    distance_criteria = group.compare_distance(distance_radians, 'miles', sample['thresholds']['miles'])

    cluster_count, cluster_label = group.get_clusters(distance_criteria)

    # uncomment to manually verify the labels
    # from clustering_dashboard import convert
    # manual = convert.radians_to_distance(distance_radians, 'miles')
    assert cluster_count == len(set(cluster_label))
    assert np.array_equal(cluster_label, sample['labels']['Location ID'])



def test_time(sample):

    duration_seconds = calculate.duration_matrix(sample['data'], 'Pickup Time')
    time_criteria = group.compare_time(duration_seconds, 'minutes', sample['thresholds']['minutes'])

    cluster_count, cluster_label = group.get_clusters(time_criteria)    

    assert cluster_count == len(set(cluster_label))
    assert np.array_equal(cluster_label, sample['labels']['Time ID'])


def test_multifeature(sample):


    distance_radians = calculate.distance_matrix(sample['data'], 'Latitude', 'Longitude')
    distance_criteria = group.compare_distance(distance_radians, 'miles', sample['thresholds']['miles'])

    duration_seconds = calculate.duration_matrix(sample['data'], 'Pickup Time')
    time_criteria = group.compare_time(duration_seconds, 'minutes', sample['thresholds']['minutes'])

    cluster_count, cluster_label = group.get_clusters([distance_criteria, time_criteria])

    assert cluster_count == len(set(cluster_label))
    assert np.array_equal(cluster_label, sample['labels']['Cluster ID'])