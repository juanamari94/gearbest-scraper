"""
Author: Juan Amari, François Oren Chikli

File that contains the CategoryData class that encompasses the scraped data for a given category during a scraper execution.
"""


class CategoryData:
    """
    Class that encompasses the scraped data for a given category during a scraper execution.
    """

    def __init__(self, category_id, name, url):
        self.category_id = category_id
        self.name = name
        self.url = url

    def __repr__(self):
        return str(vars(self))
