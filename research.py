from bs4 import BeautifulSoup
import requests


class Research:
    def __init__(self, url):
        self.url = url
        self.items_price_list = None
        self.name = None

    def change_name(self, name):
        self.name = name

    def get_page_html(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        }
        page = requests.get(url, headers=headers)
        print(page.status_code)
        return page.content

    def get_items_on_sale(self):
        page_html = self.get_page_html(self.url)
        soup = BeautifulSoup(page_html, "html.parser")
        items_on_sale = []
        items_price = []
        for el in soup.findAll(
            "h2",
            {
                "class": "classes_sbt-text-atom__2GBat classes_token-h6__1ZJNe size-normal classes_weight-semibold__1RkLc jsx-3045029806 item-title jsx-3924372161"
            },
        ):
            items_on_sale.append(el.getText())

        for el in soup.findAll(
            "h6",
            {
                "class": "classes_sbt-text-atom__2GBat classes_token-h6__1ZJNe size-normal classes_weight-semibold__1RkLc classes_price__HmHqw"
            },
        ):
            items_price.append(el.getText())

        items_price_list = list(zip(items_on_sale, items_price))

        self.items_price_list = items_price_list

    def print_research(self):
        text = f"\nName: {self.name}\n"
        text += f"URL: {self.url}\n"
        # for item in self.items_price_list:
        #     text += f"Item: {item[0]}\nPrice: {item[1]}\n\n"

        return text