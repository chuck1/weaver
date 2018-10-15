import bson
import logging

import elephant.local_
import weaver.util

logger = logging.getLogger(__name__)

class Design(elephant.local_.doc.Doc):
    """
    fields

    'unit'           - default unit
    'conversions'   - conversions between units of different fundamental measurement
    'onhand'        - desired onhand quantity. used for automaticly adding to shopping list
    'onhand_thresh' - threshold for purchase quantity when buying to meet onhand quantity
    """

    def __init__(self, e, d, _d, is_subobject=False):
        super().__init__(e, d, _d, is_subobject)
        self.d["_collection"] = "weaver designs"

    def visit_manager_produce(self, user, manager, m, q):
        return manager.purchase(user, m, q)

    def print_info(self, indent='', m=None):
        print(indent + f'{self["description"]}')
        if m is not None:
            print(indent + f'quantity: {m["quantity"]}')
            print(indent + f'consumed: {m["consumed"]}')

    async def quantity_onhand(self):
        return self.d.get("onhand", weaver.quantity.Quantity(0, self.d.get("unit", None)))

    async def quantity_onhand_threshold(self):
        return self.d.get("onhand_threshold", weaver.quantity.Quantity(0, self.d.get("unit", None)))

    async def list_recipes_negative(self, user):

        async for r in self.e.h.weaver.e_recipes.find(user, {"materials.Material.design.id": self.d["_id"]}):
            q = r.quantity(self)
            if q.num < 0: yield r

    async def list_upstream(self, user, filt):
 
        async for r in self.e.h.weaver.e_recipes.find(user, {"materials.design.id": self.d["_id"]}):
            q = r.quantity(self)
            if q.num > 0: continue
            yield r

    async def conversion(self, u0, u1):
        """
        conversion factor from u0 to u1
        x (u1) = y (u10 * c (u1 / u0)
        """
        print("conversion")
        print(f"{u0!r}")
        print(f"{u1!r}")
        r0 = u0.reduce()
        r1 = u1.reduce()
        print(f"{u0!r}")
        print(f"{u1!r}")
        c0 = [r0, r1]
        c1 = [r1, r0]

        if r0 == r1:
            return weaver.quantity.Quantity(1)

        print("looking for")
        print(f"    {c0}")
        for c, y in self.d.get("conversions", []):
            r = [c[0].reduce(), c[1].reduce()]
            print(f"try {r!r}")
            if r == c0:
                return weaver.quantity.Quantity({"num": y, "unit": weaver.quantity.unit.ComposedUnit([u1], [u0])})

        print("looking for")
        print(f"    {c1}")
        for c, y in self.d.get("conversions", []):
            r = [c[0].reduce(), c[1].reduce()]
            print(f"try {r!r} {r == c1}")
            if r == c1:
                return weaver.quantity.Quantity({"num": 1/y, "unit": weaver.quantity.unit.ComposedUnit([u1], [u0])})

        raise Exception("no conversion")

    async def produce(self, user, quantity):
        if not isinstance(quantity, weaver.quantity.Quantity):
            raise TypeError()

        d0 = {
                'mode':     weaver.designinstance.DesignInstanceMode.DEMAND.value,
                'design':   self.freeze(),
                'quantity': quantity,
                }

        d1 = await self.e.manager.e_designinstances.put(
                user,
                None,
                d0,
                )

        return d1


    async def cost(self, user, q):
        # yield the cost of all possible options for producing this design
        
        if not weaver.quantity.unit.unit_eq(self.d.get("unit"), q.unit):

            try:
                c = await self.conversion(q.unit, self.d.get("unit"))
            except:
                raise Exception(f'failed to convert {q.unit} to {self.d.get("unit")} for design {self.d.get("description")}')
                raise

            q = q * c

            if not weaver.quantity.unit_eq(self.d.get("unit"), q.unit):
                raise Exception(f'units must be equal {self.d.get("unit")} {q.unit}')
            #logger.error(f'units must be equal {self.d.get("unit")} {q.unit}')
            #return

        async for r in self.list_recipes_negative(user):
            q1 = r.quantity(self)
            q2 = q / q1
            async for _ in r.cost(user, q2): yield _

        if 'cost' in self.d:
            assert isinstance(self.d["cost"], (int, float))
            yield self.d["cost"]

class DEPAssembly(Design):
    def __init__(self, manager, e, d):
        super(Assembly, self).__init__(manager, e, d)

    def print_info(self, indent='', m0=None):
        print(indent + f'{self["description"]}')
        if m0 is not None:
            print(indent + f'quantity: {m0["quantity"]}')
            print(indent + f'consumed: {m0["consumed"]}')

        for m in self.d['materials']:
            part = self.manager.e_designs.get_content(m['part']['ref'], {'_id': m['part']['_id']})
            part.print_info(indent + '  ', m)

    def produce(self, user, manager, q):

        purchased = []

        for m in self.d['materials']:

            part = manager.e_designs.get_content(m['part']['ref'], user, {'_id': m['part']['_id']})
        
            # check inventory

            i = manager.get_inventory(m['part'])

            d = m['quantity'] * q - i

            if d > 0:
                # insufficient inventory
                
                purchased1 = part.visit_manager_produce(user, manager, m['part'], d)

                purchased += purchased1

                #manager.purchase(m, d)

                pass
            else:
                # sufficient inventory
                pass

            manager.consume(m)

        manager.receive(user, self.freeze(), q)

        return purchased

class Engine(weaver.engine.EngineLocal):

    _doc_class = Design

    def __init__(self, manager, coll, e_queries):
        super().__init__(manager, coll, e_queries)
        self.manager = manager
        self.h = manager.h

    async def create_indices(self):
        self.coll.files.create_index([("description", "text")])


