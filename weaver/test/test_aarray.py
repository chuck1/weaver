
def test_1(manager):
    print()

    part_1 = {
            'description': 'part 1',
            'cost': 10,
            }
    
    part_1_id = manager.engine_designs.put("master", None, part_1).inserted_id

    p = manager.engine_designs.get_content('master', part_1_id)

    print(p)

    p['description'] = 'this is a part'



