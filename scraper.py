"""
Author: François Oren Chikli, Juan Amari

Main file
"""

import logging
import os
import traceback
from datetime import datetime

import click

from data_classes.data_parser import DataParser
from database_classes.gearbest_query_manager import GearbestQueryManager
from gearbest_scraping.gearbest_scraper import GearbestScraper

FILE_PLACEHOLDER = "%s.csv"
scraping_date = datetime.now().strftime("%Y_%m_%d|%H_%M_%S")

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(WORKING_DIR, "logs")

logger = logging.getLogger("GearbestLogger")
logging.getLogger("GearbestLogger").setLevel(logging.DEBUG)
if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)
fh = logging.FileHandler(os.path.join(LOGS_DIR, "scraper_logs.log"))
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)


def upload_item_to_database(all_departments):
    """
    Helper function that reunites all scraped data and writes it to a CSV file.
    :param all_departments: The scraped data from Gearbest.
    """
    for catalog in all_departments:
        for item in catalog:
            if item:
                try:
                    item_data = DataParser.create_item_data(item)
                    GearbestQueryManager.add_product(item_data)
                except Exception as err:
                    logger.error(str(err) + traceback.format_exc())


@click.group()
def cli():
    """
    Entry function for the command line interface created by Clicky.
    """
    pass


@click.command(help="Scrapes all of Gearbest's departments.")
@click.option('--maxproducts', default=50, help="Maximum amount of products to scrape from a given department.")
@click.option('--reviewlimit', default=10, help="Maximum amount of review pages to scrape from each product page.")
@click.option('--sortnewest/--sortrelevant', default=True,
              help="Whether to sort catalog by newest products or most relevant ones.")
def scrape_gearbest(maxproducts, reviewlimit, sortnewest):
    """
    Main scraping function. Scrapes all departments of gearbest with the given parameters.
    :param maxproducts: The maximum amount of products to scrape per department.
    :param reviewlimit: The maximum amount of review pages to scrape per product.
    :param sortnewest: Whether to sort products by newest or most relevant.
    """
    with GearbestScraper() as scraper:
        try:
            all_items = scraper.scrape_all_departments(product_limit_per_department=maxproducts,
                                                       review_limit=reviewlimit,
                                                       sort_by_newest=sortnewest)
            upload_item_to_database(all_items)
        except Exception as err:
            logger.error(str(err) + traceback.format_exc())


@click.command(help="Scrapes a specific catalog from Gearbest.")
@click.argument('url')
@click.option('--maxproducts', default=50, help="Maximum amount of products to scrape from a given department.")
@click.option('--reviewlimit', default=10, help="Maximum amount of review pages to scrape from each product page.")
@click.option('--sortnewest/--sortrelevant', default=True,
              help="Whether to sort catalog by newest products or most relevant ones.")
def scrape_catalog(url, maxproducts, reviewlimit, sortnewest):
    """
    Scrapes an entire catalog from Gearbest given the limiting parameters.
    :param url: The catalog URL.
    :param maxproducts: The maximum amount of products to scrape per department.
    :param reviewlimit: The maximum amount of review pages to scrape per product.
    :param sortnewest: Whether to sort products by newest or most relevant.
    """
    with GearbestScraper() as scraper:
        try:
            all_items = scraper.scrape_paginated_catalog(url, maxproducts, reviewlimit, sort_by_newest=sortnewest)
            upload_item_to_database([all_items])
        except Exception as err:
            logger.error(str(err) + traceback.format_exc())


@click.command(help="Scrapes an item from Gearbest.")
@click.argument('url')
@click.option('--scrapereviews', default=True,
              help="Flag that indicates whether to scrape reviews from an item or not.")
@click.option('--reviewlimit', default=10, help="Maximum amount of review pages to scrape from each product page.")
def scrape_item(url, scrapereviews, reviewlimit):
    """
    Scrapes an item from Gearbest from the given URL.
    :param url: The catalog URL.
    :param maxproducts: The maximum amount of products to scrape per department.
    :param reviewlimit: The maximum amount of review pages to scrape per product.
    """
    with GearbestScraper() as scraper:
        try:
            item_data = scraper.scrape_item(url, scrapereviews, reviewlimit)
            upload_item_to_database([[item_data]])
        except Exception as err:
            logger.error(str(err) + traceback.format_exc())


def main_db():
    from database_classes.gearbest_mysql_manager import GearbestMySQLManager
    with GearbestMySQLManager() as mgr:
        mgr.create_and_set_database()
        mgr.create_tables()


if __name__ == "__main__":
    main_db()
    cli.add_command(scrape_gearbest)
    cli.add_command(scrape_catalog)
    cli.add_command(scrape_item)
    logger.info("### LOGGER FOR {} ###".format(scraping_date))
    cli()
