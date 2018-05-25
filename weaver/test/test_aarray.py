
def test_1(user, manager):
    print()

    part_1 = {
            'description': 'part 1',
            'cost': 10,
            }
    
    part_1_id = manager.e_designs.put("master", None, part_1, user["_id"]).inserted_id

    p = manager.e_designs.get_content("master", part_1_id)

    p.user = user

    print(p)

    p['description'] = 'this is a part'



