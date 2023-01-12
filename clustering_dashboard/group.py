import numpy as np
import numpy.ma as ma
import pandas as pd
from scipy.spatial import ConvexHull
from scipy.sparse.csgraph import connected_components


from clustering_dashboard import summary, convert

def assign_id(details, input_columns, output_name):

    id_name = f'{output_name} ID'

    # combine geo and time cluster ids
    overall = details.groupby(input_columns).ngroup()
    overall = overall.astype('Int64')
    overall[overall==-1] = None
    overall.name = 'Grouped'
    overall = overall.reset_index()

    # calculate size of each cluster
    size = overall['Grouped'].value_counts()
    size.name = '# Points'
    size.index.name = 'Grouped'
    size = size.reset_index()

    # require multiple points for a cluster
    size = size[size['# Points']>1]

    # assign 0 as the largest sized cluster
    size[id_name] = range(0,len(size))
    overall = overall.merge(size, on='Grouped', how='left')
    overall[id_name] = overall[id_name].astype('Int64')

    # add id to original input
    if id_name in details:
        details = details.drop(columns=id_name)
    details = details.merge(overall[[id_name]], left_index=True, right_index=True, how='left')


    return details


# def get_clusters(details, cluster_distance, distance, column_time, units_time, units_distance, cluster_time, additional_summary):

#     # group dates
#     date_id, grouped = cluster_date(details, column_time, cluster_time, units_time)
#     details = details.drop(columns=['Time ID']).merge(date_id, left_index=True, right_index=True)

#     # group on location without time aspect
#     geo_id = cluster_geo(details, cluster_distance, distance, units_distance, 'Location')
#     details = details.drop(columns=['Location ID']).merge(geo_id, left_index=True, right_index=True)

#     # group on location with time to assign overall Cluster ID
#     # geo_id = grouped.apply(lambda x:  cluster_geo(x, cluster_distance, distance, units_distance, 'LocationTime'))
#     # details = details.drop(columns=['LocationTime ID']).merge(geo_id, left_index=True, right_index=True)

#     # assign an overall id desc with largest size
#     details = assign_id(details, ['Time ID', 'Location ID'], 'Cluster')

#     # determine distance of points to other points
#     details = point_distance(details, distance, units_distance)

#     # summerize cluster
#     cluster_summary, location_summary, time_summary = summary.get_summary(details, column_time, units_time, units_distance, additional_summary)

#     # calculate cluster boundary for map zoom
#     cluster_boundary = details.groupby('Cluster ID')
#     cluster_boundary = cluster_boundary.apply(get_boundary)

#     return cluster_summary, location_summary, time_summary, cluster_boundary, details


def compare_distance(distance_radians, threshold_units, threshold_value):

    threshold_converted = convert.distance_to_radians(threshold_value, threshold_units)

    distance_criteria = (np.array(distance_radians) <= threshold_converted)

    return distance_criteria


def compare_time(duration_seconds, threshold_units, threshold_value):

    threshold_converted = convert.time_to_seconds(threshold_value, threshold_units)

    duration_criteria = duration_seconds <= threshold_converted

    return duration_criteria


def get_clusters(comparison_criteria):

    if isinstance(comparison_criteria, list):
        comparison_criteria = np.array(comparison_criteria)
        comparison_criteria = np.all(comparison_criteria, axis=0)

    cluster_count, cluster_label = connected_components(comparison_criteria)

    return cluster_count, cluster_label


def cluster_date(details, column_time, cluster_time, units_time):

    if units_time == 'days':
        offset = 'D'
    elif units_time == 'hours':
        offset = 'H'
    elif units_time == 'minutes':
        offset = 'T'
    grouped = details.groupby(pd.Grouper(key=column_time, freq=f'{cluster_time}{offset}'))
    assigned_id = pd.DataFrame(grouped.ngroup(), columns=['Time ID'], index=details.index, dtype='Int64')
    assigned_id['Time ID'][assigned_id['Time ID']==-1] = None

    # assign ID based on size
    assigned_id = assign_id(assigned_id, ['Time ID'], 'Time')

    return assigned_id, grouped


# def cluster_geo(df, cluster_distance, distance, units_distance, name):

#     id_name = f'{name} ID'

#     # convert to radians
#     eps = convert.distance_to_radians(cluster_distance, units_distance)

#     # identify geographic clusters from already clustered time values
#     # TODO: include core_sample_indices_ in plotting or summary
#     clusters = DBSCAN(metric='precomputed', eps=eps, min_samples=2)
#     if len(df)==0:
#         assigned_id = None
#     else:
#         time_submatrix = distance[np.ix_(df.index, df.index)]
#         clusters = clusters.fit(time_submatrix)
#         assigned_id = pd.DataFrame(clusters.labels_, columns=[id_name], index=df.index, dtype='Int64')
#         assigned_id[id_name][assigned_id[id_name]==-1] = None

#         # assign ID based on size if grouping by location only
#         if name == 'Location':
#             assigned_id = assign_id(assigned_id, [id_name], name)

#     return assigned_id


def get_boundary(group):
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


def point_distance(details, distance, units_distance):

    grouped = pd.DataFrame(details['Cluster ID'])
    grouped['index'] = range(0, len(grouped))
    grouped = grouped.groupby('Cluster ID')
    grouped = grouped.agg({'index': list})
    grouped['index'] = grouped['index'].apply(lambda x: np.array(x))
    grouped['row'] = grouped['index'].apply(lambda x: x.repeat(len(x)))
    grouped['col'] = grouped['index'].apply(lambda x: np.tile(x,len(x)))
    row = np.concatenate(grouped['row'].values)
    col = np.concatenate(grouped['col'].values)

    distance.mask = np.eye(distance.shape[0], dtype=bool)
    distance[row, col] = ma.masked
    nearest = distance.min(axis=0)
    nearest = convert.radians_to_distance(nearest, units_distance)
    details[f'Nearest ({units_distance})'] =  nearest

    distance.mask = True
    distance.mask[row, col] = False
    length = distance.max(axis=0)
    length = convert.radians_to_distance(length, units_distance)
    details[f'Length ({units_distance})'] =  length

    distance.mask = False

    return details