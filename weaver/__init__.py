


class PurchaseLine:
    def __init__(self, part, q):
        self.part = part
        self.q = q

class Manager:
    def __init__(self, engine):
        self.engine = engine
        self.inventory = []
        self.purchased = []

    def get_inventrory(self, part_id):
        for i in self.inventory:
            if part_id == i.d['part_id']:
                return i.d['quantity']
        return 0

    def purchase(self, part, q):
        for i in self.inventory:
            if part.d['_id'] == i.d['part_id']:
                i.d['quantity'] += q
                self.purchased.append(PurchaseLine(part, q))

    def consume(self, m):
        for i in self.inventory:
            if m.d['part_id'] == i.d['part_id']:
                i.d['quantity'] -= m['consumed']
                return
        raise Exception('part not found')

class Assembly:
    def __init__(self, d):
        self.d = d

    def produce(self, manager, q):

        for m in self.d['materials']:

            # check inventory

            i = manager.get_inventory(m['part_id'])

            d = m['quantity'] - i

            if d > 0:
                # insufficient inventory

                manager.purchase(m, d)

                pass
            else:
                # sufficient inventory
                pass

            manager.consume(m)

