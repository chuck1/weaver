
import elephant.global_


class Unit(elephant.global_.File):
    def __init__(self, manager, e, d):
        super().__init__(e, d)

class Engine(elephant.global_.Engine):
    def __init__(self, manager, coll):
        super().__init__(coll, "weaver units", elephant.local_.Engine(coll.queries))
        self.manager = manager
        self.h = manager.h

    def _factory(self, d):
        return Unit(self.manager, self, d)


