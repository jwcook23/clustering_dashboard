import numpy as np
import pandas as pd
from scipy.sparse.csgraph import connected_components


from clustering_dashboard import convert

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


def get_clusters(df, distance_radians, distance_units, distance_threshold, duration_seconds, time_units, time_threshold):

    # label records for same location
    distance_criteria = compare_distance(distance_radians, distance_units, distance_threshold)
    location_id = assign_id(distance_criteria)

    # label records for same time
    time_criteria = compare_time(duration_seconds, time_units, time_threshold)
    time_id = assign_id(time_criteria)

    # label records for same location and time
    cluster_id = assign_id([distance_criteria, time_criteria])

    # assign to original input
    df[['Location ID', 'Time ID', 'Cluster ID']] = pd.DataFrame({
        'Location ID': location_id, 'Time ID': time_id, 'Cluster ID': cluster_id
    })

    return df


def compare_distance(distance_radians, distance_units, distance_threshold):

    threshold_converted = convert.distance_to_radians(distance_threshold, distance_units)

    distance_criteria = (np.array(distance_radians) <= threshold_converted)

    return distance_criteria


def compare_time(duration_seconds, time_units, time_threshold):

    threshold_converted = convert.time_to_seconds(time_threshold, time_units)

    duration_criteria = (np.array(duration_seconds) <= threshold_converted)

    return duration_criteria


def assign_id(comparison_criteria):

    if isinstance(comparison_criteria, list):
        comparison_criteria = np.array(comparison_criteria)
        comparison_criteria = np.all(comparison_criteria, axis=0)

    _, cluster_label = connected_components(comparison_criteria)

    # assign lower id values to larger sized groups and assign noise points
    cluster_label = pd.DataFrame(cluster_label, columns=['Original'])
    arranged = pd.DataFrame(cluster_label.value_counts(), columns=['Size'])
    arranged['ID'] = range(0, len(arranged))
    arranged['ID'] = arranged['ID'].astype('Int64')
    arranged.loc[arranged['Size']==1, 'ID'] = pd.NA
    cluster_label = cluster_label.merge(arranged[['ID']], left_on='Original', right_index=True)
    cluster_label = cluster_label['ID'].sort_index()

    return cluster_label
