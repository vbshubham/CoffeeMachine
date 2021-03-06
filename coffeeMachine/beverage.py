from collections import Counter


class Beverage(object):
    ingredients: Counter  # counter of items and quantity required for this beverage
    name: str  # name of the beverage

    def __init__(self, name, ingredients):
        self.name = name
        self.ingredients = Counter(ingredients)
