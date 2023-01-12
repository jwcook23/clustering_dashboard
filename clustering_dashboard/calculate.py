import numpy as np
import numpy.ma as ma
import pandas as pd
from sklearn.metrics.pairwise import haversine_distances
from sklearn.metrics import pairwise_distances

from clustering_dashboard import convert

def distance_matrix(df, column_latitude, column_longitude):
    
    # TODO: calculate sparse matrix for better performance
    coords = np.radians(df[[column_latitude, column_longitude]].values)
    distance_radians = haversine_distances(coords, coords)
    distance_radians = ma.array(distance_radians)

    return distance_radians

def duration_matrix(df, column_time):

    # TODO: calculate sparse matrix for better performance
    time = df[column_time].view('int64').to_numpy().reshape(-1,1)
    duration_seconds = pairwise_distances(time, metric='cityblock') / 10**9

    return duration_seconds


def nearest_point(distance, units):

    distance.mask = np.eye(distance.shape[0], dtype=bool)
    np.fill_diagonal(distance.mask, True)
    nearest = distance.min(axis=0)
    nearest = convert.radians_to_distance(nearest, units)
    distance.mask = False

    nearest = pd.Series(np.array(nearest))

    return nearest
    

def nearest_time(timestamps, units):
    
    timestamps = timestamps.sort_values()
    nearest = pd.DataFrame({
        'next': abs(timestamps-timestamps.shift(1)),
        'previous': abs(timestamps-timestamps.shift(-1))
    })
    nearest = nearest[['next','previous']].min(axis='columns')
    nearest = convert.duration_to_numeric(nearest, units)

    return nearest
