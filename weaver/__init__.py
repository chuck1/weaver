
class _AArray:
    def __getitem__(self, k):
        return self.d[k]

    def get(self, k, default):
        if k in self.d:
            return self.d[k]
        else:
            return default

class PurchaseLine:
    def __init__(self, part_id, q):
        self.part_id = part_id
        self.q = q

    def cost(self, manager):
        part = manager.engine_designs.get_content("master", self.part_id)
        cost = part['cost'] * self.q
        return cost

class Manager:
    def __init__(self, engine_designs, engine_parts):
        self.engine_designs = engine_designs
        self.engine_parts = engine_parts
        self.purchased = []

    def get_inventory(self, part_id):

        res = self.engine_parts.collection.aggregate([
            {'$match': {'part_id': part_id}},
            {'$group': {'_id': '$part_id', 'total': {'$sum': '$quantity'}}},
            ])

        return sum([r['total'] for r in res])

    def purchase(self, part_id, q):
        self.purchased.append(PurchaseLine(part_id, q))
        self.receive(part_id, q)

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

    def get_content(self, ref, part_id):
        part = self.el_engine.get_content(ref, part_id)
        if 'assembly' in part.get('tags', []):
            return Assembly(part_id, part)
        else:
            return Part(part_id, part)

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

class Part(_AArray):
    def __init__(self, part_id, d):
        self.part_id = part_id
        self.d = d

    def visit_manager_produce(self, manager, m, q):
        manager.purchase(m, q)

class Assembly(_AArray):
    def __init__(self, part_id, d):
        self.part_id = part_id
        self.d = d

    def visit_manager_produce(self, manager, m, q):
        self.produce(manager, q)

    def produce(self, manager, q):
        
        for m in self.d['materials']:

            part = manager.engine_designs.get_content("master", m['part_id'])
        
            # check inventory

            i = manager.get_inventory(m['part_id'])

            d = m['quantity'] - i

            if d > 0:
                # insufficient inventory
                
                part.visit_manager_produce(manager, m['part_id'], d)
                #manager.purchase(m, d)

                pass
            else:
                # sufficient inventory
                pass

            manager.consume(m)

        manager.receive(self.part_id, q)

