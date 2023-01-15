import pandas as pd
import numpy as np
import numpy.ma as ma
from scipy.spatial import ConvexHull

from clustering_dashboard import convert, aggregations


def get_summary(details, distance_radians, units_distance, duration_seconds, units_time, column_time):

    location_summary, time_summary = summerize_ids(details)

    row_id, col_id = matrix_indices(details)

    details = find_next_cluster_nearest('distance', distance_radians, units_distance, row_id, col_id, details)
    details = find_same_cluster_length('distance', distance_radians, units_distance, row_id, col_id, details)

    details = find_next_cluster_nearest('time', duration_seconds, units_time, row_id, col_id, details)
    details = find_same_cluster_length('time', duration_seconds, units_time, row_id, col_id, details)

    cluster_groups = details.reset_index().groupby('Cluster ID')
    plan = {
        'Location ID': 'first', 'Time ID': 'first', column_time: min,
        f"Nearest ({units_distance})": min, f"Furthest ({units_distance})": max, 
        f"Nearest ({units_time})": min, f"Furthest ({units_time})": max
    }
    cluster_summary = cluster_groups.agg(plan)
    cluster_summary = cluster_summary.rename(columns={column_time: 'Time (first)'})

    num_points = cluster_groups.size()
    num_points.name = '# Points'
    cluster_summary['# Points'] = num_points

    cluster_summary = cluster_summary[[
        '# Points', 'Location ID', 'Time ID', 'Time (first)',
        f"Nearest ({units_distance})", f"Furthest ({units_distance})", 
        f"Nearest ({units_time})", f"Furthest ({units_time})"
    ]]

    cluster_boundary = cluster_groups.apply(find_location_boundary)

    return cluster_summary, location_summary, time_summary, details, cluster_boundary


def summerize_ids(details):

    # summarize location ids
    location_summary = details.groupby('Location ID')
    location_summary = location_summary.agg({'Cluster ID': [aggregations.UniqueCountNonNA, aggregations.CountNA]})
    location_summary.columns = location_summary.columns.droplevel(0)
    location_summary = location_summary.rename(columns={'UniqueCountNonNA': '# Clusters', 'CountNA': '# Unassigned Points'})

    # summerize time ids
    time_summary = details.groupby('Time ID')
    time_summary = time_summary.agg({'Cluster ID': [aggregations.UniqueCountNonNA, aggregations.CountNA]})
    time_summary.columns = time_summary.columns.droplevel(0)
    time_summary = time_summary.rename(columns={'UniqueCountNonNA': '# Clusters', 'CountNA': '# Unassigned Points'})

    return location_summary, time_summary


def matrix_indices(details):

    grouped = pd.DataFrame(details['Cluster ID'])
    grouped['index'] = range(0, len(grouped))
    grouped = grouped.groupby('Cluster ID')
    grouped = grouped.agg({'index': list})
    grouped['index'] = grouped['index'].apply(lambda x: np.array(x))
    grouped['row'] = grouped['index'].apply(lambda x: x.repeat(len(x)))
    grouped['col'] = grouped['index'].apply(lambda x: np.tile(x,len(x)))
    row_id = np.concatenate(grouped['row'].values)
    col_id = np.concatenate(grouped['col'].values)

    return row_id, col_id


def find_next_cluster_nearest(feature, matrix, units, row_id, col_id, details):

    matrix.mask = np.eye(matrix.shape[0], dtype=bool)
    matrix[row_id, col_id] = ma.masked
    nearest = matrix.min(axis=0)
    if feature == 'distance':
        nearest = convert.radians_to_distance(nearest, units)
    elif feature == 'time':
        nearest = convert.seconds_to_time(nearest, units)

    details[f'Nearest ({units})'] =  nearest

    matrix.mask = False

    return details


def find_same_cluster_length(feature, matrix, units, row_id, col_id, details):

    matrix.mask = True
    matrix.mask[row_id, col_id] = False
    length = matrix.max(axis=0)
    if feature == 'distance':
        length = convert.radians_to_distance(length, units)
    elif feature == 'time':
        length = convert.seconds_to_time(length, units)

    details[f"Furthest ({units})"] =  length

    matrix.mask = False

    return details


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