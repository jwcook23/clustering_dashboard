import numpy as np
import pandas as pd

def _min(series):

    val = series.min()
    if np.isnan(val):
        val = ''
    else:
        val = str(val)
    return val

def _max(series):

    val = series.max()
    if np.isnan(val):
        val = ''
    else:
        val = str(val)
    return val

def _unique(series):
    
    series = series.dropna()
    series = series.explode()
    series = series[series.str.len()>0]
    series = series.drop_duplicates()
    series = series.tolist()
    series = ', '.join(series)

    return series

def distance_id(cluster_id, distance):
    
    # set self references (distance of zero) as nan
    np.fill_diagonal(distance, np.nan)
    
    # assign cluster id to distance values
    distance = distance.reshape(distance.size, 1)
    distance = pd.DataFrame(distance, columns=['Distance'])
    distance['ClusterID1'] = cluster_id['ClusterID'].repeat(len(cluster_id)).reset_index(drop=True)
    distance['ClusterID2'] = cluster_id['ClusterID'].tolist() * len(cluster_id)

    return distance

def get_summary(cluster_id, distance, column_date, additional_summary):

    cluster_summary = calcualte_simple(cluster_id, column_date, additional_summary)

    cluster_summary = find_nearby(cluster_summary, cluster_id)

    distance = distance_id(cluster_id, distance)
    cluster_summary = calculate_distance(cluster_summary, distance)


    return cluster_summary


def calcualte_simple(cluster_id, column_date, additional_summary):

    agg_options = {
        'min': _min,
        'max': _max,
        'unique': _unique
    }

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

    return cluster_summary


def find_nearby(cluster_summary, cluster_id):

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


def calculate_distance(cluster_summary, distance):
    
    # calculate min and max distances for each combination
    grouped = distance.groupby(['ClusterID1','ClusterID2'])
    grouped = grouped.agg(['min','max'])
    grouped.columns = ['min', 'max']
    grouped = grouped.reset_index()

    # convert to miles
    grouped[['min','max']] = grouped[['min','max']]*3958.756

    # calculate max spread within a cluster
    spread = grouped.loc[grouped['ClusterID1']==grouped['ClusterID2'],['ClusterID1','max']]
    spread = spread.rename(columns={'ClusterID1': 'ClusterID', 'max': 'Cluster Spread (miles)'})
    cluster_summary = cluster_summary.merge(spread, on='ClusterID')

    # calculate min distance to another cluster
    nearest = grouped.loc[grouped['ClusterID1']!=grouped['ClusterID2'],['ClusterID1','min']]
    nearest = nearest.sort_values(by=['ClusterID1','min'], ascending=True)
    nearest = nearest.drop_duplicates(subset='ClusterID1', keep='first')
    nearest = nearest.rename(columns={'ClusterID1': 'ClusterID', 'min': 'Next Cluster (miles)'})
    cluster_summary = cluster_summary.merge(nearest, on='ClusterID')

    return cluster_summary