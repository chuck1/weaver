import time

import pytest
import pymongo

import weaver
import elephant.local_

def test_1(manager):
    print()

    part_1 = {
            'description': 'part 1',
            'cost': 10,
            }
    part_1_id = manager.engine_designs.put(None, part_1).inserted_id

    part_2 = {
            'description': 'part 2',
            'cost': 10,
            }
    part_2_id = manager.engine_designs.put(None, part_2).inserted_id

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
    assy_1_id = manager.engine_designs.put(None, assy_1).inserted_id

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
    assy_2_id = manager.engine_designs.put(None, assy_2).inserted_id

    a = manager.engine_designs.get_content(assy_2_id)

    purchased = a.produce(manager, 1)

    a.print_info()

    cost = sum([p.cost(manager) for p in purchased])

    print(f'cost={cost}')

    print('parts:')
    for p in manager.engine_parts.el_engine.db.files.find({}):
        for k, v in p.items():
            if k == '_elephant':
                print('elephant')
                print(v)
            else:
                print(f'{k:16} {v}')

        
    assy_2 = manager.engine_designs.get_content({"_id": assy_2_id})

    print(assy_2)
    print(list(assy_2.commits()))

