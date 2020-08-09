from collections import Counter

from coffeeMachine.beverage import Beverage


class BeverageFactory(object):
    description_dct: dict  # dict of beverage name and ingredients(dict of items and quantity)

    def __init__(self, description_dct):
        self.description_dct = description_dct

    def get_beverage(self, name):
        try:
            return Beverage(name, self.description_dct[name])
        except KeyError:
            raise ValueError(name + " is not supported")

    def get_minimum_ingredients(self):
        res = Counter()
        for ing_dct in self.description_dct.values():
            res |= Counter(ing_dct)
        return res
