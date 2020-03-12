import pickle
import json
import ujson
import simplejson
from time import time

test_runs = 2

if __name__ == "__main__":
    from preprocessing import file_handler
    start = time()
    data = file_handler.read_pickle('/work/haukurpj/data/mideind/enriched.pickle')
    r = time() - start
    print(f'initial read={r}')

    # simplejson
    module = 'simplejson'
    start = time()
    for i in range(test_runs):
        with open('tmp', mode='w+') as f:
            simplejson.dump(data, f)
    w = time() - start
    start = time()
    for i in range(test_runs):
        with open('tmp', mode='r+') as f:
            simplejson.load(f)
    r = time() - start
    print(f"Module=({module}, Write={w}, Read={r}")

    # ujson
    module = 'ujson'
    start = time()
    for i in range(test_runs):
        with open('tmp', mode='w+') as f:
            ujson.dump(data, f)
    w = time() - start
    start = time()
    for i in range(test_runs):
        with open('tmp', mode='r+') as f:
            ujson.load(f)
    r = time() - start
    print(f"Module=({module}, Write={w}, Read={r}")

    
    # json
    module = 'json'
    start = time()
    for i in range(test_runs):
        with open('tmp', mode='r+') as f:
            json.dump(data, f)
    w = time() - start
    start = time()
    for i in range(test_runs):
        with open('tmp', mode='r+') as f:
            json.load(f)
    r = time() - start
    print(f"Module=({module}, Write={w}, Read={r}")

    # pickle
    module = 'pickle'
    start = time()
    for i in range(test_runs):
        with open('tmp', mode='r+b') as f:
            pickle.dump(data, f)
    w = time() - start
    start = time()
    for i in range(test_runs):
        with open('tmp', mode='r+b') as f:
            pickle.load(f)
    r = time() - start
    print(f"Module=({module}, Write={w}, Read={r}")
