import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from sklearn.cluster import DBSCAN

from summary import agg_options

def assign_id(cluster_id, address, min_cluster_size):

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

    # remove geo clusters smaller than parameter that were split by date cluster
    size = size[size['Count']>=min_cluster_size.value]

    # assign 0 as the largest sized cluster
    size['ClusterID'] = range(0,len(size))
    overall = overall.merge(size, on='Grouped', how='left')
    overall['ClusterID'] = overall['ClusterID'].astype('Int64')
    overall = overall.set_index(address.index.name)

    cluster_id = cluster_id.merge(overall['ClusterID'], left_index=True, right_index=True, how='inner')

    return cluster_id


def get_clusters(address, max_cluster_distance_miles, min_cluster_size, column_latitude, column_longitude, column_date, date_range, additional_summary):

    # group dates
    # date_id, grouped = cluster_date(address, column_latitude, column_longitude, column_date)
    date_id = cluster_date(address, column_date, date_range)
    cluster_id = address.merge(date_id, left_index=True, right_index=True)

    # group addresses
    # geo_id = grouped.apply(lambda x: cluster_geo(x, max_cluster_distance_miles, min_cluster_size, column_latitude, column_longitude))
    geo_id = cluster_geo(address, max_cluster_distance_miles, min_cluster_size, column_latitude, column_longitude)
    cluster_id = cluster_id.merge(geo_id, left_index=True, right_index=True)

    # assign an overall id desc with largest size
    cluster_id = assign_id(cluster_id, address, min_cluster_size)

    # summerize cluster
    cluster_summary = get_summary(cluster_id, column_date, additional_summary)

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


def cluster_geo(df, max_cluster_distance_miles, min_cluster_size, column_latitude, column_longitude):

    # convert to kilometers then radians
    eps = max_cluster_distance_miles.value*1.60934/6371   

    # find geographic clusters
    coords = df[[column_latitude, column_longitude]].values
    db = DBSCAN(eps=eps, min_samples=min_cluster_size.value, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
    cluster_id = db.labels_.astype('float')
    cluster_id[cluster_id==-1] = np.nan

    cluster_id = pd.Series(cluster_id, name='ClusterLocation', index=df.index.values, dtype='Int64')

    return cluster_id


def get_summary(cluster_id, column_date, additional_summary):

    cluster_summary = cluster_id.reset_index().groupby('ClusterID')
    plan = {cluster_id.index.name: 'count', column_date: 'max'}
    additional_summary = {key:agg_options[val] for key,val in additional_summary.items()}
    plan = {**plan, **additional_summary}
    cluster_summary = cluster_summary.agg(plan)
    cluster_summary = cluster_summary.reset_index()

    cluster_summary = cluster_summary.rename(columns={
        cluster_id.index.name: 'Cluster Size (count)',
        column_date: f'{column_date} (max)'
    })

    nearby = cluster_id[['ClusterLocation','ClusterID']].reset_index()
    nearby = nearby.groupby(['ClusterLocation','ClusterID'], dropna=False)
    nearby = nearby.agg({cluster_id.index.name: 'count'})
    nearby = nearby.rename(columns={cluster_id.index.name: 'Points'})
    nearby = nearby.reset_index()
    other = nearby.groupby('ClusterLocation').agg({'Points': sum})
    nearby = nearby.merge(other, on='ClusterLocation')
    nearby = nearby.dropna(subset='ClusterID')
    nearby['Nearby Points Not In Cluster (count)'] = nearby['Points_y']-nearby['Points_x']
    nearby = nearby[['ClusterID','Nearby Points Not In Cluster (count)']]
    cluster_summary = cluster_summary.merge(nearby, on='ClusterID')

    return cluster_summary


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