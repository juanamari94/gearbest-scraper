"""
Author: Juan Amari, François Oren Chikli

File that contains the ReviewData class that encompasses the scraped data for a given review.
"""


class ReviewData:
    """
    Class that encompasses the scraped data for a given review.
    """

    def __init__(self, user_name, user_id, review_title, review_rating, review_attributes, review_text, post_timestamp,
                 item_id):
        self.user_name = user_name
        self.user_id = user_id
        self.review_title = review_title
        self.review_rating = review_rating
        self.review_attributes = review_attributes
        self.review_text = review_text
        self.post_timestamp = post_timestamp
        self.item_id = item_id
