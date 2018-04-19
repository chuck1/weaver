
class _AArray:
    def __getitem__(self, k):
        return self.d[k]

    def get(self, k, default):
        if k in self.d:
            return self.d[k]
        else:
            return default


