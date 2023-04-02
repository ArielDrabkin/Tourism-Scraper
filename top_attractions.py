import grequests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import logging
import json

UA = UserAgent()

# load config data
with open("config.json", "r") as config_file:
    configs = json.load(config_file)

# define global vars
BASE_URL = configs["urls"]["base_url_tripadvisor"]
LOG_FORMAT = configs["logger_format_string"]
LOGGER_NAME = configs["logger_name"]
ARROW_CLASS = configs["soup_elements"]["arrow_class"]
TITLE_CLASS = configs["soup_elements"]["title_class"]
URL_CLASS = configs["soup_elements"]["url_class"]
NEXT_PAGE_LABEL = configs["soup_elements"]["next_page_label"]
ARROW_ERROR = configs["log_messages"]["arrow_error"]
SOUP_ERROR = configs["log_messages"]["soup_error"]
SOUP_SUCCESS = configs["log_messages"]["soup_success"]
GET_HTML_ERROR = configs["log_messages"]["html_error"]

NUM_ATTRACTIONS = 420
TIMEOUT = 5

# Initialize a logger object
logger = logging.getLogger(LOGGER_NAME)


def get_next_page_arrow(soup):
    """
    param: soup : a soup object of the beautifulsoup library.
        (The url from which it was generated is a Tripadvisor.com
        webpage with links to top attractions for a city.)
    return: next_page_arrow - the element of the webpage soup which directs you to the next page in the list.
    """
    try:
        arrow_elements = soup.find_all("div", class_=ARROW_CLASS)  # there are 2 arrows, 1 for prev_page, 1 for next_page
        if arrow_elements is None:
            return arrow_elements  # return None
    except Exception as e:
        logger.error(ARROW_ERROR + f" {e}")
        raise Exception(e)

    next_page_arrow = None  # if code finds next page then it will be defined.
    if arrow_elements:
        for element in arrow_elements:  # find the next page
            if element.a["aria-label"] == NEXT_PAGE_LABEL:  # this ensures we don't get the arrow for prev. pg. instead
                next_page_arrow = element
    else:
        logger.info(ARROW_ERROR)
        return next_page_arrow  # return None

    return next_page_arrow


def get_next_page_html(soup):
    """
    param : soup -a soup object of the beautifulsoup library from a tripadvisor webpage of top attractions.
    return : html code for the following page in the tripadvisor list of top attractions.
        (Returns None if there's an issue collecting the html.)
    """
    try:
        next_page_arrow = get_next_page_arrow(soup)  # will either return soup element, None or an Exception :)
    except Exception as e:
        raise Exception(ARROW_ERROR + f" {e}")

    if next_page_arrow:  # if function could get the next page arrow element
        next_page_url = BASE_URL + next_page_arrow.a[URL_CLASS]
        logger.debug(f"url of next_page: {next_page_url}")

        # Make requests until successful
        headers = {"User-Agent": UA.random}
        while True:
            req = grequests.get(next_page_url, headers=headers, timeout=TIMEOUT).send()
            next_page_response = grequests.map([req])[0]
            if next_page_response is not None and next_page_response.status_code == 200:
                break
        return next_page_response.text

    else:
        logger.debug(GET_HTML_ERROR)
        return None


def get_next_page_soup(soup):
    """
    param: soup - a soup object of the beautiful soup library from a webpage in tripadvisor
    return : next_page_soup - a soup object from the following webpage of tripadvisor.
    """
    try:
        next_page_html = get_next_page_html(soup)
        if next_page_html is None:
            raise Exception(GET_HTML_ERROR)
    except Exception as e:
        return None

    next_page_soup = BeautifulSoup(next_page_html, features="html.parser")
    if next_page_soup is not None:  # checking for the purposes of debug log.
        logger.debug(SOUP_SUCCESS)
    else:
        logger.debug(SOUP_ERROR)
        return None
    return next_page_soup


def get_links_from_page(soup):
    """
    :param: soup - a soup object fo the beautifulsoup library from a webpage of top attractions for a city.
    :return: a list of ~30 urls from the webpage.
    """
    urls = list()
    titles = soup.find_all("div", class_=TITLE_CLASS)
    for i, title in enumerate(titles):
        urls.append("https://www.tripadvisor.com/" + title.a["href"])

    logger.debug(f"Got {len(urls)} more urls.")
    logger.debug("Finished gathering urls from page.")
    return urls


def get_response_then_get_soup(url):
    """
    Param: url (str) a url from a ripadvisor webpage.
    Returns: a soup object of the BeautifulSoup library.
    
    [Motivation: Often, getting a response from a website using the grequests library can take a long time.
    It is more efficient to try again after a certain short time-period, especially with a website like Tripadvisor
    which has an unstable servor.
    After getting a response, this function will then generate a soup object from the BeautifulSoup library.]
    """
    headers = {"User-Agent": UA.random}
    while True:
        req = grequests.get(url, headers=headers, timeout=TIMEOUT).send()
        response = grequests.map([req])[0]
        if response is not None and response.status_code == 200:
            break

    html = response.text
    soup = BeautifulSoup(html, features="html.parser")
    return soup


def get_all_top_links(url, num_attractions):
    """
    param: url (str) - the url for the homepage of top attractions for a particular city on tripadvisor.com
    param: num_attractions (int) - the number of attraction-urls to gather starting from the homepage and continuing on to
        the next page (and the ext page...)
    return: all_urls (list) - a list of urls.
    """
    # 1. get response obj. ==> 2. get html code. ==> 3. get soup obj.
    front_page_soup = get_response_then_get_soup(url)

    top_attractions_urls = list()
    count = 0
    while True:  # while there are more pages to gather urls from
        count += 1
        urls = get_links_from_page(front_page_soup)
        top_attractions_urls.extend(urls)
        if len(top_attractions_urls) >= num_attractions:
            break
            # otherwise, continue to get the next page!
        try:
            front_page_soup = get_next_page_soup(front_page_soup)  # redefine the new "front-page" as the next page.
            if front_page_soup is None:
                logger.error(SOUP_ERROR)
                break
        except Exception as e:
            logger.error(f"{SOUP_ERROR}: {e}")
            break

    return top_attractions_urls


def main():
    """
    # grab home-page url for each city.
    paris_top_to_do_url = config_data["urls"]["Paris_top_url"]
    b_a_top_to_do_url = config_data["urls"]["Buenos_Aires_top_url"]
    washington_top_to_do_url = config_data["urls"]["Washington_top_url"]
    seoul_top_to_do_url = config_data["urls"]["Seoul_top_url"]
    cairo_top_to_do_url = config_data["urls"]["Cairo_top_url"]

    # configure logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)
    handler = logging.FileHandler("tripadvisor.log")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    urls_paris = get_all_top_links(paris_top_to_do_url, NUM_ATTRACTIONS)
    with open("url_list.csv", "w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Num", "URL"])
        for i, url in enumerate(urls_paris, start=1):
            writer.writerow((i, url))

    urls_b_a = get_all_top_links(b_a_top_to_do_url, NUM_ATTRACTIONS)
    with open("url_list_ba.csv", "w") as b_a_csv:
        writer = csv.writer(b_a_csv)
        writer.writerow(["Num", "URL"])
        for i, url in enumerate(urls_b_a, start=1):
            writer.writerow((i, url))

    urls_cairo = get_all_top_links(cairo_top_to_do_url, NUM_ATTRACTIONS)
    with open("url_list_cairo.csv", "w") as cairo_csv:
        writer = csv.writer(cairo_csv)
        writer.writerow(("Num", "URL"))
        for i, url in enumerate(urls_cairo, start=1):
            writer.writerow((i, url))

    urls_wash = get_all_top_links(washington_top_to_do_url, NUM_ATTRACTIONS)
    with open("url_list_wash.csv", "w") as wash_csv:
        writer = csv.writer(wash_csv)
        writer.writerow(("Num", "URL"))
        for i, url in enumerate(urls_wash, start=1):
            writer.writerow((i, url))

    urls_seoul = get_all_top_links(seoul_top_to_do_url, NUM_ATTRACTIONS)
    with open("url_list_seoul.csv", "w") as seoul_csv:
        writer = csv.writer(seoul_csv)
        writer.writerow(("Num", "URL"))
        for i, url in enumerate(urls_seoul, start=1):
            writer.writerow((i, url))
    """

if __name__ == '__main__':
    main()
