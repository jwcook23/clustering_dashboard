import numpy as np
import numpy.ma as ma
import pandas as pd
from scipy.spatial import ConvexHull
from sklearn.cluster import DBSCAN

import summary

def assign_id(cluster_id, address):

    # combine geo and date cluster ids
    overall = cluster_id.groupby(['ClusterDate','ClusterLocation']).ngroup()
    overall = overall.astype('Int64')
    overall[overall==-1] = None
    overall.name = 'Grouped'
    overall = overall.reset_index()

    # calculate size of each cluster
    size = overall['Grouped'].value_counts()
    size.name = 'Count'
    size.index.name = 'Grouped'
    size = size.reset_index()

    # assign 0 as the largest sized cluster
    size['ClusterID'] = range(0,len(size))
    overall = overall.merge(size, on='Grouped', how='left')
    overall['ClusterID'] = overall['ClusterID'].astype('Int64')
    overall = overall.set_index(address.index.name)

    cluster_id = cluster_id.merge(overall['ClusterID'], left_index=True, right_index=True, how='inner')

    return cluster_id


def get_clusters(address, max_cluster_distance_miles, distance, column_date, date_range, additional_summary):

    # group dates
    # date_id, grouped = cluster_date(address, column_latitude, column_longitude, column_date)
    date_id = cluster_date(address, column_date, date_range)
    cluster_id = address.merge(date_id, left_index=True, right_index=True)

    # group addresses
    # geo_id = grouped.apply(lambda x: cluster_geo(x, max_cluster_distance_miles, min_cluster_size, column_latitude, column_longitude))
    geo_id = cluster_geo(address, max_cluster_distance_miles, distance)
    cluster_id = cluster_id.merge(geo_id, left_index=True, right_index=True)

    # assign an overall id desc with largest size
    cluster_id = assign_id(cluster_id, address)

    # determine distance of points to other points
    cluster_id = point_distance(cluster_id, distance)

    # summerize cluster
    cluster_summary = summary.get_summary(cluster_id, column_date, additional_summary)

    # calculate cluster boundary for map zoom
    cluster_boundary = cluster_id.groupby('ClusterID')
    cluster_boundary = cluster_boundary.apply(get_boundary)

    return cluster_summary, cluster_boundary, cluster_id


def cluster_date(address, column_date, date_range):

    if not date_range.visible:
        cluster_id = pd.Series([0]*len(address), index=address.index)
    else:
        grouped = address.groupby(pd.Grouper(key=column_date, freq=f'{date_range.value}D'))
        cluster_id = grouped.ngroup()
        cluster_id = cluster_id.astype('Int64')
        cluster_id[cluster_id==-1] = pd.NA
    
    cluster_id.name = 'ClusterDate'

    return cluster_id


def cluster_geo(df, max_cluster_distance_miles, distance):

    # convert to kilometers then radians
    eps = max_cluster_distance_miles.value*1.60934/6371

    # identify geographic clusters
    clusters = DBSCAN(metric='precomputed', eps=eps, min_samples=2)
    clusters = clusters.fit(distance)
    cluster_id = clusters.labels_.astype('float')
    cluster_id[cluster_id==-1] = np.nan

    cluster_id = pd.Series(cluster_id, name='ClusterLocation', index=df.index.values, dtype='Int64')
    cluster_id.index.name = df.index.name

    return cluster_id


def get_boundary(group):
    '''Calculate the boundary of latitude and longitude points using a convex hull.'''

    points = group[['Latitude_mercator','Longitude_mercator']].values

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
    boundary = pd.Series({'Latitude_mercator': [[list(boundary[:,0])]], 'Longitude_mercator': [[list(boundary[:,1])]]})

    return boundary

def point_distance(cluster_id, distance):

    grouped = pd.DataFrame(cluster_id['ClusterLocation'])
    grouped['index'] = range(0, len(grouped))
    grouped = grouped.groupby('ClusterLocation')
    grouped = grouped.agg({'index': list})
    grouped['index'] = grouped['index'].apply(lambda x: np.array(x))
    grouped['row'] = grouped['index'].apply(lambda x: x.repeat(len(x)))
    grouped['col'] = grouped['index'].apply(lambda x: np.tile(x,len(x)))
    row = np.concatenate(grouped['row'].values)
    col = np.concatenate(grouped['col'].values)

    distance.mask = np.eye(distance.shape[0], dtype=bool)
    distance[row, col] = ma.masked
    cluster_id['Nearest (miles)'] = distance.min(axis=0) * 3958

    distance.mask = True
    distance.mask[row, col] = False
    cluster_id['Span (miles)'] = distance.max(axis=0) * 3958

    distance.mask = False

    return cluster_id