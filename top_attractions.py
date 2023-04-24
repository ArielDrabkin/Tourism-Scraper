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
        arrow_elements = soup.find_all("div", class_=ARROW_CLASS)  # there are 2 arrows, 1) prev_page, 2) next_page
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
    except Exception:
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
    param: num_attractions (int) - the number of attraction-urls to gather starting from the homepage
        and continuing on to the next page (and the ext page...)
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
