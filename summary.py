import pandas as pd
import numpy as np

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


def get_summary(cluster_id, column_date, additional_summary):

    cluster_summary = cluster_id.reset_index().groupby('Cluster ID')
    plan = {
        'Cluster (count)': 'first', 'Location ID': 'first', 'Date ID': 'first',
        'Nearest (miles)': min, 'Span (miles)': max, 
        column_date: ['max','min'],
    }
    cluster_summary = cluster_summary.agg(plan)

    cluster_summary = date_summary(cluster_summary, column_date)

    return cluster_summary


# def calculate_additional(cluster_id, column_date, additional_summary):

    # agg_options = {
    #     'min': _min,
    #     'max': _max,
    #     'unique': _unique
    # }

    # TODO: additional summary in another tab?
    # additional_summary = {key:agg_options[val] for key,val in additional_summary.items()}
    # plan = {**plan, **additional_summary}

    # return cluster_summary


def date_summary(cluster_summary, column_date):

    duration = cluster_summary[column_date]['max']-cluster_summary[column_date]['min']
    duration = duration.astype('string')

    first = cluster_summary[column_date]['min']

    cluster_summary = cluster_summary.drop(columns=column_date)
    cluster_summary.columns = cluster_summary.columns.droplevel(1)
    cluster_summary['Time (first)'] = first
    cluster_summary['Length (duration)'] = duration

    return cluster_summary

