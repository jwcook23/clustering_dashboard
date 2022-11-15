from functools import lru_cache
import pandas as pd


@lru_cache()
def load_data():

    # https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page

    # https://docs.microsoft.com/en-us/azure/open-datasets/dataset-taxi-yellow?tabs=azureml-opendatasets
    # pip install azureml-opendatasets


    df = pd.read_parquet(
        'yellow_tripdata_2010-01.parquet',
        columns = ['pickup_latitude','pickup_longitude','pickup_datetime','fare_amount']
    )
    df.index.name = 'TripID'

    df = df[(df['pickup_latitude']!=0) & (df['pickup_longitude']!=0)]

    df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'])

    return df.head(1000)

address = load_data()