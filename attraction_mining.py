from bs4 import BeautifulSoup
import json
import re
from fake_useragent import UserAgent
import pandas as pd
import logging
import warnings
import grequests

TIMEOUT = 5
BATCH_SIZE = 5

# Dismiss warnings for updating packages
warnings.filterwarnings("ignore", category=FutureWarning)

# Read configuration data from a json file
with open("config.json", "r") as config_file:
    configs = json.load(config_file)

LOG_FORMAT = configs["logger_format_string"]
LOGGER_NAME = configs["logger_name"]
RATE_CLASS = configs["soup_elements"]["rate_class"]
ATTRACTION_DESCRIPTION_TAG = configs["soup_elements"]["attraction_description_tag"]
DATA_SECTION_TAG = configs["soup_elements"]["data_section_tag"]
NAME_TAG = configs["soup_elements"]["name_tag"]
POPULAR_MENTION_TAG = configs["soup_elements"]["popular_mention_tag"]
REVIEWERS_TAG = configs["soup_elements"]["reviewers_tag"]
SCORE_TAG = configs["soup_elements"]["score_tag"]
RAW_RATES_TAG = configs["soup_elements"]["raw_rates_tag"]
STAT_TAG = configs["soup_elements"]["stat_tag"]
RESPONSE_ERROR = configs["log_messages"]["response_error"]

# Set up logging to write messages to a file with a specific format and logging level.
logger = logging.getLogger(LOGGER_NAME)
"""
logger.setLevel(logging.INFO)
formatter = logging.Formatter(LOG_FORMAT)
handler = logging.FileHandler("tripadvisor.log")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False
"""

# Create a user agent to use in the headers of HTTP requests
ua = UserAgent(browsers=['edge', 'chrome'])
headers = {"User-Agent": ua.random}


def tripadvisor_popular_mentions(soup):
    """
    param: soup - a parsed html attraction from a tripadvisor.com attraction webpage.
    return: popular_mentions - a list containing information about the tourist attraction popular mentions
    on trip advisor.com.
    """
    # Find the main section tag that contains the needed data
    main_tag = soup.find('div',
                         ATTRACTION_DESCRIPTION_TAG)  # Find the main div tag that contains attraction descriptions

    # Find the main div tag that contains attraction descriptions and scrape attraction tags
    try:
        popular_mentions = [elem.text.strip() for elem in
                            main_tag.findAll('span', class_=POPULAR_MENTION_TAG)]  # scrapes attraction tags
    except AttributeError:
        popular_mentions = ['empty']
    return popular_mentions


def tripadvisor_name_rate(soup):
    """
    param: soup - a parsed html attraction from a tripadvisor.com attraction webpage.
    return: info dict - a dictionary containing information about the name, location and rating of a tourist attraction
    on trip advisor.com.
    """
    # Find the main section tag that contains the needed data
    main_tag = soup.find('section', DATA_SECTION_TAG)

    # Get rate, city name, tags and attraction's name info
    try:
        rate = main_tag.find('div', class_=RATE_CLASS).text.strip()
        city = rate.split()[-1]
    except AttributeError:
        rate = ['empty']
        city = rate
    name = soup.find('h1', NAME_TAG).text.strip()
    popular_mentions = tripadvisor_popular_mentions(soup)

    info_dict = {"City": city, "Name": name, "Popular Mentions": popular_mentions}
    return info_dict


def reviewers_count(soup):
    """
    param: soup - a parsed html attraction from a tripadvisor.com attraction webpage.
    return: reviewers (variable) - containing number of reviewers for a specific attraction.
    """
    main_tag = soup.find('div', STAT_TAG)  # Find the main div tag containing the statistics
    # Extract the number of reviewers and the score of the attraction
    try:
        reviewers = main_tag.find('span', class_=REVIEWERS_TAG).text.strip().split()[0].replace(",", "")
    except AttributeError:
        reviewers = ['empty']
    return reviewers


def reviewers_score(soup):
    """
    param: soup - a parsed html attraction from a tripadvisor.com attraction webpage.
    return: score (variable) - containing the score of a specific attraction.
    """
    main_tag = soup.find('div', STAT_TAG)  # Find the main div tag containing the statistics
    # Extract the number of reviewers and the score of the attraction
    try:
        score = main_tag.find('div', class_=SCORE_TAG).text.strip()
    except AttributeError:
        score = ['empty']
    return score


def attraction_stats(soup):
    """
    param: soup - a parsed html attraction from a tripadvisor.com attraction webpage.
    return: stats (dict) - containing statistics about a tourist attraction on tripadvisor.com
    stats contains the following data: attraction's score, number of reviewers, and
    ratios of excellent, very good, average, poor, and terrible ratings.
    """
    # Extract the rating scales and rates from the raw html
    reviewers = reviewers_count(soup)
    score = reviewers_score(soup)
    raw_rates = str(soup.findAll('div', RAW_RATES_TAG))
    rate_scales_pattern = r'<div class="biGQs _P pZUbB hmDzD">(.+?)</div>'
    scales = re.findall(rate_scales_pattern, raw_rates)
    reviewers_rate_pattern = r'<div class="biGQs _P pZUbB osNWb">(.+?)</div>'
    rates = re.findall(reviewers_rate_pattern, raw_rates)
    rates = [re.sub(",", "", rate) for rate in rates]

    # Calculate and store the ratios of each rating type
    try:
        ratios_dict = {
            "Excellent_ratio": int(rates[0]) / int(reviewers),
            "VG_ratio": int(rates[1]) / int(reviewers),
            "Average_ratio": int(rates[2]) / int(reviewers),
            "Poor_ratio": int(rates[3]) / int(reviewers),
            "Terrible_ratio": int(rates[4]) / int(reviewers),
        }
    except (IndexError, ValueError,TypeError):
        ratios_dict = {
            "Excellent_ratio": 0,
            "VG_ratio": 0,
            "Average_ratio": 0,
            "Poor_ratio": 0,
            "Terrible_ratio": 0,
        }

    # Store the extracted statistics in a dictionary
    stats = {"Score": score, "Reviewers#": reviewers}
    stats.update({key: int(value) for key, value in zip(scales, rates)})
    stats.update(ratios_dict)
    return stats


def add_url_rank(urls, ranks, attraction_url, attractions_dict):
    """
    [Adds the URL and TripAdvisor rank for a given attraction to the provided dictionary.
    Parameters]
    param: urls (list) - A list of attraction URLs.
    param: ranks (list) - A list of TripAdvisor ranks corresponding to the attraction URLs.
    param: attraction_url (str) - The URL of the attraction to add to the dictionary.
    param: attractions_dict (dict) - The dictionary to add the URL and rank information to.
    Returns: (dict) - The updated attractions dictionary.
    """
    attractions_dict['Url'] = re.sub(r'(?<!/)/(?!/)', r'//', attraction_url)
    attractions_dict['Tripadvisor rank'] = ranks[urls.index(attractions_dict['Url'])]
    return attractions_dict


def retrieve_data(soup):
    """
    [Retrieves the relevant data for a TripAdvisor attraction page and returns it as a dictionary.
    Parameters]
    param: soup (BeautifulSoup) - A BeautifulSoup object representing the HTML of the attraction page.
    Returns (dict) - A dictionary containing the name, rating, and other relevant stats for the attraction.
    """
    attractions_dict = tripadvisor_name_rate(soup)  # Scrape the needed stats
    stats = attraction_stats(soup)
    attractions_dict.update(stats)
    return attractions_dict


def attraction_data_update(attractions_dict, urls_counter, data_df):
    """
    param: attractions_dict (dict) - A dictionary containing the name, rating, and other relevant stats for attractions.
    param: urls_counter (int) - The id of the current url.
    param: data_df(df) - Data frame that storing the attraction data that was retrieved before.
    return: data_df (pandas.DataFrame) - contains all the statistical data about each attraction
            whose url was passed to this function
    """
    # Append the attraction data to the DataFrame
    if data_df is None:
        data_df = pd.DataFrame.from_dict(attractions_dict, orient='index').T
        data_df.index = data_df.index + 1
        logger.debug(f"Successfully created the DF for river attractions data")
    else:
        data_df = data_df._append(attractions_dict, ignore_index=True)
        data_df.index = data_df.index + 1
        logger.debug(f"Successfully added the river attractions from url #{urls_counter} to the DF")

    logger.info(f"Data from url #{urls_counter} successfully retrieved")
    return data_df


def attractions_data(urls, ranks, batch_size):
    """
    param: lst (list)- a list of urls of tourist attraction webpages from tripadvisor.com
    param: batch_size (int) - the number of urls to get a response from in an asynchronous grequests get() function.
    return: data_df (pandas.DataFrame) - contains all the statistical data about each attraction
            whose url was passed to this function
    """
    data_df = None  # we will return this dataframe upon scraping all the desired data
    attraction_urls = urls.copy()
    urls_counter = 1
    while attraction_urls:
        batch, attraction_urls = attraction_urls[:batch_size], attraction_urls[
                                                               batch_size:]  # update the urls batch and the urls list
        while True:  # try to get response from the batch until it works
            try:
                responses = [grequests.get(url, headers=headers, timeout=TIMEOUT) for url in batch]
                response_unparsed = grequests.map(responses, size=batch_size)
                for response in response_unparsed:
                    if response is None or response.status_code != 200:
                        raise Exception(RESPONSE_ERROR)
                break  # break from "While True" if successfully got response
            except Exception as e:
                logger.error(e)
                continue  # try again from "While True"

        for attraction in response_unparsed:
            logger.info(f"Start retrieving attraction information from url #{urls_counter}")
            soup = BeautifulSoup(attraction.text, 'html.parser')  # Parse the HTML response using BeautifulSoup
            logger.debug(f"The response is parsed into a BeautifulSoup object")

            # Scrape the needed stats
            attractions_dict = retrieve_data(soup)
            attractions_dict = add_url_rank(urls, ranks, attraction.url, attractions_dict)
            logger.debug(f"Successfully retrieved attraction #'{urls_counter}' stats")

            data_df = attraction_data_update(attractions_dict, urls_counter, data_df)
            urls_counter += 1

    # sort cities by their ranking, within each city.
    data_df = data_df.sort_values(["City", "Tripadvisor rank"], ascending=[True, True])
    return data_df
