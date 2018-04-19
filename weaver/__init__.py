import argparse

import weaver.design

class PurchaseLine:
    def __init__(self, part_id, q):
        self.part_id = part_id
        self.q = q

    def cost(self, manager):
        part = manager.engine_designs.get_content("master", {'_id': self.part_id})
        cost = part['cost'] * self.q
        return cost

    def print_info(self, manager):
        part = manager.engine_designs.get_content("master", {'_id': self.part_id})
        cost = part['cost'] * self.q
        print(f'{part["description"]} {cost}')

class Manager:
    def __init__(self, engine_designs, engine_parts):
        self.engine_designs = engine_designs
        self.engine_parts = engine_parts

        self.engine_designs.manager = self
        self.engine_parts.manager = self

    def get_inventory(self, part_id):

        res = self.engine_parts.collection.aggregate([
            {'$match': {'part_id': part_id}},
            {'$group': {'_id': '$part_id', 'total': {'$sum': '$quantity'}}},
            ])

        return sum([r['total'] for r in res])

    def purchase(self, part_id, q):
        self.receive(part_id, q)
        return [PurchaseLine(part_id, q)]

    def receive(self, part_id, q):
        
        res = self.engine_parts.put("master", None, {
            'part_id': part_id,
            'quantity': q,
            })

    def consume(self, m):

        parts = self.engine_parts.collection.find({'part_id': m['part_id'], 'quantity': {'$gt': 0}})
        
        c = m['consumed']

        for part in parts:
            if part['quantity'] >= c:
                part['quantity'] -= c
                c = 0
                self.engine_parts.put("master", part["_id"], part)
                return
            else:
                c -= part['quantity']
                part['quantity'] = 0
                self.engine_parts.put("master", part["_id"], part)

        raise Exception('insufficient part quantity')

class Engine:
    def __init__(self, el_engine):
        self.el_engine = el_engine

    @property
    def collection(self):
        return self.el_engine.collection

    def put(self, ref, part_id, part):
        return self.el_engine.put(ref, part_id, part)

    def put_new(self, ref, part):
        res = self.el_engine.put(ref, None, part)
        return self.get_content(ref, {'_id': res.inserted_id})

    def get_content(self, ref, filt):
        part = self.el_engine.get_content(ref, filt)
        if part is None: return
        part_id = part['_id']
        if 'materials' in part:
            return weaver.design.Assembly(self.manager, self, part_id, part)
        else:
            return weaver.design.Part(self.manager, self, part_id, part)

class EngineParts:
    def __init__(self, el_engine):
        self.el_engine = el_engine

    @property
    def collection(self):
        return self.el_engine.collection

    def put(self, ref, part_id, part):
        return self.el_engine.put(ref, part_id, part)

    def get_content(self, ref, part_id):
        return self.el_engine.get_content(ref, part_id)


def shell(args):
    import pymongo
    import elephant.collection_local

    client = pymongo.MongoClient(args.client)
    database = client[args.db]

    e_designs = elephant.collection_local.CollectionLocal(database.test_designs)
    e_designs = Engine(e_designs)

    e_parts = elephant.collection_local.CollectionLocal(database.test_parts)
    e_parts = EngineParts(e_parts)

    manager = Manager(e_designs, e_parts)

    if args.s is not None:
        with open(args.s) as f:
            s = f.read()
            exec(s)

    from bson.objectid import ObjectId

    import readline
    import code
    variables = globals().copy()
    variables.update(locals())
    shell = code.InteractiveConsole(variables)
    shell.interact()
    
def main(av):

    parser = argparse.ArgumentParser()

    def _help(args):
        parser.print_usage()

    parser.set_defaults(func=_help)

    subparsers = parser.add_subparsers()

    parser_shell = subparsers.add_parser('shell')
    parser_shell.add_argument('client')
    parser_shell.add_argument('db')
    parser_shell.add_argument('-s')
    parser_shell.set_defaults(func=shell)

    args = parser.parse_args(av)
    args.func(args)



