import numpy as np
import numpy.ma as ma
import pandas as pd
from sklearn.metrics.pairwise import haversine_distances

def calc_distance(df, column_latitude, column_longitude):
    
    coords = np.radians(df[[column_latitude, column_longitude]].values)
    distance = haversine_distances(coords, coords)
    distance = ma.array(distance)

    return distance

def convert_to_mercator(df, latitude, longitude):
    """Converts wgs94 decimal longitude/latitude to web mercator format."""
    k = 6378137
    df["Longitude_mercator"] = df[longitude] * (k * np.pi/180.0)
    df["Latitude_mercator"] = np.log(np.tan((90 + df[latitude]) * np.pi/360.0)) * k
    return df


def near_geo(df1, df2, threshold_miles=25):
    '''Find the values in df2 within threshold_miles of df1. Both df1 and df2 contain the columns Latitude and Longitude.'''

    # remove duplicates form lookup
    # df2 = df2.loc[df2.index.duplicated(keep='last'),['Latitude','Longitude']]

    # find the distance in miles between df1 and df2 for each value in df1 using haversine distance
    lats1, lats2 = np.meshgrid(df2['Latitude'].values, df1['Latitude'].values)
    lons1, lons2 = np.meshgrid(df2['Longitude'].values, df1['Longitude'].values)
    lat_dif = np.radians(lats1 - lats2)
    long_dif = np.radians(lons1 - lons2)
    sin_d_lat = np.sin(lat_dif / 2.)
    sin_d_long = np.sin(long_dif / 2.)
    step_1 = (sin_d_lat ** 2) + (sin_d_long ** 2) * np.cos(np.radians(lats1[0])) * np.cos(np.radians(lats2[0])) 
    step_2 = 2 * np.arctan2(np.sqrt(step_1), np.sqrt(1-step_1))
    dist = step_2 * 3958.75

    # filter for stations within the distance of threshold_miles
    indices = df2.index.to_numpy()
    df2_index_name = df2.index.name
    indices = np.where(dist<=threshold_miles, indices, -1)
    df_distance = pd.DataFrame({
        df2_index_name: indices.tolist(),
        'DistanceMiles': dist.tolist()
    }, index=df1.index)
    df_distance = df_distance.apply(pd.Series.explode)
    df_distance = df_distance[df_distance[df2_index_name]!=-1]

    # sort stations by distance to claim
    # df_distance = df_distance.sort_values('DistanceMiles')

    # include records without threshold criteria match
    # missing = address.index[~address.index.isin(df_distance.index)]
    missing = df1.index[~df1.index.isin(df_distance.index)]
    missing = pd.DataFrame({df2_index_name: [None]*len(missing), 'DistanceMiles': [pd.NA]*len(missing)}, index=missing)
    df_distance = pd.concat([df_distance, missing])
    df_distance['DistanceMiles'] = df_distance['DistanceMiles'].astype('Float64')

    # include df2 details
    # df_distance = df_distance.merge(df2, left_on=df2_index_name, right_index=True, how='left')

    # sort by clost distance and the index in the main dataframe
    df_distance = df_distance.sort_values(by=[df1.index.name, 'DistanceMiles'], na_position='last')

    return df_distance


def calc_haversine_distance(lat1, lon1, lat2, lon2):
    '''Calculate distance between lat/lon coordinates in miles.'''

    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    newlon = lon2 - lon1
    newlat = lat2 - lat1

    haver_formula = np.sin(newlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(newlon/2.0)**2

    dist_miles = 2 * np.arcsin(np.sqrt(haver_formula )) * 3958

    return dist_miles

