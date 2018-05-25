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
    e_designs = weaver.EngineDesigns(database.test)
    e_parts = weaver.EngineParts(database.test_parts)
    manager = weaver.Manager(e_designs, e_parts)
    return manager

@pytest.fixture
def user(database):
    user_id = database.users.insert_one({}).inserted_id
    return database.users.find_one({"_id": user_id})

