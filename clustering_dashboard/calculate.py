import numpy as np
import numpy.ma as ma
import pandas as pd
from sklearn.metrics.pairwise import haversine_distances

from clustering_dashboard import convert

def distance_matrix(df, column_latitude, column_longitude):
    
    # TODO: calculate sparse matrix for better performance
    coords = np.radians(df[[column_latitude, column_longitude]].values)
    distance = haversine_distances(coords, coords)
    distance = ma.array(distance)

    return distance


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
