import weaver.util

class Part(weaver.util._AArray):
    def __init__(self, manager, e, part_id, d):
        super(Part, self).__init__(manager, e, part_id, d)

    def visit_manager_produce(self, manager, m, q):
        return manager.purchase(m, q)

    def print_info(self, indent='', m=None):
        print(indent + f'{self["description"]}')
        if m is not None:
            print(indent + f'quantity: {m["quantity"]}')
            print(indent + f'consumed: {m["consumed"]}')

    def freeze(self):
        return {
            '_id': self.d['_id'],
            'ref': self.d['_elephant']['refs'][self.d['_elephant']['ref']],
            }

class Assembly(weaver.util._AArray):
    def __init__(self, manager, e, part_id, d):
        super(Assembly, self).__init__(manager, e, part_id, d)

    def visit_manager_produce(self, manager, m, q):
        return self.produce(manager, q)

    def print_info(self, indent='', m0=None):
        print(indent + f'{self["description"]}')
        if m0 is not None:
            print(indent + f'quantity: {m0["quantity"]}')
            print(indent + f'consumed: {m0["consumed"]}')

        for m in self.d['materials']:
            part = self.manager.engine_designs.get_content(m['part']['ref'], {'_id': m['part']['_id']})
            part.print_info(indent + '  ', m)

    def freeze(self):
        return {
            '_id': self.d['_id'],
            'ref': self.d['_elephant']['refs'][self.d['_elephant']['ref']],
            }

    def produce(self, manager, q):

        purchased = []

        for m in self.d['materials']:

            part = manager.engine_designs.get_content(m['part']['ref'], {'_id': m['part']['_id']})
        
            # check inventory

            i = manager.get_inventory(m['part'])

            d = m['quantity'] * q - i

            if d > 0:
                # insufficient inventory
                
                purchased1 = part.visit_manager_produce(manager, m['part'], d)

                purchased += purchased1

                #manager.purchase(m, d)

                pass
            else:
                # sufficient inventory
                pass

            manager.consume(m)

        manager.receive(self.freeze(), q)

        return purchased

