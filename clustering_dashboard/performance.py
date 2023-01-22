from functools import wraps
from time import time
import os

def timing(f):
    
    @wraps(f)
    def wrap(*args, **kw):
        time_start = time()
        result = f(*args, **kw)
        duration = time()-time_start
        file = os.path.split(timing.__globals__['__file__'])[1]
        func = f.__name__
        print(f'{file}/{func} {duration:.2f} seconds')
        return result
    return wrap

# @timing
# def test():
#     from time import sleep
#     sleep(3)
#     print(1)
# test()