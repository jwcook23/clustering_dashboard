

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