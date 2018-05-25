import time

import pytest
import pymongo

import weaver
import elephant.local_

def test_1(user, manager):
    print()
    ref = "master"
    part_1 = {
            'description': 'part 1',
            'cost': 10,
            }
    part_1_id = manager.e_designs.put("master", None, part_1, user["_id"]).inserted_id
    part_1 = manager.e_designs.get_content("master", part_1_id)

    assy_1 = {
            'description': 'assy 1',
            'materials': [
                {
                    'part': part_1.freeze(),
                    'quantity': 1,
                    'consumed': 0,
                    },
                ],
            }
    assy_1_id = manager.e_designs.put("master", None, assy_1, user["_id"]).inserted_id
    assy_1 = manager.e_designs.get_content("master", assy_1_id)

    purchased = assy_1.produce(manager, 1)

def test_2(user, manager):
    print()
    ref = "master"
    part_1 = {
            'description': 'part 1',
            'cost': 10,
            }
    part_1_id = manager.e_designs.put("master", None, part_1, user["_id"]).inserted_id
    part_1 = manager.e_designs.get_content("master", part_1_id)

    part_2 = {
            'description': 'part 2',
            'cost': 10,
            }
    part_2_id = manager.e_designs.put("master", None, part_2, user["_id"]).inserted_id
    part_2 = manager.e_designs.get_content("master", part_2_id)

    assy_1 = {
            'description': 'assy 1',
            'materials': [
                {
                    'part': part_1.freeze(),
                    'quantity': 1,
                    'consumed': 0,
                    },
                ],
            }
    assy_1_id = manager.e_designs.put("master", None, assy_1, user["_id"]).inserted_id
    assy_1 = manager.e_designs.get_content("master", assy_1_id)

    assy_2 = {
        'description': 'assy 2',
        'materials': [
            {
                'part': part_1.freeze(),
                'quantity': 1,
                'consumed': 0,
                },
            {
                'part': part_2.freeze(),
                'quantity': 2,
                'consumed': 2,
                },
            {
                'part': assy_1.freeze(),
                'quantity': 1,
                'consumed': 1,
                },
            ]
        }
    assy_2_id = manager.e_designs.put(ref, None, assy_2, user["_id"]).inserted_id

    a = manager.e_designs.get_content(ref, assy_2_id)

    purchased = a.produce(manager, 1)

    a.print_info()

    cost = sum([p.cost(manager) for p in purchased])

    print(f'cost={cost}')

    print('parts:')
    for p in manager.e_parts.find({}):
        for k, v in p.d.items():
            if k == '_elephant':
                print('elephant')
                print(v)
            else:
                print(f'{k:16} {v}')

        
    assy_2 = manager.e_designs.get_content(ref, {"_id": assy_2_id})

    print(assy_2)
    print(list(assy_2.commits()))

