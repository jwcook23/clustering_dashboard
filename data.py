import pandas as pd

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

df = df.head(10000)

df = df.rename(columns={
    'pickup_latitude': 'Latitude', 'pickup_longitude': 'Longitude',
    'pickup_datetime': 'Pickup Time', 'fare_amount': 'Fare Amount'
})

df.to_parquet('C:/Users/jacoo/Desktop/Temp/CabData.gzip')
