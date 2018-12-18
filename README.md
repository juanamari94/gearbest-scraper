# gearbest-scraper

## What is it?

It's a scraper for the online department store [GearBest][https://www.gearbest.com/], it scrapes the full site and stores it into a database, it also enriches the data by getting the language of the item reviews.

## Main features

* Lazy evaluation through Python generators.
* Automation with selenium for the scraping of complex JavaScript-generated elements.
* A database layout.
* Code to consume the `LanguageLayer` API.
* Some (but not many at all) unit tests.
* A ridiculous amount of regular expressions.

## What does it scrape?

It scrapes the category hierarchy for each department and its sub-departments, as well as the price, discount, currency, title, description, and as many reviews as possible for as many products as specified in the parameters.
