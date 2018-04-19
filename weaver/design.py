import weaver.util

class Part(weaver.util._AArray):
    def __init__(self, part_id, d):
        self.part_id = part_id
        self.d = d

    def visit_manager_produce(self, manager, m, q):
        manager.purchase(m, q)

class Assembly(weaver.util._AArray):
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

