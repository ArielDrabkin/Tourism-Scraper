import grequests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import logging
import json
import csv

UA = UserAgent()

# Load config data
with open("config.json", "r") as config_file:
    config_data = json.load(config_file)

# Constants
BASE_URL = config_data["urls"]["base_url_tripadvisor"]
LOG_FORMAT = config_data["logger_format_string"]
NUM_ATTRACTIONS = 30
TIMEOUT = 5

# Initialize a logger object
logger = logging.getLogger("scrape-log")


def get_next_page_arrow(soup):
    """
    Take a BeautifulSoup soup object from a trip advisor page as input.
    return the element of a BeautifulSoup soup object of the arrow.
    """
    logger.info("Beginning to find next page arrow element")
    try:
        arrow_elements = soup.find_all("div", class_="UCacc")  # there are 2 arrows, 1 for prev_page, 1 for next_page
    except Exception as e:
        logger.error(f"Couldn't find next page arrows from soup. Error: {e}")
        raise Exception(e)

    next_page_arrow = None  # if code finds next page then it will be defined.
    if arrow_elements:
        # find the next page
        for element in arrow_elements:
            if element.a["aria-label"] == "Next page":
                next_page_arrow = element
                logger.info("Found next-page icon.")
    else:
        logger.info("Failed to get next page soup.")
        return next_page_arrow  # None

    return next_page_arrow


def get_next_page_soup(soup):
    """
    from the BeautifulSoup soup object of one tripadvisor page,
    get a new soup object for the next page
    If there is an issue getting the soup, return None.
    """
    logger.info("Trying to get next page soup.")
    try:
        next_page_arrow = get_next_page_arrow(soup)  # will either return soup element, None or an Exception :)
    except Exception as e:
        raise Exception("Couldn't get next page element.", e)

    if next_page_arrow:  # if function couldn't get the next page arrow element
        next_page_url = BASE_URL + next_page_arrow.a["href"]
        logger.debug(f"url of next_page: {next_page_url}")

        headers = {"User-Agent": UA.random}

        # Make requests until successful
        while True:
            logger.info("requesting...")
            req = grequests.get(next_page_url, headers=headers, timeout=TIMEOUT).send()
            next_page_response = grequests.map([req])[0]
            if next_page_response is not None and next_page_response.status_code == 200:
                break

        next_page_html = next_page_response.text

        logger.info("Got next page html code.")

        next_page_soup = BeautifulSoup(next_page_html, features="html.parser")
        if next_page_soup is not None:
            logger.info("Successfully got next page soup.")
        else:
            logger.info("Failed to get next page soup.")
            return None

    else:
        logger.info("Failed to get next page soup.")
        return None

    return next_page_soup


def get_links_from_page(soup):
    """
    from a single page on tripadvisor.com, get the ~30 urls to attractions.
    :param soup: a BeautifulSoup object
    :return: a list of ~30 urls.
    """
    logger.info("Trying to get links from page")
    urls = list()
    titles = soup.find_all("div", class_="alPVI eNNhq PgLKC tnGGX")
    for i, title in enumerate(titles):
        urls.append("https://www.tripadvisor.com/" + title.a["href"])

    logger.debug(f"Got {len(urls)} more urls.")
    logger.info("Finished gathering urls from page.")
    return urls


def get_all_top_links(url, NUM_ATTRACTIONS):
    """
    Take the "homepage" of top attractions in Paris, and traverse the specified number of attractions in NUM_ATTRACTIONS
    to get a url for each of them.
    :param url:
    :NUM_ATTRACTIONS:
    :return: all_urls: a list of urls.
    """
    logger.info("Started from main page, looking for all top links.")
    headers = {"User-Agent": UA.random}

    # Make requests until successful
    while True:
        logger.info("requesting...")
        req = grequests.get(url, headers=headers, timeout=TIMEOUT).send()
        response = grequests.map([req])[0]
        if response is not None and response.status_code == 200:
            break

    html_front_page = response.text

    front_page_soup = BeautifulSoup(html_front_page, features="html.parser")

    top_attractions_urls = list()
    count = 0
    while True:  # while there are more pages to gather urls from
        count += 1
        logger.debug(f"Page #: {count}.")

        urls = get_links_from_page(front_page_soup)
        top_attractions_urls.extend(urls)
        logger.info(f"Now have {len(top_attractions_urls)} urls.")

        if len(top_attractions_urls) >= NUM_ATTRACTIONS:
            break

        try:
            logger.info(f"Trying to get next page after: {count+1}.")
            front_page_soup = get_next_page_soup(front_page_soup)  # redefine the new "front-page" as the next page.
            if front_page_soup is None:
                logging.error("Couldn't get next page soup.")
                break

        except Exception as e:
            logger.error(f"Error while getting next page (page {count+1}) soup: {e}")
            break

    return top_attractions_urls


def main():
    # grab home-page url for each city.
    paris_top_to_do_url = config_data["urls"]["paris_top_url"]
    b_a_top_to_do_url = config_data["urls"]["buenos_aires_top_url"]
    washington_top_to_do_url = config_data["urls"]["washington_top_url"]
    seoul_top_to_do_url = config_data["urls"]["seoul_top_url"]
    cairo_top_to_do_url = config_data["urls"]["cairo_top_url"]

    # configure logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)
    handler = logging.FileHandler("tripadvisor.log")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    urls_paris = get_all_top_links(paris_top_to_do_url)
    with open("url_list.csv", "w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Num", "URL"])
        for i, url in enumerate(urls_paris, start=1):
            writer.writerow((i, url))

    urls_b_a = get_all_top_links(b_a_top_to_do_url)
    with open("url_list_ba.csv", "w") as b_a_csv:
        writer = csv.writer(b_a_csv)
        writer.writerow(["Num", "URL"])
        for i, url in enumerate(urls_b_a, start=1):
            writer.writerow((i, url))

    urls_cairo = get_all_top_links(cairo_top_to_do_url)
    with open("url_list_cairo.csv", "w") as cairo_csv:
        writer = csv.writer(cairo_csv)
        writer.writerow(("Num", "URL"))
        for i, url in enumerate(urls_cairo, start=1):
            writer.writerow((i, url))

    urls_wash = get_all_top_links(washington_top_to_do_url)
    with open("url_list_wash.csv", "w") as wash_csv:
        writer = csv.writer(wash_csv)
        writer.writerow(("Num", "URL"))
        for i, url in enumerate(urls_wash, start=1):
            writer.writerow((i, url))

    urls_seoul = get_all_top_links(seoul_top_to_do_url)
    with open("url_list_seoul.csv", "w") as seoul_csv:
        writer = csv.writer(seoul_csv)
        writer.writerow(("Num", "URL"))
        for i, url in enumerate(urls_seoul, start=1):
            writer.writerow((i, url))


if __name__ == '__main__':
    main()