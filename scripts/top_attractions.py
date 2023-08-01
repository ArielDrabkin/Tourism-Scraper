import grequests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import logging
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, InvalidArgumentException


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
SEE_ALLS_XPATH = configs["urls"]["see_alls_xpath"]
SEARCH_BAR_XPATH = configs["urls"]["search_bar_xpath"]
TOP_ATTRACTIONS_SEE_ALL_CODE = configs["urls"]["top_attractions_see_all_code"]
THINGS_TO_DO_XPATH = configs["urls"]["things_to_do_xpath"]
SUGGESTION_XPATH = configs["urls"]["suggestion_number_one_xpath"]
TOP_ATTRACTIONS_CODE_FOR_URL = configs["top_attractions_code_for_url"]
A_CLASS_SEE_ALL = configs["urls"]["a_class_see_all"]

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
        urls.append(BASE_URL + title.a[URL_CLASS])

    logger.debug(f"Got {len(urls)} more urls.")
    logger.debug("Finished gathering urls from page.")
    return urls


def get_response_then_get_soup(url):
    """
    Param: url (str) url from a tripadvisor webpage.
    Returns: a soup object of the BeautifulSoup library.
    
    [Motivation: Often, getting a response from a website using the grequests library can take a long time.
    It is more efficient to try again after a certain short time-period, especially with a website like Tripadvisor
    which has an unstable server.
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


def get_correct_see_all_url(see_alls):
    """
    param: see_alls (list) - list of selenium.webdriver.remote.webelement.WebElement objects
    return: see_all_top_attractions
    On the webpage that this scraper is searching, there are several elements which are called "see all".
    Only one of them is for the top attractions of a particular city.
    Based on the url (href class / attribute), we can discern which one is correct.
    """
    for see_all in see_alls:
        url = see_all.get_attribute(URL_CLASS)
        if url.count(TOP_ATTRACTIONS_SEE_ALL_CODE) > 0:
            return url


def get_top_attraction_url_from_city_homepage(homepage_url):
    """
    param: homepage_url (str) - the url for the homepage of a city on tripadvisor.com
    return: (str) - the url for the top attractions list for the city.
    """
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    driver.get(homepage_url)

    while True:
        try:
            see_all_top_things_to_do = wait.until(EC.visibility_of_all_elements_located(
                (By.XPATH, A_CLASS_SEE_ALL)))
            if see_all_top_things_to_do:
                break
        except TimeoutException as e:
            logger.error(e, "need to try again to get all 'see alls'")
            continue

    for see_all in see_all_top_things_to_do:
        url = see_all.get_attribute(URL_CLASS)
        print(url)
        if "Activities-oa0" in url:
            driver.close()
            return url

    driver.close()
    return None  # didn't find the right url


def clear_search_bar(search_bar_element):
    """
    param: search_bar_element (selenium.webdriver element) - the search bar element of the tripadvisor homepage
    This function uses backspace until the search bar is clear for another input
    """
    while search_bar_element.get_attribute("value") != "":
        search_bar_element.send_keys(Keys.BACK_SPACE)


def get_city_top_attractions_url(city_string):
    """
    param: city_string (str) - name of city, or name of city and its country
    return url (str) - url of the top attractions page for the city on tripadvisor.com
    The goal of this function is to use Selenium library to track-down the url.
    This way you don't have to feed the scraper a specific url to get started.
    All you need is a name of a place you want to go!
    """
    # initialize a webdriver object from selenium to engage with website
    driver = webdriver.Chrome()
    driver.get(BASE_URL)

    # set up a WebDriverWait object to allow pages/elements to load properly
    wait = WebDriverWait(driver, 15)

    # find search bar
    search_bar = wait.until(EC.visibility_of_element_located((By.XPATH, SEARCH_BAR_XPATH)))
    city_string = str(city_string+" ")
    while True:
        # erase any existing values in the search-bar
        clear_search_bar(search_bar)

        search_bar.send_keys(city_string)
        driver.implicitly_wait(15000)
        search_bar.send_keys(Keys.ARROW_DOWN)
        driver.implicitly_wait(15000)
        try:
            a_element = wait.until(EC.presence_of_all_elements_located((By.XPATH, SUGGESTION_XPATH)))
            url = a_element[0].get_attribute("href")
            if a_element and url != "":
                break
            else:
                logger.error("a element didn't load properly")
        except TimeoutException as e:
            logger.error(e, "need to try again to get 'a' element again")  # then try again
        except InvalidArgumentException as e:
            logger.error(e, "need to try again to get 'a' element again")  # then try again

    driver.close()
    logger.info(f"got url: {url}")
    top_attractions_url = get_top_attraction_url_from_city_homepage(url)

    return top_attractions_url
