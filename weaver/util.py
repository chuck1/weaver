
class _AArray:
    def __init__(self, engine, _id, d):
        self.engine = engine
        self._id = _id
        self.d = d

    def __getitem__(self, k):
        return self.d[k]

    def __setitem__(self, k, v):
        self.d[k] = v

        self.engine.put('master', self._id, self.d)

    def get(self, k, default):
        if k in self.d:
            return self.d[k]
        else:
            return default


