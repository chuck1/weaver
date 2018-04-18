import time

import pytest
import pymongo

import weaver
import elephant.collection_local

@pytest.fixture
def client():
    client = pymongo.MongoClient()
    yield client
    
@pytest.fixture
def database(client):
    db_name =f'test_{int(time.time())}'
    db = client[db_name]
    yield db
    client.drop_database(db_name)

def test_1(database):

    e = elephant.collection_local.CollectionLocal(database.test)
    
    part_1_id = e.put("master", None, {'description': 'part 1'}).inserted_id

    manager = weaver.Manager(e)

    a = weaver.Assembly({
        'materials': [
            {
                'part_id': part_1_id,
                'quantity': 1,
                'consumed': 0,
                }
            ]
        })

    a.produce(manager, 1)

