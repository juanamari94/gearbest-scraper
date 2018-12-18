"""
Authors: Juan Amari, François Oren Chikli

Main class for Gearbest Enrichment
"""

import logging
import time

from database_classes.gearbest_mysql_manager import GearbestMySQLManager
from enrichment.errors.enrichment_error import EnrichmentError
from enrichment.language_enricher import LanguageEnricher

logger = logging.getLogger("GearbestEnricher")

REVIEW_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS `review_languages` (
`id` int NOT NULL AUTO_INCREMENT,
`review_id` int NOT NULL,
`detected_language` varchar(50) DEFAULT NULL,
`certainty_percentage` int DEFAULT NULL,
PRIMARY KEY (`id`),
FOREIGN KEY(`review_id`) REFERENCES reviews(`id`)
) ENGINE=InnoDB
"""

SELECT_REVIEWS_QUERY = """
SELECT id, review_text from `reviews` WHERE `id` NOT IN (SELECT `review_id` FROM `review_languages`) LIMIT %s;
"""

INSERTION_QUERY = """
INSERT IGNORE INTO `review_languages` (`review_id`, `detected_language`, `certainty_percentage`) VALUES (%s, %s, %s);
"""


class GearbestEnricher:

    def __init__(self, max_rows, rpm, database="gearbest"):
        """
        Main initiazlization method.
        :param max_rows: Max rows allowed by the plan.
        :param rpm: Maximum amount of requests per minute for the API.
        :param database: The database to write into.
        """
        self.database = database
        self.max_rows = max_rows
        self.allowed_rpm = rpm
        self.create_review_language_table()

    def update_languages(self, api_key):
        """
        Goes over the amount of rows defined by maxrows from the database and retrieves the language
        for each review and inserts it into a new table.
        """
        with GearbestMySQLManager(self.database) as mgr:
            logger.info("Retrieving reviews...")
            cur = mgr.execute_selection_query(SELECT_REVIEWS_QUERY, [self.max_rows])
            reviews = cur.fetchall()
            enricher = LanguageEnricher(api_key=api_key)
            for review in reviews:
                review_text = review["review_text"]
                review_id = review["id"]
                logger.info("Detecting Language for Review ID: {}".format(review_id))
                try:
                    results = enricher.get_language(review_text)
                    detected_language, confidence = results["language_name"], results["confidence_percentage"]
                    mgr.execute_manipulation_query(INSERTION_QUERY, [review_id, detected_language, confidence])
                    logger.info("Language Detected for Review ID: {} is {}, with confidence {}".format(review_id,
                                                                                                       detected_language,
                                                                                                       confidence))
                    # Sleep for however long to match the allowed RPM.
                except EnrichmentError as err:
                    logger.error("An error occured: {}".format(err))
                finally:
                    time.sleep(self.allowed_rpm / 59)

    def create_review_language_table(self):
        """
        Method to create the review_language table if it doesn't exist.
        """
        with GearbestMySQLManager(self.database) as mgr:
            logger.info("Creating table if it doesn't exist for Review Languages.")
            mgr.create_table(REVIEW_TABLE_QUERY)
