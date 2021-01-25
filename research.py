from bs4 import BeautifulSoup
import requests


class Item:
    def __init__(self, item_id, title, price, town, city, date):
        self.item_id = item_id
        self.title = title
        self.price = price
        self.town = town
        self.city = city
        self.date = date

    def __key(self):
        return self.item_id

    def __str__(self):
        return (
            f"{self.title}\nPrice: {self.price}\n{self.town}{self.city} - {self.date}\n"
        )

    def __eq__(self, other):
        if isinstance(other, Item):
            return self.__key() == other.__key()

        return False

    def __hash__(self):
        return hash(self.__key())


class Research:
    def __init__(self, url):
        self.url = url
        self.items_list = []
        self.name = None

    def __str__(self):
        return f"\n{self.name}\n{self.url}\n"

    def change_name(self, name):
        self.name = name

    def get_page_html(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        }
        page = requests.get(url, headers=headers)
        return page.content

    def get_items_on_sale(self):
        items_list = []
        i = 1

        while True:
            url = self.url + f"&o={i}"
            i += 1

            page_html = self.get_page_html(url)
            soup = BeautifulSoup(page_html, "html.parser")

            # item_key_data = soup.findAll(
            #     "div", {"class": "jsx-3924372161 item-key-data"}
            # )

            links = soup.findAll("a", {"class": "jsx-3924372161 link"})

            # if len(item_key_data) == 0:
            if len(links) == 0:
                break

            # for item in item_key_data:
            for item in links:
                # Get the ad ID from the href
                href = item["href"]
                item_page_html = self.get_page_html(href)
                item_soup = BeautifulSoup(item_page_html, "html.parser")

                item_id = item_soup.find(
                    "p",
                    {
                        "class": "classes_sbt-text-atom__2GBat classes_token-caption__1Ofu6 size-normal classes_weight-book__3zPi1"
                    },
                )
                title = item.find(
                    "h2",
                    {
                        "class": "classes_sbt-text-atom__2GBat classes_token-h6__1ZJNe size-normal classes_weight-semibold__1RkLc jsx-3045029806 item-title jsx-3924372161"
                    },
                )
                price = item.find("h6", {"class": "classes_price__HmHqw"})
                town = item.find("span", {"class": "classes_town__W-0Iq"})
                city = item.find("span", {"class": "city"})
                date = item.find("span", {"class": "classes_date__2lOoE"})

                if date is not None:
                    new_item = Item(
                        item_id.getText(),
                        title.getText(),
                        price.getText(),
                        town.getText(),
                        city.getText(),
                        date.getText(),
                    )
                    items_list.append(new_item)

        self.items_list = items_list

        print(f"{self.name} {str(len(self.items_list))} results")
