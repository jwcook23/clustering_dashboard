import numpy as np

def UniqueCountNonNA(series):
    
    count = series.dropna()
    count = count.nunique()

    return count

def CountNA(series):

    count = series[series.isna()]
    count = len(count)

    return count


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

def _unique_list(series):
    
    series = series.dropna()
    series = series.explode()
    series = series[series.str.len()>0]
    series = series.drop_duplicates()
    series = series.tolist()
    series = ', '.join(series)

    return series