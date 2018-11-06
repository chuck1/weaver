import argparse
import itertools

import elephant.local_

import weaver.unit
import weaver.design
import weaver.design.query
import weaver.recipe.query
import weaver.recipeinstance
import weaver.recipeinstance.query
import weaver.designinstance
import weaver.designinstance.query

"""
Designinstances

Designinstances are one of the following types

* created to create demand
* created as a material for a recipeinstance



"""

class PurchaseLine:
    def __init__(self, part, q):
        self.part = part
        self.q = q

    def cost(self, manager):
        part = manager.e_designs.get_content(self.part['ref'], {'_id': self.part['_id']})
        cost = part['cost'] * self.q
        return cost

    def print_info(self, manager):
        part = manager.e_designs.get_content(self.part['ref'], {'_id': self.part_id})
        cost = part['cost'] * self.q
        print(f'{part["description"]} {cost}')

class Manager:
    def __init__(self, db, h):
        self.h = h

        self.e_designs = weaver.design.Engine(
                self,
                db.weaver.designs,
                weaver.design.query.Engine(self, db.weaver.designs.queries))

        self.e_designinstances = weaver.designinstance.Engine(
                self,
                db.weaver.designinstances,
                weaver.designinstance.query.Engine(self, db.weaver.designinstances.queries))

        self.e_recipes = weaver.recipe.Engine(
                self,
                db.weaver.recipes,
                weaver.recipe.query.Engine(self, db.weaver.recipes.queries))

        self.e_recipeinstances = weaver.recipeinstance.Engine(
                self,
                db.weaver.recipeinstances,
                weaver.recipeinstance.query.Engine(self, db.weaver.recipeinstances.queries))

        self.e_units = weaver.unit.Engine(self, db.weaver.units)

    def get_inventory(self, part):

        res = self.e_parts.coll.files.aggregate([
            {'$match': {
                'part._id': part['_id'],
                'part.ref': part['ref']
            }},
            {'$group': {'_id': '$part_id', 'total': {'$sum': '$quantity'}}},
            ])

        return sum([r['total'] for r in res])

    def purchase(self, user, part, q):
        self.receive(user, part, q)
        return [PurchaseLine(part, q)]

    def receive(self, user, part, q):
        
        res = self.e_parts.put("master", None, {
            'part': part,
            'quantity': q,
            },
            user)

    def consume(self, m):

        parts = self.e_parts.coll.files.find({'part': m['part'], 'quantity': {'$gt': 0}})
        
        c = m['consumed']

        for part in parts:
            if part['quantity'] >= c:
                part['quantity'] -= c
                c = 0
                self.e_parts.put("master", part["_id"], part, None)
                return
            else:
                c -= part['quantity']
                part['quantity'] = 0
                self.e_parts.put("master", part["_id"], part)

        raise Exception('insufficient part quantity')

    async def _demand_0(self, user):
        async for d0 in self.e_designinstances.find(user, {}):
            yield d0, (await d0.quantity_demand(user))

    async def demand(self, user):

        def keyfunc(_):
            # TODO this ignores ref
            return _.d.d['_id']

        class DemandHelper:
            def __init__(self, di, d, q):
                assert isinstance(q, weaver.quantity.Quantity)
                self.di, self.d, self.q = di, d, q
            
        async def _func0(di, q):
            d = await di.get_design(user)
            return DemandHelper(di, d, q)

        l = [await _func0(di, q) async for di, q in self._demand_0(user)]

        for dh in l:
            c = await dh.di.cost(user)
            #print(f'  {dh.d.d["description"]:40} {dh.q: 8.2f} {c: 8.2f}')
            print(f'  {dh.d.d["description"]:40} {dh.q!r} {c: 8.2f}')

        l = sorted(l, key=keyfunc)

        for k, g in itertools.groupby(l, key=keyfunc):
            g = list(g)

            d = g[0].d

            s = functools.reduce(operator.add, [dh.q for dh in g])

            if s.num == 0: continue

            #print(f'  {d.d["description"]:40} {s: 8.2f}')
            print(f'  {d.d["description"]:40} {s!r}')

            yield d, s


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



