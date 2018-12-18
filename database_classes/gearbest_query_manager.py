"""
Author: Juan Amari
File that manages the queries that go into the Gearbest Scraping database.
"""

from data_classes.item_data import ItemData
from data_classes.price_data import PriceData
from database_classes.gearbest_mysql_manager import GearbestMySQLManager

# These are basic queries
SELECT_QUERY = "SELECT %s FROM %s WHERE %s"

DATABASE_NAME = "gearbest"

INSERT_ITEM_QUERY = """
INSERT IGNORE INTO items (item_id, 
                item_name, 
                item_url, 
                timestamp, 
                granular_cat_id, 
                item_description, 
                item_brand, 
                item_rating, 
                customer_reviews_count, 
                customer_answer_count
                )
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

INSERT_PRICE_QUERY = """
INSERT INTO prices (price, currency_type, scrape_timestamp, discount_percentage, item_id)
VALUES (%s, %s, %s, %s, %s)
"""

INSERT_REVIEW_QUERY = """
INSERT IGNORE INTO reviews (user_id, 
                user_name, 
                review_title, 
                review_rating, 
                review_attributes, 
                review_text, 
                post_timestamp,
                item_id)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

INSERT_INTO_CHILD_CATEGORY = """
INSERT IGNORE INTO * (category_id,
               category_name,
               category_url, 
               parent_category_id)
VALUES (%s, %s, %s, %s)
"""

INSERT_INTO_MAIN_CATEGORY = """
INSERT IGNORE INTO main_categories (category_id,
                       category_name,
                       category_url)
VALUES (%s, %s, %s)
"""

INSERT_INTO_ITEM_TO_CAT = """
INSERT IGNORE INTO item_to_cat (item_id, category_id)
VALUES (%s, %s)
"""


class GearbestQueryManager:
    """
    Class that manages the queries into the gearbest MySQL database.
    """

    @staticmethod
    def add_product(item_data: ItemData):
        """
        This is the most complex query. It needs to add everything else first.
        Order is very important.
        :param item_data: An ItemData object.
        """
        GearbestQueryManager.add_categories_from_item(item_data)
        GearbestQueryManager.add_item(item_data)
        GearbestQueryManager.add_item_cat_relationship(item_data)
        GearbestQueryManager.add_price_from_item(item_data)
        GearbestQueryManager.add_reviews_from_item(item_data)

    @staticmethod
    def add_item(item_data: ItemData):
        with GearbestMySQLManager(DATABASE_NAME) as sql_mgr:
            sql_mgr.execute_manipulation_query(INSERT_ITEM_QUERY, [
                item_data.item_id,
                item_data.item_name,
                item_data.item_url,
                item_data.timestamp,
                item_data.granular_category.category_id,
                item_data.item_description,
                item_data.item_brand,
                item_data.item_rating,
                item_data.customer_reviews_count,
                item_data.customer_answer_count
            ])

    @staticmethod
    def add_categories_from_item(item_data: ItemData):
        """
        Fetches the categories from Item Data and inserts them into the granular_categories, middle_categories and
        main_categories tables.
        :param item_data: An ItemData object that contains the required data to insert.
        """
        main_cat = item_data.main_category
        middle_cat = item_data.middle_category
        granular_cat = item_data.granular_category

        with GearbestMySQLManager(DATABASE_NAME) as sql_mgr:
            if main_cat:
                sql_mgr.execute_manipulation_query(INSERT_INTO_MAIN_CATEGORY, [main_cat.category_id,
                                                                               main_cat.name,
                                                                               main_cat.url])

            if middle_cat:
                sql_mgr.execute_manipulation_query(INSERT_INTO_CHILD_CATEGORY.replace("*", "middle_categories"),
                                                   [middle_cat.category_id,
                                                    middle_cat.name,
                                                    middle_cat.url,
                                                    main_cat.category_id])

            sql_mgr.execute_manipulation_query(INSERT_INTO_CHILD_CATEGORY.replace("*", "granular_categories"),
                                               [granular_cat.category_id,
                                                granular_cat.name,
                                                granular_cat.url,
                                                middle_cat.category_id])

    @staticmethod
    def add_price_from_item(item_data: ItemData):
        """
        Adds a price to the price history of an item from the given data.
        :param item_data: ItemData object that contains the scraped data.
        """
        price_history = item_data.price_history
        for price in price_history:
            if not isinstance(price, PriceData):
                continue
            with GearbestMySQLManager(DATABASE_NAME) as sql_mgr:
                sql_mgr.execute_manipulation_query(INSERT_PRICE_QUERY, [price.price,
                                                                        price.currency_type,
                                                                        price.scraped_timestamp,
                                                                        price.discount,
                                                                        item_data.item_id
                                                                        ])

    @staticmethod
    def add_reviews_from_item(item_data: ItemData):
        """
        Manages the addition of reviews into the reviews table within the Gearbest database. Reviews are contained within
        and ItemData object.
        :param item_data: The given ItemData object.
        """
        reviews = item_data.reviews
        if not reviews:
            return
        with GearbestMySQLManager(DATABASE_NAME) as sql_mgr:
            for review in reviews:
                sql_mgr.execute_manipulation_query(INSERT_REVIEW_QUERY,
                                                   [review.user_id,
                                                    review.user_name,
                                                    review.review_title,
                                                    review.review_rating,
                                                    review.review_attributes,
                                                    review.review_text,
                                                    review.post_timestamp,
                                                    item_data.item_id])

    @staticmethod
    def add_item_cat_relationship(item_data: ItemData):
        """
        Since Items can belong to many categories and many categories can belong to an item, this method manages
        the weak entity table that encompasses this relationship. It feeds off ItemData an ItemData object.
        :param item_data: The given ItemData object that contains the scraped elements for that specific item.
        """
        with GearbestMySQLManager(DATABASE_NAME) as sql_mgr:
            sql_mgr.execute_manipulation_query(INSERT_INTO_ITEM_TO_CAT,
                                               [item_data.item_id, item_data.granular_category.category_id])
