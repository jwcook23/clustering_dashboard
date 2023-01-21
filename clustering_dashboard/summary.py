import pandas as pd
import numpy as np
import numpy.ma as ma
from scipy.spatial import ConvexHull

from clustering_dashboard import convert, aggregations


def _calc_distance_features(distance_radians, units_distance, row_id, col_id):

    distance_nearest_column = f"Nearest Cluster ({units_distance})"
    distance_length_column = f"Distance ({units_distance})"
    distance_nearest = find_next_cluster_nearest(
        'distance', distance_radians, units_distance, row_id, col_id, distance_nearest_column
    )
    distance_length = find_same_cluster_length(
        'distance', distance_radians, units_distance, row_id, col_id, distance_length_column
    )

    return distance_nearest, distance_length


def _calc_time_features(duration_seconds, units_time, row_id, col_id):

    time_nearest_column = f"Nearest Cluster ({units_time})"
    time_length_column = f"Duration ({units_time})"
    time_nearest = find_next_cluster_nearest(
        'time', duration_seconds, units_time, row_id, col_id, time_nearest_column
    )
    time_length = find_same_cluster_length(
        'time', duration_seconds, units_time, row_id, col_id, time_length_column
    )

    return time_nearest, time_length


def get_cluster_summary(details, distance_radians, units_distance, duration_seconds, units_time, column_time):

    row_id, col_id = matrix_indices(details, 'Cluster ID')

    distance_nearest, distance_length = _calc_distance_features(
        distance_radians, units_distance, row_id, col_id
    )
    details[distance_nearest.name] = distance_nearest
    details[distance_length.name] = distance_length

    time_nearest, time_length = _calc_time_features(
        duration_seconds, units_time, row_id, col_id
    )
    details[time_nearest.name] = time_nearest
    details[time_length.name] = time_length   

    cluster_groups = details.reset_index().groupby('Cluster ID')
    plan = {
        column_time: min,
        distance_nearest.name: min, distance_length.name: max, 
        time_nearest.name: min, time_length.name: max
    }
    cluster_summary = cluster_groups.agg(plan)

    num_points = cluster_groups.size()
    num_points.name = '# Points'
    cluster_summary['# Points'] = num_points

    cluster_summary = cluster_summary[[
        '# Points', column_time,
        distance_nearest.name, distance_length.name, 
        time_nearest.name, time_length.name
    ]]
    cluster_summary = cluster_summary.rename(columns={
        column_time: "Time (first)"
    })

    cluster_boundary = cluster_groups.apply(find_location_boundary)

    return cluster_summary, details, cluster_boundary


def get_location_summary(details, distance_radians, units_distance):

    row_id, col_id = matrix_indices(details, 'Location ID')

    distance_nearest, distance_length = _calc_distance_features(
        distance_radians, units_distance, row_id, col_id
    )
    location_summary = details[['Location ID','Cluster ID']].copy()
    location_summary[distance_nearest.name] = distance_nearest
    location_summary[distance_length.name] = distance_length

    location_summary = location_summary.groupby('Location ID')
    location_summary = location_summary.agg({
        'Cluster ID': aggregations.UniqueCountNonNA,
        distance_nearest.name: 'min',
        distance_length.name: 'max'
    })
    location_summary = location_summary.rename(columns={'Cluster ID': '# Clusters'})

    return location_summary


def get_time_summary(details, duration_seconds, units_time):

    row_id, col_id = matrix_indices(details, 'Time ID')

    time_nearest, time_length = _calc_time_features(
        duration_seconds, units_time, row_id, col_id
    )
    time_summary = details[['Time ID', 'Cluster ID']].copy()
    time_summary[time_nearest.name] = time_nearest
    time_summary[time_length.name] = time_length

    time_summary = time_summary.groupby('Time ID')
    time_summary = time_summary.agg({
        'Cluster ID': aggregations.UniqueCountNonNA,
        time_nearest.name: 'min',
        time_length.name: 'max'
    })
    time_summary = time_summary.rename(columns={'Cluster ID': '# Clusters'})

    return time_summary


def matrix_indices(df, id_column):

    grouped = pd.DataFrame(df[id_column])
    grouped['index'] = range(0, len(grouped))
    grouped = grouped.groupby(id_column)
    grouped = grouped.agg({'index': list})
    grouped['index'] = grouped['index'].apply(lambda x: np.array(x))
    grouped['row'] = grouped['index'].apply(lambda x: x.repeat(len(x)))
    grouped['col'] = grouped['index'].apply(lambda x: np.tile(x,len(x)))
    row_id = np.concatenate(grouped['row'].values)
    col_id = np.concatenate(grouped['col'].values)

    return row_id, col_id


def find_next_cluster_nearest(feature, matrix, units, row_id, col_id, column_name):

    matrix.mask = np.eye(matrix.shape[0], dtype=bool)
    matrix[row_id, col_id] = ma.masked
    nearest = matrix.min(axis=0)
    if feature == 'distance':
        nearest = convert.radians_to_distance(nearest, units)
    elif feature == 'time':
        nearest = convert.seconds_to_time(nearest, units)

    nearest =  pd.Series(nearest, name=column_name)

    matrix.mask = False

    return nearest


def find_same_cluster_length(feature, matrix, units, row_id, col_id, column_name):

    matrix.mask = True
    matrix.mask[row_id, col_id] = False
    length = matrix.max(axis=0)
    if feature == 'distance':
        length = convert.radians_to_distance(length, units)
    elif feature == 'time':
        length = convert.seconds_to_time(length, units)

    length = pd.Series(length, name=column_name)

    matrix.mask = False

    return length


def find_location_boundary(group):
    '''Calculate the boundary of latitude and longitude points using a convex hull.'''

    points = group[['_latitude_mercator','_longitude_mercator']].values

    # return a line for only 2 points
    if points.shape[0]<=2:
        boundary = points
    # return hull for >2 points
    else:
        hull = ConvexHull(points)
        boundary = points[hull.vertices]
        # enclose the hull boundary
        boundary = np.concatenate([boundary,boundary[[0],:]])

    # reshape and format for multi_polygons
    # ex) LAT_mercator = [[[[0, 0, 1, 1]]], [[[3,4,5]]]]
    boundary = pd.Series({'_latitude_mercator': [[list(boundary[:,0])]], '_longitude_mercator': [[list(boundary[:,1])]]})

    return boundary

# def summarize_additional(details, column_time, additional_summary):

    # agg_options = {
    #     'min': _min,
    #     'max': _max,
    #     'unique': _unique
    # }

    # TODO: additional summary in another tab?
    # additional_summary = {key:agg_options[val] for key,val in additional_summary.items()}
    # plan = {**plan, **additional_summary}

    # return cluster_summary