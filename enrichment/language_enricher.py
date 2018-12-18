"""
Authors: Juan Amari, François Oren Chikli
Enrichment API class file.
"""

import requests

import enrichment.language_enricher_secrets as secrets
from enrichment.errors.enrichment_error import EnrichmentError
from enrichment.errors.quota_error import QuotaError

MAX_CHARS_DEFAULT = 100

QUOTA_EXCEEDED_ERROR = 104


class LanguageEnricher:
    DEFAULT_TEMPLATE = "{}?access_key={}&query={}"

    def __init__(self, url=secrets.BASE_API_URL, api_key=secrets.API_KEY):
        self.url = url
        self.api_key = api_key

    def get_language(self, input_string, max_chars=MAX_CHARS_DEFAULT):
        """
        Retrieves the language from the given API.
        :param input_string: The input string to retrieve the language from.
        :param max_chars: Maximum amount of characters to send to the API.
        :return: The language if it has a meaningful probability.
        """
        parsed_string = input_string[:max_chars]
        assembled_url = self.assemble_url(parsed_string)
        response = requests.get(assembled_url).json()
        first_result_index = 0
        if response["success"]:
            if response["results"]:
                language_name = response["results"][first_result_index]["language_name"]
                confidence_percentage = response["results"][first_result_index]["percentage"]
                return dict(language_name=language_name, confidence_percentage=confidence_percentage)
        elif response.get("error") and response["error"]["code"] == QUOTA_EXCEEDED_ERROR:
            raise QuotaError("Quota has been exceeded: {}".format(str(response)))
        else:
            raise EnrichmentError("There was an error with this request: {}".format(str(response)))

    def assemble_url(self, parsed_string):
        """
        Assembles a URL from the base url, access key and the string.
        :param parsed_string: The string to query for.
        :return: The URL to query.
        """
        return LanguageEnricher.DEFAULT_TEMPLATE.format(self.url, self.api_key, parsed_string)
