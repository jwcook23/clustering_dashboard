from datetime import datetime, timedelta
import random
import pandas as pd

today = datetime.now()
before = today - timedelta(days=3)

df = pd.DataFrame.from_records([
    {'LocationGroup': 0, 'Latitude': 30.315008, 'Longitude': -81.680390, 'GroupDate': 0, 'Timestamp': today},
    {'LocationGroup': 0, 'Latitude': 30.314855, 'Longitude': -81.680879, 'GroupDate': 0, 'Timestamp': today},
    {'LocationGroup': 0, 'Latitude': 30.314901, 'Longitude': -81.680186, 'GroupDate': 0, 'Timestamp': today},
    {'LocationGroup': 1, 'Latitude': 30.311655, 'Longitude': -81.680513, 'GroupDate': 0, 'Timestamp': today},
    {'LocationGroup': 1, 'Latitude': 30.311484, 'Longitude': -81.680309, 'GroupDate': 0, 'Timestamp': today},
    {'LocationGroup': 1, 'Latitude': 30.311363, 'Longitude': -81.681002, 'GroupDate': 1, 'Timestamp': before},
    {'LocationGroup': 1, 'Latitude': 30.311771, 'Longitude': -81.681066, 'GroupDate': 1, 'Timestamp': before},
    {'LocationGroup': 1, 'Latitude': 30.312248, 'Longitude': -81.681077, 'GroupDate': 1, 'Timestamp': before},
])
df.index = random.sample(range(1, len(df)*3), len(df))
df.index.name = 'SampleID'

df.to_parquet('tests/Sample.gzip')