"""
Author: Juan Amari, François Oren Chikli

File that contains the ItemData class that encompasses the scraped data for a given item.
"""
from datetime import datetime

from data_classes.category_data import CategoryData
from data_classes.price_data import PriceData


class ItemData:
    """
    The main class of the Gearbest Scraper. Makes use of all the other Data classes. Contains a list of prices which is known
    as price_history, which has the historical records for all scraped prices for the given item.
    """

    def __init__(self, item_id: str, item_name: str, item_url: str, timestamp: datetime, main_category: CategoryData,
                 middle_category: CategoryData, granular_category: CategoryData,
                 item_description: str, item_brand: str, item_rating: float, customer_reviews_count: int,
                 customer_answer_count: int,
                 price_history: list,
                 reviews: list):
        self.item_id = item_id
        self.item_name = item_name
        self.item_url = item_url
        self.timestamp = timestamp
        self.main_category = main_category
        self.middle_category = middle_category
        self.granular_category = granular_category
        self.item_description = item_description
        self.item_brand = item_brand
        self.item_rating = item_rating
        self.customer_reviews_count = customer_reviews_count
        self.customer_answer_count = customer_answer_count
        self.price_history = price_history
        self.reviews = reviews

    def append_new_price(self, price: PriceData):
        """
        Adds a new price to the item's price history.
        :param price: The price object to add to.
        """
        self.price_history.append(price)

    def __repr__(self):
        """
        Returns the string representation of the values within the class.
        :return: Returns the string representation of the values within the class.
        """
        return str(vars(self))
