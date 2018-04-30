import time
import pymongo
import pytest
import elephant
import weaver

@pytest.fixture(scope='module')
def client():
    client = pymongo.MongoClient()
    yield client
    
@pytest.fixture
def database(client):
    db_name =f'test_{int(time.time())}'
    db = client[db_name]
    yield db
    client.drop_database(db_name)

@pytest.fixture
def manager(database):
    e_designs = elephant.local_.Local(database.test)
    e_designs = weaver.Engine(e_designs)

    e_parts = elephant.local_.Local(database.test_parts)
    e_parts = weaver.EngineParts(e_parts)

    manager = weaver.Manager(e_designs, e_parts)
    return manager


