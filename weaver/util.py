import bson
import datetime

import elephant.file

class _AArray(elephant.file.File):
    def __init__(self, manager, e, _id, d):
        super(_AArray, self).__init__(e, d)
        self.manager = manager
        self._id = _id

    def __getitem__(self, k):
        return self.d[k]

    def __setitem__(self, k, v):
        self.d[k] = v

        self.e.put("master", self._id, self.d)

    def get(self, k, default):
        if k in self.d:
            return self.d[k]
        else:
            return default

    def to_array(self):
        d0 = dict(self.d)
        return d0



