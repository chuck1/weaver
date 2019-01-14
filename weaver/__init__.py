import argparse
import datetime
import functools
import itertools
import logging
import operator

import elephant.local_

import weaver.unit
import weaver.design
import weaver.design.query
import weaver.recipe.query
import weaver.recipeinstance
import weaver.recipeinstance.query
import weaver.designinstance
import weaver.designinstance.query

logger = logging.getLogger(__name__)

"""
Designinstances

Designinstances are one of the following types

* created to create demand
* created as a material for a recipeinstance



"""

class DesignRef:
    def __init__(self, ref, d):
        self.ref = ref
        self.d = d

    async def ainit(self):
        # dont add target here because we could end up with multipe versions of a design, each with a target
        self.O = weaver.quantity.Quantity(0, self.d.get("unit", None))

        self.T = await self.d.quantity_onhand_threshold()
        self.I = weaver.quantity.Quantity(0, self.d.get("unit", None))
        self.D = weaver.quantity.Quantity(0, self.d.get("unit", None))
        self.R = weaver.quantity.Quantity(0, self.d.get("unit", None))

        # lists to store designinstances
        self.lines_inventory = []

    def quantity_buy(self):
        O = self.O # target inventory
        T = self.T # threadhold
        I = self.I # actual inventory
        R = self.R # demand for recipeinstances
        D = self.D # manual demand

        

        logger.info(f'description = {self.d.d.get("description")}')
        logger.info(f'unit        = {self.d.d.get("unit")}')
        logger.info(f"O = {O}")
        logger.info(f"T = {T}")
        logger.info(f"I = {I}")
        logger.info(f"R = {R}")
        logger.info(f"D = {D}")

        b0 = R + D - I
        b1 = O + R + D - I
        b2 = b0

        if b0.num > 0:
            # must buy to meet demand
            b2 = b1
        else:
            if b1.num > 0:
                # would buy to meet target
                if T is None:
                    # no threshold, buy
                    b2 = b1
                elif -b0 <= T:
                    # inventory minus demand is less than threshold, buy
                    b2 = b1
 
        if b2.num < 0:
            b2.num = 0

        logger.info(f"shop = {b2}")

        return b2

    async def __encode__(self, h, user, mode):
        args = [
		self.d,
                self.lines_inventory,
                self.I,
                self.quantity_buy(),
                ]
        args = await elephant.util.encode(h, user, mode, args)
        return {"ShoppingItem": args}

class ShoppingHelper:
    def __init__(self):
        self.design_refs = []

    async def get_design_ref(self, ref, d):
        for dr in self.design_refs:
            if dr.ref == ref:
                return dr
        dr = DesignRef(ref, d)
        await dr.ainit()
        self.design_refs.append(dr)
        return dr

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

class LineInventory:
    def __init__(self, di, y):
        self.di = di
        self.y = y

    async def __encode__(self, h, user, mode):
        args = [self.di, self.y]
        args = await elephant.util.encode(h, user, mode, args)
        return {self.__class__.__name__: args}

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

    async def shopping(self, ws, user, body, when=None, recipeinstance_before=None, criteria=None):
        """
        recipeinstance_before - if not None, only count recipeinstances that are scheduled before 
        """
 
        # check all recipeinstances. this makes sure that all the designinstances have been
        # generated for all recipeinstances
        async for ri in self.e_recipeinstances.find(user, {}):
            async for _ in ri.get_designinstances(user):
                pass

        helper = ShoppingHelper()

        logger.info(f'when = {when}')

        now = datetime.datetime.utcnow()
        when = when or datetime.datetime.utcnow()

        logger.info(f'when = {when}')

        async for d in self.e_designs._find():
            ref = d.freeze()
            dr = await helper.get_design_ref(ref, d)

        ###############

        async for di in self.e_designinstances._find({}):

            di.init1()

            d = await di.get_design(user)
            dr = await helper.get_design_ref(di.d["design"], d)

            # INVENTORY

            y = await di.d["behavior"].quantity_inventory(user)

            if y is not None:
                dr.lines_inventory.append(LineInventory(di, y))
                dr.I += y
 
            # RECIPEINSTANCE

            y = await di.d["behavior"].quantity_recipeinstance_for(user, recipeinstance_before)

            if y is not None: dr.R += y
 
            # INVENTORY

            y = await di.d["behavior"].quantity_demand(user)

            if y is not None:
                dr.D += y
 
            # ORDER

            y = await di.d["behavior"].quantity_order(user, when)
 
            if y is not None:
                dr.I += y

	# Target
        async for d in self.e_designs._find({}):

            dr = await helper.get_design_ref(d.freeze(), d)
            
            dr.O += await d.quantity_target()

        # return
        for dr in helper.design_refs:
            if criteria is not None:
                b = eval(criteria)
                #if dr.quantity_buy().num == 0: continue
                if b: continue
            yield dr


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



