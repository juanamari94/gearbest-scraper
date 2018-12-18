"""
Author: Juan Amari, François Oren Chikli
File that contains all table creation and connection data for the database.
"""

MYSQL_USER = "root"
MYSQL_PASSWORD = "root"
MYSQL_HOST = '127.0.0.1'

DB_NAME = "gearbest"

# Dictionary that will contain all tables.
TABLES = dict()

TABLES['main_categories'] = """
CREATE TABLE IF NOT EXISTS `main_categories` (
`id` int NOT NULL AUTO_INCREMENT,
`category_id` varchar(50) NOT NULL UNIQUE,
`category_name` varchar(100) NOT NULL,
`category_url` varchar(200) NOT NULL,
PRIMARY KEY (`id`)
) ENGINE=InnoDB
"""

TABLES['middle_categories'] = """
CREATE TABLE IF NOT EXISTS `middle_categories` (
`id` int NOT NULL AUTO_INCREMENT,
`category_id` varchar(50) NOT NULL UNIQUE,
`category_name` varchar(100) NOT NULL,
`category_url` varchar(200) NOT NULL,
`parent_category_id` varchar(50) NOT NULL,
PRIMARY KEY (`id`),
FOREIGN KEY (`parent_category_id`) REFERENCES main_categories(`category_id`)
) ENGINE=InnoDB
"""

TABLES['granular_categories'] = """
CREATE TABLE IF NOT EXISTS `granular_categories` (
`id` int NOT NULL AUTO_INCREMENT,
`category_id` varchar(50) NOT NULL UNIQUE,
`category_name` varchar(100) NOT NULL,
`category_url` varchar(200) NOT NULL,
`parent_category_id` varchar(50),
PRIMARY KEY (`id`),
FOREIGN KEY (`parent_category_id`) REFERENCES middle_categories(`category_id`)
) ENGINE=InnoDB
"""

TABLES['items'] = """
CREATE TABLE IF NOT EXISTS `items` (
`id` int NOT NULL AUTO_INCREMENT,
`item_id` varchar(50) NOT NULL UNIQUE,
`item_name` varchar(200) NOT NULL,
`item_url` varchar(200) NOT NULL,
`timestamp` datetime NOT NULL,
`granular_cat_id` varchar(50) NOT NULL,
`item_description` text,
`item_brand` varchar(50),
`item_rating` float,
`customer_reviews_count` int,
`customer_answer_count` int,
PRIMARY KEY (`id`),
FOREIGN KEY (`granular_cat_id`) REFERENCES granular_categories(`category_id`)
) ENGINE=InnoDB;
"""

TABLES['prices'] = """
CREATE TABLE IF NOT EXISTS `prices` (
`price_id` int NOT NULL AUTO_INCREMENT,
`price` double NOT NULL,
`currency_type` varchar(10) NOT NULL,
`scrape_timestamp` datetime,
`discount_percentage` float,
`item_id` varchar(50) NOT NULL,
PRIMARY KEY (`price_id`),
FOREIGN KEY (`item_id`) REFERENCES items(`item_id`)
) ENGINE=InnoDB
"""

TABLES['item_to_cat'] = """
CREATE TABLE IF NOT EXISTS `item_to_cat` (
`id` int NOT NULL AUTO_INCREMENT,
`item_id` varchar(50) NOT NULL,
`category_id` varchar(50) NOT NULL,
PRIMARY KEY(`id`),
UNIQUE KEY(`item_id`, `category_id`),
FOREIGN KEY (`item_id`) REFERENCES items(`item_id`),
FOREIGN KEY (`category_id`) REFERENCES granular_categories(`category_id`)
) ENGINE=InnoDB
"""

TABLES['reviews'] = """
CREATE TABLE IF NOT EXISTS `reviews` (
`id` int NOT NULL AUTO_INCREMENT,
`user_id` int NOT NULL,
`user_name` varchar(100),
`review_title` varchar(300),
`review_rating` int,
`review_attributes` varchar(200),
`review_text` text,
`post_timestamp` datetime,
`item_id` varchar(50) NOT NULL,
PRIMARY KEY (`id`),
FOREIGN KEY (`item_id`) REFERENCES items(`item_id`)
) ENGINE=InnoDB
"""
