import pandas as pd
import pytest

@pytest.fixture(scope='module')
def sample():

    data = pd.read_csv('tests/Sample20Records.csv')
    yield data

def test_multifeature(sample):

    print(1)