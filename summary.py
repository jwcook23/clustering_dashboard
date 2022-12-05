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

    cluster_summary = calculate_simple(cluster_id, column_date, additional_summary)

    cluster_summary = find_overlap(cluster_summary, cluster_id, 'Location')

    # TODO: use distance matrix directly to calculate
    # distance = distance_id(cluster_id, distance)
    # cluster_summary = calculate_distance(cluster_summary, distance)

    return cluster_summary


def calculate_simple(cluster_id, column_date, additional_summary):

    agg_options = {
        'min': _min,
        'max': _max,
        'unique': _unique
    }

    cluster_summary = cluster_id.reset_index().groupby('Cluster ID')
    plan = {
        'Cluster (count)': 'first', 
        'Location ID': 'first', 'Location (count)': 'first', 'Nearest (miles)': min, 'Span (miles)': max, 
        'Date ID': 'first', 'Date (count)': 'first', column_date: ['max','min'],
    }
    # TODO: additional summary in another tab?
    # additional_summary = {key:agg_options[val] for key,val in additional_summary.items()}
    # plan = {**plan, **additional_summary}
    cluster_summary = cluster_summary.agg(plan)
    duration = cluster_summary[column_date]['max']-cluster_summary[column_date]['min']
    duration = duration.astype('string')
    cluster_summary = cluster_summary.drop(columns=column_date)
    cluster_summary.columns = cluster_summary.columns.droplevel(1)
    cluster_summary['Length (duration)'] = duration

    return cluster_summary


def find_overlap(cluster_summary, cluster_id, name_id):

    column = f'{name_id} ID'
    agg = f'{name_id} (count)'

    nearby = cluster_id[[column,'Cluster ID']]
    nearby = nearby.groupby(column)
    nearby = nearby.agg({'Cluster ID': 'unique'})
    nearby[agg] = nearby['Cluster ID'].str.len()-1
    nearby = nearby.explode('Cluster ID')
    nearby['Cluster ID'] = nearby['Cluster ID'].astype('Int64')
    cluster_summary = cluster_summary.merge(nearby, on='Cluster ID')
    cluster_summary = cluster_summary.set_index('Cluster ID')

    return cluster_summary

