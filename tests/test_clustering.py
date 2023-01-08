# https://pypi.org/project/hdbscan/
# https://medium.com/@sylvainma/multi-feature-geo-clustering-with-dbscan-4857c6b932e2

import pandas as pd
import pytest

from clustering_dashboard import calculate, group

@pytest.fixture(scope='module')
def sample():

    # data = pd.read_parquet('C:/Users/jacoo/Desktop/Temp/CabData.gzip')

    # labeled = pd.DataFrame([
    #     [7034, 0, 0, 0],[294, 0, 0, 0],[857, 0, 0, 0],
    #     [5890, 0, 1, 1], [2801, 0, 1, 1], [4230, 0, 1, 1],
    #     [1192, 0, 3, -1], 
    #     [7329, 1, 0, 2], [10211, 1, 0, 2],
    #     [2662, 1, 1, -1]
    # ], columns=['TripID', 'Labeled_Location ID', 'Labeled_Time ID', 'Labeled_Cluster ID'])
    # labeled = labeled.set_index('TripID')

    # data = data.merge(labeled, left_index=True, right_index=True, how='inner')
    # data.index = labeled.index

    # data.to_csv('tests/Sample10Records.csv')

    data = pd.read_csv('tests/Sample10Records.csv')

    yield data



def test_multifeature(sample):

    distance = calculate.distance_matrix(sample, 'Latitude', 'Longitude')
    
    geo_id = cluster_geo(sample, cluster_distance, distance, units_distance, 'Location')