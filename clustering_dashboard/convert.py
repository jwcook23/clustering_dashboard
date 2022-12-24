import numpy as np

def duration_to_numeric(dur, time_units):

    if time_units == 'days':
        dur = dur.dt.total_seconds()/60/60/24
    elif time_units == 'hours':
        dur = dur.dt.total_seconds()/60/60
    elif time_units == 'minutes':
        dur = dur.dt.total_seconds()/60
    else:
        raise RuntimeError('Invalid time units.')

    return dur


def radians_to_distance(rads, distance_units):

    if distance_units == 'miles':
        dist = rads * 3958
    elif distance_units == 'feet':
        dist = rads * 3958 * 5280
    elif distance_units == 'kilometers':
        dist = dist * 6371
    else:
        raise RuntimeError('Invalid distance units.')

    return dist

def distance_to_radians(dist, distance_units):

    if distance_units == 'miles':
        rads = dist / 3958.8
    elif distance_units == 'feet':
        rads = dist / 3958.8 / 5280
    elif distance_units == 'kilometers':
        rads = dist / 6371
    else:
        raise RuntimeError('Invalid distance units.')

    return rads


def latlon_to_mercator(latitude, longitude):

    k = 6378137
    longitude_mercator = longitude * (k * np.pi/180.0)
    latitude_mercator = np.log(np.tan((90 + latitude) * np.pi/360.0)) * k

    return latitude_mercator, longitude_mercator