

class Quantity:
    def __init__(self, num_or_dict):
        if isinstance(num_or_dict, dict):
            assert "num" in num_or_dict
            assert "unit" in num_or_dict

            self.num = num_or_dict["num"]
            self.unit = num_or_dict["unit"]

        elif isinstance(num_or_dict, (int, float)):
            
            self.num = num_or_dict["num"]
            self.unit = None

        else:
            raise Exception("expected dict, int, or float")

    #def __rtruediv__(self, other):
    #    assert isinstance(other, (int, float)):
            

