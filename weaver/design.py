import elephant.local_
import weaver.util

class Design(elephant.local_.File):
    def __init__(self, manager, e, d):
        super(Design, self).__init__(e, d)

    def visit_manager_produce(self, user, manager, m, q):
        return manager.purchase(user, m, q)

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

    def list_upstream(self, user, filt):

        for m in self.d.get("materials", []):
            if m is None: continue

            u_id = m["part"]["_id"]
                
            u = self.manager.e_designs.get_content(m["part"]["ref"], {"_id": u_id})

            yield



class Assembly(Design):
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

