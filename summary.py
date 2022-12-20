import pandas as pd
import numpy as np

import convert

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


def get_summary(cluster_id, column_time, units_time, units_distance, additional_summary):

    cluster_summary = cluster_id.reset_index().groupby('Cluster ID')
    plan = {
        '# Points': 'first', 'Location ID': 'first', 'Time ID': 'first',
        f'Nearest ({units_distance})': min, f'Length ({units_distance})': max, 
        column_time: ['max','min'],
    }
    cluster_summary = cluster_summary.agg(plan)

    cluster_summary = date_summary(cluster_summary, column_time, units_time)

    cluster_summary = cluster_summary[[
        '# Points', 'Location ID', 'Time ID', 'Time (first)',
        f'Nearest ({units_distance})', f'Length ({units_distance})', f'Nearest ({units_time})', f'Length ({units_time})'
    ]]

    return cluster_summary


# def calculate_additional(cluster_id, column_time, additional_summary):

    # agg_options = {
    #     'min': _min,
    #     'max': _max,
    #     'unique': _unique
    # }

    # TODO: additional summary in another tab?
    # additional_summary = {key:agg_options[val] for key,val in additional_summary.items()}
    # plan = {**plan, **additional_summary}

    # return cluster_summary


def date_summary(cluster_summary, column_time, units_time):

    duration = cluster_summary[(column_time,'max')]-cluster_summary[(column_time,'min')]
    duration = convert.duration_to_numeric(duration, units_time)

    first = cluster_summary[(column_time,'min')]

    nearest = cluster_summary[['Location ID','Pickup Time']]
    nearest = nearest.sort_values(by=[('Location ID','first'), ('Pickup Time', 'max')], ascending=[True, False])
    column = f'Previous {units_time}'
    nearest[column] = nearest[('Pickup Time', 'max')].shift(-1)
    nearest['Previous (Location ID)'] = nearest['Location ID'].shift(-1)
    nearest['Previous (Location ID)'] = nearest['Previous (Location ID)'].astype('Int64')
    nearest[column] = nearest[('Pickup Time', 'max')]-nearest[column]
    nearest.loc[nearest[('Location ID','first')]!=nearest['Previous (Location ID)']] = pd.NA
    nearest = nearest[column]
    nearest = convert.duration_to_numeric(nearest, units_time)

    cluster_summary = cluster_summary.drop(columns=column_time)
    cluster_summary.columns = cluster_summary.columns.droplevel(1)
    cluster_summary['Time (first)'] = first
    cluster_summary[f'Length ({units_time})'] = duration
    cluster_summary[f'Nearest ({units_time})'] = nearest

    return cluster_summary

