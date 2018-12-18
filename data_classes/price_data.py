"""
Author: Juan Amari, François Oren Chikli

File that contains the PriceData class that encompasses the scraped data for a given price during a scraper execution.
"""


class PriceData:
    """
    Class that encompasses the scraped data for a given price during a scraper execution
    """

    def __init__(self, price, currency_type, scraped_timestamp, discount):
        self.price = price
        self.currency_type = currency_type
        self.scraped_timestamp = scraped_timestamp
        self.discount = discount

    def __repr__(self):
        return "Price: {} - Currency_Type: {} - Timestamp: {} - Discount: {}".format(self.price,
                                                                                     self.currency_type,
                                                                                     self.scraped_timestamp,
                                                                                     self.discount)
