import os
import requests
import json

import textwrap

from dotenv import load_dotenv

load_dotenv()


class ArticleExtractor:
    def __init__(self):
        self.api_key = os.getenv("ARTICLE_EXTRACTOR_API_KEY")

    @staticmethod
    def truncate(string, length):
        if length >= len(string):
            return string
        else:
            return textwrap.shorten(string, width=length, placeholder="")

    def extract_articles(self, urls: list) -> list:
        return_data = []
        if len(urls) == 0:
            return return_data
        for url in urls:
            url = f"https://api.articlextractor.com/v1/extract?url={url}&language=en&api_token={self.api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                res_dict = json.loads(response.text)["data"]
                if res_dict["title"] != "" and res_dict["text"] != "":
                    return_data.append(
                        {
                            "title": res_dict["title"],
                            "content": self.truncate(
                                "".join(res_dict["text"]), 10000
                            ),
                        }
                    )
            else:
                raise Exception(
                    f"Error fetching data from ArticleExtractor API: {response.text}"
                )

        return return_data
