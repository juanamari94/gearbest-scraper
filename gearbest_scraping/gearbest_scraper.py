"""
Authors: François Oren Chikli, Juan Amari
File for the scraper class.
"""

import logging
import math

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

from database_classes.gearbest_mysql_manager import GearbestMySQLManager
from database_classes.gearbest_query_manager import DATABASE_NAME
from gearbest_scraping.errors.parsing_error import ParsingError
from gearbest_scraping.gearbest_parser import GearbestParser

GEARBEST_URL = r"https://www.gearbest.com/"
REVIEW_NEXT_XPATH = r"//div[@class='goodsReviews_pageWrap']//a[@data-goto='next']"
SORTING_OPTIONS_XPATH = r"//*[@id='js-reviewFilter']/li[4]"
REVIEW_MOST_RECENT_XPATH = r"//*[@id='js-reviewFilter']/li[4]/div/div/a[4]"


class GearbestScraper:

    def __init__(self):
        """Initialization function. Instances a Chrome webdriver for scraping."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)
        self.logger = logging.getLogger("GearbestLogger")

    def __enter__(self):
        """Context manager function, returns self the scope is created."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager function, closes the web driver once out of scope."""
        self.driver.close()

    def scrape_all_departments(self, product_limit_per_department=math.inf, review_limit=math.inf, sort_by_newest=True):
        """
        Wrapper function that consumes all other independent functionalities and scrapes all of GearBest with limits imposed
        by the given parameters.
        :param product_limit_per_department: How many products to scrape from each department.
        :param review_limit: How many review pages to scrape from each product.
        :param sort_by_newest: Whether to sort products by newest or most relevant.
        :return: A list containing all the items and their reviews.
        """
        department_content = self.retrieve_source_from_url(GEARBEST_URL)
        departments = set(GearbestParser.parse_departments(department_content))
        self.logger.info(
            "Avoiding Top Brands and Fashion departments due to duplicate elements" +
            ", for those elements use the single catalog configuration.")
        self.logger.info("Scraping departments %s" % ", ".join([x[0] for x in departments]))

        for department_name, department_url in departments:
            self.logger.info("Scraping department %s, URL %s" % (department_name, department_url))
            department_items = self.scrape_paginated_catalog(department_url, max_products=product_limit_per_department,
                                                             review_limit=review_limit, sort_by_newest=sort_by_newest)
            yield department_items

    def scrape_paginated_catalog(self, url, max_products=math.inf, review_limit=math.inf, sort_by_newest=True):
        """
        Scrapes a catalog or department. Since both have a similar structure, it can be used for any of the two.
        This is yet another method that wraps scrape_item, which is the most granular form of scraping apart from reviews,
        which are itself a part of scrape_item.
        :param url: The URL of the catalog.
        :param max_products: The maximum amount of products to scrape from that specific catalog.
        :param review_limit: The maximum amount of review pages to scrape from the product (if it has reviews).
        :param sort_by_newest: Whether to sort products by newest or most relevant.
        :return: A list of items belonging to the catalog along with their reviews.
        """
        self.logger.info("Scraping %s for catalog %s\n" % (
            "all items" if max_products == math.inf else "%s items" % max_products, url))

        parsed_count = 0

        if sort_by_newest:
            non_sorted_page_source = self.retrieve_source_from_url(url)
            current_page = GearbestParser.retrieve_catalog_sort_by_new_url(non_sorted_page_source, 'html.parser')
        else:
            current_page = url

        while current_page and parsed_count < max_products:
            page_content = self.retrieve_source_from_url(current_page)
            self.logger.info("Retrieving items from page %s" % current_page)

            item_ids_and_urls = None
            try:
                item_ids_and_urls = GearbestParser.parse_catalog_content(page_content, 'html.parser')
            except Exception as err:
                self.logger.error(str(err) + " -- Error with: %s" % url)
                yield None

            if not item_ids_and_urls:
                yield None
                raise ParsingError("Invalid catalog site.")

            for item_id, url in item_ids_and_urls:
                if max_products < parsed_count:
                    break
                product = self.scrape_item(url, review_limit=review_limit)
                if product:
                    parsed_count += 1

                yield product

            next_page = GearbestParser.retrieve_next_page(page_content, 'html.parser')
            current_page = next_page

    def retrieve_items_from_catalog_page(self, url):
        """
        Function that retrieves source content for a catalog page and parses it using GearbestParser. In this case,
        the source content is a list of all item URLs belonging to the catalog in the given static resource along with their IDs.
        :param url: The URL of the catalog to retrieve the page source from.
        :return: A list of item URLs and their IDs.
        """
        self.logger.info("Scraping catalog from %s" % url)
        catalog_content = self.retrieve_source_from_url(url)
        return GearbestParser.parse_catalog_content(catalog_content, 'html.parser')

    def scrape_item(self, url, scrape_reviews=True, review_limit=math.inf):
        """
        Scrapes an item from the given URL along with its reviews which by default is enabled up to as many pages as review_limit denotes.
        :param url: The URL of the item resource.
        :param scrape_reviews: A condition on whether to scrape reviews or not.
        :param review_limit: The maximum amount of review pages to scrape from the item.
        :return:
        """
        self.logger.info("Scraping product from %s" % url)
        try:
            item_content = self.retrieve_source_from_url(url)
            item_data = GearbestParser.parse_item(item_content, 'html.parser')
            self.logger.debug(item_data)
        except Exception as err:
            self.logger.error(err)
            return None
        if scrape_reviews:
            try:
                hover_element = self.driver.find_element_by_xpath(SORTING_OPTIONS_XPATH)
                sorting_element = self.driver.find_element_by_xpath(REVIEW_MOST_RECENT_XPATH)
                hover_and_click = ActionChains(self.driver).move_to_element(hover_element).move_to_element(
                    sorting_element).click(sorting_element)
                hover_and_click.perform()
                item_content = self.driver.page_source
                reviews = self.scrape_paginated_reviews_from_item(item_content, review_limit=review_limit,
                                                                  item_id=item_data["item_id"])
                if reviews:
                    item_data["reviews"] = reviews
            except WebDriverException as err:
                self.logger.error(err)
        return item_data

    def retrieve_source_from_url(self, url):
        """
        Method that wraps around a selenium webdriver in order to retrieve the page source from a given URL.
        :param url: The URL to retrieve the page source from.
        :return: The given page source content that was retrieved from the URL.
        """
        try:
            self.driver.get(url)
        except TimeoutException as e:
            self.logger.error(e.msg)
            return None

        content = self.driver.page_source

        if not content:
            self.logger.error("Content could not be retrieved.")
            return None

        return content

    def scrape_reviews_from_item(self, content=None, url=None):
        """
        Method that takes care of scraping the reviews from a given item. If there's no content as a parameter, the item page
        source will be loaded by the webdriver. If there's neither content nor a url to use, then None is returned.
        :param content: The content of a page source if it's given.
        :param url: The URL of an item if it's given.
        :return: A list containing all the reviews of an item for the given page source.
        """
        if not content:
            if url:
                content = self.retrieve_source_from_url(url)
            else:
                return None

        return GearbestParser.retrieve_reviews_from_item(content)

    def scrape_paginated_reviews_from_item(self, content=None, url=None, review_limit=math.inf, item_id=None):
        """
        Wrapper function that scrapes paginated reviews from the item. It scrapes as many as review_limit defines, if the
        page source is None, it will retrieve it from the URL if it exists, if none exist, None is returned.
        The reviews will be filtered according to whether they've been scraped before or not.
        :param content: The content of the page source of the site.
        :param url: The URL of the site in case the content is None.
        :param review_limit: The maximum amount of review pages to scrape for the item.
        :param item_id: The ID of the item in order to get the last review and avoid re-scraping.
        :return: A list containing all reviews of the given item .
        """
        if not content:
            if url:
                raw_content = self.retrieve_source_from_url(url)
                try:
                    self.driver.find_element_by_xpath(REVIEW_MOST_RECENT_XPATH).click()
                    content = self.driver.page_source
                except WebDriverException:
                    content = raw_content
            else:
                return None

        all_reviews = []
        review_count = 0
        last_seen_timestamp = self.retrieve_last_seen_timestamp(item_id)

        while review_count < review_limit:
            page_reviews = GearbestParser.retrieve_reviews_from_item(content)

            if page_reviews:
                if last_seen_timestamp:
                    new_reviews = self._retrieve_review_deltas(page_reviews, last_seen_timestamp)
                    if len(new_reviews) == 0:
                        return all_reviews
                    all_reviews.extend(new_reviews)
                else:
                    all_reviews.extend(page_reviews)
            else:
                return all_reviews

            next_page_element = GearbestParser.retrieve_new_review_page_element(content)

            if not next_page_element:
                return all_reviews
            try:
                self.driver.find_element_by_xpath(REVIEW_NEXT_XPATH).click()
            except WebDriverException:
                return all_reviews
            content = self.driver.page_source
            review_count += 1
        return all_reviews

    def retrieve_last_seen_timestamp(self, item_id):
        """
        Retrieves the last seen timestamp for that specific item id.
        :param item_id: The item id in question.
        :return: A datetime that represents the last seen review.
        """
        max_timestamp_query = "SELECT max(post_timestamp) as max_timestamp FROM reviews WHERE item_id = %s"
        with GearbestMySQLManager(DATABASE_NAME) as sql_mgr:
            cur = sql_mgr.execute_selection_query(max_timestamp_query, [item_id])
            res = cur.fetchone().get("max_timestamp")
            return res if res else None

    def _retrieve_review_deltas(self, reviews, last_seen_timestamp):
        return [page_review for page_review in reviews if page_review["post_timestamp"] > last_seen_timestamp]
