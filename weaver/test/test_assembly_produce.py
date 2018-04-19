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

@pytest.fixture
def manager(database):
    e = elephant.collection_local.CollectionLocal(database.test)
    e = weaver.Engine(e)
    e_parts = elephant.collection_local.CollectionLocal(database.test_parts)
    e_parts = weaver.EngineParts(e_parts)
    manager = weaver.Manager(e, e_parts)
    return manager

def test_1(manager):
    print()

    part_1 = {
            'description': 'part 1',
            'cost': 10,
            }
    part_1_id = manager.engine_designs.put("master", None, part_1).inserted_id

    part_2 = {
            'description': 'part 2',
            'cost': 10,
            }
    part_2_id = manager.engine_designs.put("master", None, part_2).inserted_id

    assy_1 = {
            'description': 'assy 1',
            'materials': [
                {
                    'part_id': part_1_id,
                    'quantity': 1,
                    'consumed': 0,
                    },
                ],
            }
    assy_1_id = manager.engine_designs.put("master", None, assy_1).inserted_id

    assy_2 = {
        'description': 'assy 2',
        'materials': [
            {
                'part_id': part_1_id,
                'quantity': 1,
                'consumed': 0,
                },
            {
                'part_id': part_2_id,
                'quantity': 2,
                'consumed': 2,
                },
            {
                'part_id': assy_1_id,
                'quantity': 1,
                'consumed': 1,
                },
            ]
        }
    assy_2_id = manager.engine_designs.put("master", None, assy_2).inserted_id

    a = manager.engine_designs.get_content('master', assy_2_id)

    a.produce(manager, 1)

    cost = sum([p.cost(manager) for p in manager.purchased])

    print(f'cost={cost}')

    print('parts:')
    for p in manager.engine_parts.collection.find({}):
        for k, v in p.items():
            if k == '_elephant':
                print('elephant')
                for c_id, c in v['commits'].items():
                    print('  commit')
                    for ch in c['changes']:
                        print(f'    {ch}')
            else:
                print(f'{k:16} {v}')

