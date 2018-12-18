"""
Authors: Juan Amari, François Oren Chikli
Main entry point for the Enrichment API for Gearbest.
"""

import logging
import os
from datetime import datetime

import click

import enrichment.language_enricher_secrets as secrets
from enrichment.errors.quota_error import QuotaError
from enrichment.gearbest_enricher import GearbestEnricher
from scraper import LOGS_DIR

enrichment_date = datetime.now().strftime("%Y_%m_%d|%H_%M_%S")

logger = logging.getLogger("GearbestEnricher")
logging.getLogger("GearbestEnricher").setLevel(logging.DEBUG)
if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)
fh = logging.FileHandler(os.path.join(LOGS_DIR, "enrichment_logs.log"))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)
MAX_PLAN_REVIEWS = 500000
API_MAX_RPM = 60


@click.command(help="Enriches the database by adding the detected language of user reviews.")
@click.option('--max_reviews', default=MAX_PLAN_REVIEWS, help="Maximum amount of reviews ")
@click.option('--api_key', default=secrets.API_KEY)
@click.option('--rpm', default=API_MAX_RPM)
def enrich_gearbest_update_languages(max_reviews, api_key, rpm):
    """
    Entry method for the enricher. Receives one parameter: max_reviews.
    :param max_reviews: The maximum amount of reviews to enrich given API limitations.
    """
    try:
        logger.info("### ENRICHMENT PROCESS START - DATE: {} ###".format(enrichment_date))
        logger.info("Enriching {} rows.".format(max_reviews))
        GearbestEnricher(max_reviews, rpm).update_languages(api_key)
    except QuotaError as err:
        logger.error("Quota has been exceeded. Execution will now be terminated. Error: {}".format(err))
    except Exception as err:
        logger.error("There was an unknown error: {}".format(err))
    finally:
        logger.info("### ENRICHMENT PROCESS END ###")


if __name__ == '__main__':
    enrich_gearbest_update_languages()
