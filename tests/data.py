import pandas as pd


df = pd.DataFrame.from_records([
    {"ClusterID_Label":2,"TripID":10211,"Latitude":40.733988,"Longitude":-73.989888,"Pickup Time":"2010-01-27 15:13:00","Fare Amount":4.5},
    {"ClusterID_Label":2,"TripID":2662,"Latitude":40.733968,"Longitude":-73.989095,"Pickup Time":"2010-01-27 15:14:00","Fare Amount":45.0},

    {"ClusterID_Label":1,"TripID":7034,"Latitude":40.764601,"Longitude":-73.972212,"Pickup Time":"2010-01-27 15:30:00","Fare Amount":13.7},
    {"ClusterID_Label":1,"TripID":294,"Latitude":40.762288,"Longitude":-73.974477,"Pickup Time":"2010-01-27 15:31:00","Fare Amount":4.5},
    {"ClusterID_Label":1,"TripID":7329,"Latitude":40.76639,"Longitude":-73.969363,"Pickup Time":"2010-01-27 15:32:00","Fare Amount":8.9},

    {"ClusterID_Label":0,"TripID":5890,"Latitude":40.73246,"Longitude":-73.98254,"Pickup Time":"2010-01-27 15:20:00","Fare Amount":7.3},
    {"ClusterID_Label":0,"TripID":2801,"Latitude":40.761867,"Longitude":-73.97524,"Pickup Time":"2010-01-27 15:21:00","Fare Amount":3.7},
    {"ClusterID_Label":0,"TripID":4230,"Latitude":40.764512,"Longitude":-73.977476,"Pickup Time":"2010-01-27 15:22:00","Fare Amount":7.7},
    {"ClusterID_Label":0,"TripID":1192,"Latitude":40.759227,"Longitude":-73.970431,"Pickup Time":"2010-01-27 15:23:00","Fare Amount":19.3},

    {"ClusterID_Label":-1,"TripID":857,"Latitude":40.753758,"Longitude":-73.975353,"Pickup Time":"2010-01-27 15:50:00","Fare Amount":6.1}
])
df = df.set_index('TripID')
df['ClusterID_Label'] = df['ClusterID_Label'].astype('Int64')
df['Pickup Time'] = pd.to_datetime(df['Pickup Time'])