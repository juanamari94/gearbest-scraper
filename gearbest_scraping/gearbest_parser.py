"""
Authors: Juan Amari, François Oren Chikli
Main file for the parsing class for Gearbeast.
"""
import datetime
import logging
import re

from bs4 import BeautifulSoup

from gearbest_scraping.errors.parsing_error import ParsingError

DIGIT_PATTERN = "[^0-9]"
PAGE_PATTERN = ".+/[0-9].+\?.*"
ID_PATTERN = "(pp|c)_.+?[/|.]"
PAGE_START_INDEX = 2
CATEGORY_HIERARCHY = ["main_category", "middle_category", "granular_category"]
REVIEW_DATE_FORMAT_BASIC = '%b %d,%Y'
REVIEW_DATE_FORMAT_COMPLEX = '%b %d,%Y %H:%M:%S'

logger = logging.getLogger("GearbestLogger")


class GearbestParser:
    """
    Class for the Gearbest Parser. Takes the responsibility of parsing content once static.
    """

    DEFAULT_CURRENCY = "$"

    @staticmethod
    def parse_price(input_price, default_locale=DEFAULT_CURRENCY):
        """
        Parses a given string that contains both a floating point number representing the price and a currency type.
        :param input_price: The given string.
        :param default_locale: In case there's a problem parsing the price.
        :return: A tuple containing the price and the currency type.
        """
        price = ""
        currency = ""
        for char in input_price:
            if char == "." or char.isdigit():
                price += char
            else:
                currency += char
        if not currency:
            logger.debug("No currency found for this price, defaulting to USD.")
            currency = default_locale
        return price, currency

    @staticmethod
    def parse_departments(department_content, parser='html.parser'):
        """
        Parses all departments from the given source content.
        :param department_content: The source content that contains the departments or catalogs.
        :param parser: The type of parser to use.
        :return: A list of tuples containing the department names and their URLs.
        """
        soup = BeautifulSoup(department_content, parser)
        department_div = soup.find('ul', {'class': 'headerCate_itemBox'})

        if not department_div:
            return None

        departments = department_div.find_all('li', {'class': 'headerCate_item'})
        department_names_and_urls = []
        for department in departments:
            department_a_tag = department.find('a')
            if not department_a_tag:
                continue
            department_url = department_a_tag.get('href')
            department_name = department_a_tag.get('title')
            if department_name not in ["Fashion", "Top Brands"]:
                department_names_and_urls.append((department_name, department_url))

        return department_names_and_urls

    @staticmethod
    def _parse_basic_element(element, parsing_func, item_dict, key_name):
        """
        Wrapper function for elements with simple parsing requirements. It mutates a given dictionary.
        :param element: Element from BeautifulSoup.
        :param parsing_func: The function that handles the parsing.
        :param item_dict: Reference to the dictionary that will be mutated in accordance to the given key_name.
        :param key_name: Key to use for the element in the given dictionary that will be mutated.
        """
        if element:
            element_data = parsing_func(element)
            item_dict[key_name] = element_data

    @staticmethod
    def _parse_item_url(element, item_dict):
        """
        Wrapper function for the item_url element of Gearbest products. Mutates a given dictionary with the key.
        :param element: The element to parse.
        :param item_dict: The dictionary to mutate.
        """
        if element:
            item_url = element.get('href')
            item_dict["item_url"] = item_url
            item_dict["item_id"] = re.search(ID_PATTERN, item_url).group().rstrip(".")

    @staticmethod
    def _parse_categories(categories, item_dict):
        """
        Parses the category elements from a given list full of those elements. Mutates a dictionary accordingly, using
        a pre-defined category hierarchy for the element names.
        :param categories: Category elements from a given list. Most products have more than one category.
        :param item_dict: The dictionary to mutate with the given categories.
        """
        if categories:
            # We get the the categories and get their name, ID and URL.
            for key_name, tag in zip(CATEGORY_HIERARCHY, categories):
                href = tag.get('href')
                item_dict[key_name + "_id"] = re.search(ID_PATTERN, href).group().strip("/")
                category_name = tag.find('span')
                if category_name:
                    category_name_text = category_name.get_text().strip().replace("\\", "")
                    item_dict[key_name + "_name"] = category_name_text
                    item_dict[key_name + "_url"] = href

    @staticmethod
    def _parse_price_element(price, item_dict):
        """
        Parses the price of a price element from a Gearbest product and mutates a dictionary with the given values.
        Retrieves the currency type and the price as a float value.
        :param price: The price element.
        :param item_dict: The dictionary to mutate.
        """
        if price:
            price_data = price.get_text().replace("\n", "").strip()
            item_price, item_currency = GearbestParser.parse_price(price_data)
            item_dict["price"] = float(item_price)
            item_dict["currency_type"] = item_currency

    @staticmethod
    def parse_item(item_content, parser='html.parser'):
        """
        Parses the content of an item in order to retrieve meaningful data, in this case a timestamp, the item IDs, the price,
        whether it has a discount, the URL, the categories it belongs to, the description, the brand, the title, the rating,
        how many reviews it has, how many ratings it has, etcetera.
        :param item_content: The page source content for the file.
        :param parser: The parser to use with BeautifulSoup, which by default is "html.parser".
        :return: A dictionary containing as keys the title of the data we desire, and the data itself as its values.
        """
        item_soup = BeautifulSoup(item_content, parser)
        item = {}

        item_data = item_soup.find('div', {"class": "goodsIntro_infoWrap"})
        if not item_data:
            return None

        timestamp = datetime.datetime.now()
        item["timestamp"] = timestamp

        # Scraped data
        name = item_data.find('h1', {'class': 'goodsIntro_title'})
        GearbestParser._parse_basic_element(name, lambda x: x.get_text().strip().replace("\n", ""), item, "item_name")

        item_url_tag = item_soup.find('link', {'rel': 'canonical'})
        GearbestParser._parse_item_url(item_url_tag, item)

        categories = item_soup.find_all('a', {'class': 'cGoodsCrumb_itemLink', 'itemprop': 'item'})
        GearbestParser._parse_categories(categories, item)

        description = item_data.find('div', {'class': 'goodsIntro_summary'})
        GearbestParser._parse_basic_element(description, lambda x: x.get_text(), item, "description")

        brand = item_data.find('label', {'class': 'goodsIntro_brand'})
        GearbestParser._parse_basic_element(brand, lambda x: x.get_text()
                                            .replace("Brand:\n", "")
                                            .replace("\n", "")
                                            .rstrip()
                                            .strip(),
                                            item,
                                            "brand")

        rating = item_data.find('span', {'class': 'gbStarGrade_count'})
        GearbestParser._parse_basic_element(rating,
                                            lambda x: x.get_text().replace("\n", "").rstrip().strip(),
                                            item,
                                            "rating")

        customer_reviews_count = item_data.find('a', {'class': 'goodsIntro_reviews'})
        GearbestParser._parse_basic_element(customer_reviews_count,
                                            lambda x: re.sub(DIGIT_PATTERN, "", x.get_text()),
                                            item,
                                            "customer_reviews_count")

        customer_answer_count = item_data.find('a', {'class': 'goodsIntro_faq'})
        GearbestParser._parse_basic_element(customer_answer_count,
                                            lambda x: re.sub(DIGIT_PATTERN, "", x.get_text()),
                                            item,
                                            "customer_answer_count")

        price = item_data.find('span', {'class': 'goodsIntro_price'})
        GearbestParser._parse_price_element(price, item)

        discount = item_data.find('span', {'class': 'goodsIntro_priceDiscount'})
        GearbestParser._parse_basic_element(discount,
                                            lambda x: re.sub(DIGIT_PATTERN, "", x.get_text()),
                                            item,
                                            "discount")

        return item

    @staticmethod
    def parse_catalog_content(content, parser='html.parser'):
        """
        Parses the content of the catalog of a given category and returns the IDs and URLs of all the products belong to that catalog in that specific page.
        :param content: The static content to parse.
        :param parser: Parsing method, usually 'html.parser'
        :param url: The URL of the category.
        :return: Returns the Item IDs and URLs of each item in the catalog for a specific page, if there is one.
        """

        soup = BeautifulSoup(content, parser)
        unordered_list = soup.find('ul', {'class': 'js_seachResultList'})
        if not unordered_list:
            unordered_list = soup.find('ul', {'class': 'brandList_content'})
        list_items = unordered_list.find_all('li', {"class": "gbGoodsItem"})

        item_urls = [list_item.find('a').get('href') for list_item in list_items]
        item_ids = [item_url[item_url.rfind("/") + 1:item_url.rfind(".")] for item_url in item_urls]
        item_ids_and_urls = list(zip(item_ids, item_urls))

        return item_ids_and_urls

    @staticmethod
    def retrieve_next_page(content, parser='html.parser'):
        """
        Parses the pages in a catalog in order to return the following link. If there's no following link to the next page, returns None.
        :param content: The static content to parse.
        :param parser: Parsing method, usually 'html.parser'
        :return: The link to the following page if it exists, otherwise None.
        """
        soup = BeautifulSoup(content, parser)
        next_page_div = soup.find("div", {"class": "cateMain_pages"})
        next_page = next_page_div.find("a", {"class": "pageNext"})
        are_valid_attrs = "disable" not in next_page.attrs["class"]
        if are_valid_attrs:
            return next_page.get("href")
        return None

    @staticmethod
    def retrieve_catalog_sort_by_new_url(content, parser='html.parser'):
        """
        Retrieves the URL for the sorted by newest elements in catalog pages.
        :param content: The content to parse.
        :param parser: The parser to use.
        :return:
        """
        soup = BeautifulSoup(content, parser)
        sort_item_box = soup.find('p', {'class': 'js-SortItemBox'})
        if not sort_item_box:
            raise ParsingError("Invalid catalog site.")
        sorting_links = sort_item_box.find_all('a', {'class': 'js-orderItem'})
        for link in sorting_links:
            text = link.get_text()
            if text and "New" in text:
                return link.get('href')
        return None

    @staticmethod
    def retrieve_new_review_page_element(content, parser='html.parser'):
        """
        Method that parses a JavaScript-generated element that contains the link or action in this case for the next
        given page if it exists, otherwise it returns None. In this case the pages are created by AJAX requests,
        which means that the source changes slightly but it's not a full change. The parser does not know about this though,
        the scraper does.
        :param content: The source content of a given page.
        :param parser: The parser to use with BeautifulSoup which by default is "html.parser".
        :return: The element that contains the next page action if it exists, otherwise None.
        """
        soup = BeautifulSoup(content, parser)
        review_page_div = soup.find('div', {'class': 'goodsReviews_pageWrap'})
        if not review_page_div:
            return None
        next_page_div = review_page_div.find('div', {'class': 'gbPaging'})
        if not next_page_div:
            return None
        next_page_button = next_page_div.find('a', {'data-goto': 'next'})
        if "disabled" in next_page_button.attrs["class"]:
            return None
        return next_page_button

    @staticmethod
    def retrieve_reviews_from_item(content, parser='html.parser'):
        """
        Parses the source in order to retrieve all reviews present in the static piece of content.
        :param content: The static source content from the page.
        :param parser: The parser to use with BeautifulSoup, which by default is "html.parser".
        :return: A list of reviews for the item for which the content was provided.
        """
        soup = BeautifulSoup(content, parser)
        reviews_div = soup.find('div', {'id': 'js-reviewWrap'})

        if not reviews_div:
            return None

        item_url_tag = soup.find('link', {'rel': 'canonical'})
        item_id = None
        if item_url_tag:
            item_url = item_url_tag.get('href')
            item_id = re.search(ID_PATTERN, item_url).group().rstrip(".")

        reviews_list_elements = soup.find_all('li', {'class': 'goodsReviews_item'})

        if not reviews_list_elements:
            return None

        reviews = []
        for review in reviews_list_elements:
            review_dict = {}
            user_name_and_id = GearbestParser.retrieve_username_and_id_from_review(review)

            if user_name_and_id:
                review_dict.update(user_name_and_id)

            review_data = GearbestParser.retrieve_review_data_from_review(review)
            if review_data:
                review_dict.update(review_data)

            if review_dict:
                review_dict['item_id'] = item_id
                reviews.append(review_dict)
        return reviews

    @staticmethod
    def retrieve_username_and_id_from_review(review):
        """
        Helper method that gets the user name and ID from a review, given that the review element itself is quite big.
        :param review: The Tag element that contains a specific review.
        :return: A dictionary that contains the user name and the ID as keys and its corresponding values.
        """
        user_name_tag = review.find('strong', {'class': 'goodsReviews_itemUserName'})
        user_name_id = review.get('data-review-id')
        if not user_name_tag or not user_name_id:
            return None
        return {'user_name': user_name_tag.get_text(), 'user_id': user_name_id}

    @staticmethod
    def retrieve_review_data_from_review(review):
        """
        Retrieves the main review data such as the title, rating, attributes, text, and time tag.
        :param review: The review element from which to parse this specific data.
        :return: A dictionary that contains the aforementioned datum.
        """
        title_tag = review.find('strong', {'class': 'goodsReviews_itemTitleText'})
        title = None
        if title_tag:
            title = title_tag.get_text()

        title_rating = GearbestParser.parse_user_rating(review)

        review_attributes = None
        review_attributes_tag = review.find('span', {'class': 'goodsReviews_itemAttrEach'})
        if review_attributes_tag:
            review_attributes = review_attributes_tag.get_text()

        review_texts = review.find_all('dl', {'class': 'goodsReviews_itemCont'})
        review_text = ""
        for element in review_texts:
            element_title = element.find('dt')
            if element_title:
                review_text += "\n" + element_title.get_text()
            text = element.find('dd')
            if text:
                review_text += "\n" + text.get_text()

        time = None
        time_tag = review.find('p', {'class': 'goodsReviews_itemTime'})
        if time_tag:
            time_text = time_tag.get_text().strip()
            try:
                time = datetime.datetime.strptime(time_text, REVIEW_DATE_FORMAT_BASIC)
            except ValueError:
                time = datetime.datetime.strptime(time_text, REVIEW_DATE_FORMAT_COMPLEX)
            except Exception:
                time = None

        return {'review_title': title, 'review_rating': title_rating, 'review_attributes': review_attributes,
                'review_text': review_text, 'post_timestamp': time}

    @staticmethod
    def parse_user_rating(review):
        """
        Retrieves the user rating from a given review element.
        :param review: The tag element for the review.
        :return: The rating as a number, or None if the element doesn't exist.
        """
        review_star = review.find('i', {'class': 'rating_full'})
        if review_star:
            return review_star.get('data-index')
        return None
