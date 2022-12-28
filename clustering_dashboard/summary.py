import pandas as pd

from clustering_dashboard import convert, aggregations


def get_summary(details, column_time, units_time, units_distance, additional_summary):

    location_summary, time_summary = id_aggregation(details)

    cluster_summary = details.reset_index().groupby('Cluster ID')
    plan = {
        'Location ID': 'first', 'Time ID': 'first',
        f'Nearest ({units_distance})': min, f'Length ({units_distance})': max, 
        column_time: ['max','min'],
    }
    num_points = cluster_summary.size()
    num_points.name = '# Points'
    cluster_summary = cluster_summary.agg(plan)
    cluster_summary['# Points'] = num_points

    cluster_summary = time_aggregation(cluster_summary, column_time, units_time)

    cluster_summary = cluster_summary[[
        '# Points', 'Location ID', 'Time ID', 'Time (first)',
        f'Nearest ({units_distance})', f'Length ({units_distance})', f'Nearest ({units_time})', f'Length ({units_time})'
    ]]

    return cluster_summary, location_summary, time_summary


# def calculate_additional(details, column_time, additional_summary):

    # agg_options = {
    #     'min': _min,
    #     'max': _max,
    #     'unique': _unique
    # }

    # TODO: additional summary in another tab?
    # additional_summary = {key:agg_options[val] for key,val in additional_summary.items()}
    # plan = {**plan, **additional_summary}

    # return cluster_summary


def id_aggregation(details):

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

def time_aggregation(cluster_summary, column_time, units_time):

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

