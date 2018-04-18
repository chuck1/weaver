
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
        part = manager.engine.get_content("master", self.part_id)
        cost = part['cost'] * self.q
        return cost

class Manager:
    def __init__(self, engine):
        self.engine = engine
        self.inventory = []
        self.purchased = []

    def get_inventory(self, part_id):
        for i in self.inventory:
            if part_id == i['part_id']:
                return i['quantity']
        return 0

    def purchase(self, part_id, q):
        self.purchased.append(PurchaseLine(part_id, q))
        self.receive(part_id, q)

    def receive(self, part_id, q):
        for i in self.inventory:
            if part_id == i['part_id']:
                i['quantity'] += q
                return
        
        self.inventory.append({
            'part_id': part_id,
            'quantity': q,
            })

    def consume(self, m):
        for i in self.inventory:
            if m['part_id'] == i['part_id']:
                i['quantity'] -= m['consumed']
                return
        raise Exception('part not found')

class Engine:
    def __init__(self, el_engine):
        self.el_engine = el_engine

    def put(self, ref, part_id, part):
        return self.el_engine.put(ref, part_id, part)

    def get_content(self, ref, part_id):
        part = self.el_engine.get_content(ref, part_id)
        if 'assembly' in part.get('tags', []):
            return Assembly(part_id, part)
        else:
            return Part(part_id, part)

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

            part = manager.engine.get_content("master", m['part_id'])
        
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

