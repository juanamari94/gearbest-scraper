"""
Author: Juan Amari, François Oren Chikli
Contains the class that manages the conversion of item data dictionaries into a proper class in order to ease
data manipulation before database insertion.
"""

import logging

from data_classes.category_data import CategoryData
from data_classes.item_data import ItemData
from data_classes.price_data import PriceData
from data_classes.review_data import ReviewData

logger = logging.getLogger("GearbestLogger")


class DataParser:
    """
    Class that manages the conversion of item data dictionaries into a proper class in order to ease
    data manipulation before database insertion.
    """

    # Map that transforms a currency literal into its proper name.
    CURRENCY_TYPES = {'₪': 'NIS', '$': 'USD', '£': 'GBP', 'C$': 'CAD', 'HK$': 'HDK', "円": "JPY", "R$": "BRL",
                      "DKr.": "DKK", "MXN$": "MXN", "Rp": "IDR", "€": "EUR", "AU$": "AUD", "CHF": "CHF",
                      "NZ$": "NZD", "руб.": "RUB", "NKr.": "NOK", "SKr": "SEK", "Col$": "COP", "฿": "TBH", "zł": "PLN",
                      "Ft": "HUF", "RM": "MYR", "lei": "RON", "₴": "UAH", "NT$": "TWD", "РСД": "RSD", "лв.": "BGN",
                      "¥": "CNY", "Kn": "HRK", "د.إ": "AED", "₩": "KRW", "ARS$": "ARS", "TL": "TRY", "₦": "NGN",
                      "R": "ZAR",
                      "S$": "SGD", "ر.س": "SAR", "PHP": "PHP", "CL$": "CLP", "Kč": "CZK", "Rs": "INR", "د.م.": "MAD",
                      "S/.": "PEN"}

    @staticmethod
    def create_item_data(item_data):
        """
        Assembles an ItemData object from the scraped item_data for a given product within GearBest.
        :param item_data: Data scraped from an item within GearBest.
        :return: An ItemData object that contains properly formatted data ready to be inserted into the database.
        """
        timestamp = item_data.get('timestamp')
        item_name = item_data.get('item_name')
        item_url = item_data.get('item_url')
        item_id = item_data.get('item_id')
        main_category_id = item_data.get('main_category_id')
        main_category_name = item_data.get('main_category_name')
        main_category_url = item_data.get('main_category_url')
        middle_category_id = item_data.get('middle_category_id')
        middle_category_name = item_data.get('middle_category_name')
        middle_category_url = item_data.get('middle_category_url')
        granular_category_id = item_data.get('granular_category_id')
        granular_category_name = item_data.get('granular_category_name')
        granular_category_url = item_data.get('granular_category_url')
        description = item_data.get('description')
        brand = item_data.get('brand')
        rating = item_data.get('rating')
        customer_reviews_count = item_data.get('customer_reviews_count')
        customer_answer_count = item_data.get('customer_answer_count')
        price = item_data.get('price')
        currency_type = item_data.get('currency_type')
        raw_reviews = item_data.get('reviews')
        discount_percentage = item_data.get('discount_percentage')

        main_category = CategoryData(main_category_id, main_category_name, main_category_url)
        middle_category = CategoryData(middle_category_id, middle_category_name, middle_category_url)
        granular_category = CategoryData(granular_category_id, granular_category_name, granular_category_url)

        # If for some reason there's only 2 nested categories instead of 3, granular and middle will be the same.
        if not granular_category.category_id:
            granular_category = middle_category if middle_category.category_id else main_category

        if raw_reviews:
            reviews = [DataParser.create_review_data(review) for review in raw_reviews]
        else:
            reviews = None

        price_record = None
        if price and currency_type and timestamp:
            price_record = PriceData(price,
                                     DataParser.CURRENCY_TYPES.get(currency_type),
                                     timestamp,
                                     discount_percentage)
        price_history = [price_record]

        return ItemData(item_id, item_name, item_url, timestamp, main_category, middle_category, granular_category,
                        description, brand, rating, customer_reviews_count, customer_answer_count, price_history,
                        reviews)

    @staticmethod
    def create_review_data(review_data):
        """
        Helper method that assembles ReviewData objects from given reviews within a list of dictionaries where each
        dictionary represents review data.
        :param review_data: A list of dictionaries where each list element is review data.
        :return: A list of ReviewData objects that contain all the information for each list element.
        """
        user_name = review_data.get('user_name')
        user_id = review_data.get('user_id')
        review_title = review_data.get('review_title')
        review_rating = review_data.get('review_rating')
        review_attributes = review_data.get('review_attributes')
        review_text = review_data.get('review_text')
        post_timestamp = review_data.get('post_timestamp')
        item_id = review_data.get('item_id')
        return ReviewData(user_name, user_id, review_title, review_rating, review_attributes, review_text,
                          post_timestamp, item_id)
