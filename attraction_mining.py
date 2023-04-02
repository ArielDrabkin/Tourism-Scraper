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
    config_data = json.load(config_file)

LOG_FORMAT = config_data["logger_format_string"]

# Set up logging to write messages to a file with a specific format and logging level.
logger = logging.getLogger("scrape-log")
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


def tripadvisor_name_rate(soup):
    """
    param: soup - a parsed html attraction from a tripadvisor.com attraction webpage.
    return: info dict - a dictionary containing information about the name, lovation and rating of a tourist attraction
    on trip advisor.com. 
    """
    # Find the main section tag that contains the needed data
    main_tag = soup.find('section', "vwOfI nlaXM")

    # Get rate, city name, tags and attraction's name info
    try:
        rate = main_tag.find('div', class_='biGQs _P pZUbB KxBGd').text.strip()
    except AttributeError:
        rate = ['empty']
    try:
        rate_tag = int(rate.split()[0][1:]),
    except IndexError:
        rate_tag = None
    city = rate.split()[-1]
    name = soup.find('h1', "biGQs _P fiohW eIegw").text.strip()
    main_tag = soup.find('div', "qWPrE XCaFq bSHRx")  # Find the main div tag that contains attraction descriptions

    # Find the main div tag that contains attraction descriptions and scrape attraction tags
    try:
        popular_mentions = [elem.text.strip() for elem in
                            main_tag.findAll('span', class_='biGQs _P vvmrG')]  # scrapes attraction tags
    except AttributeError:
        popular_mentions = ['empty']
    info_dict = {"City": city, "Name": name, "Tripadvisor Rate": rate_tag, "Popular Mentions": popular_mentions}
    return info_dict


def attraction_stats(soup):
    """
    param: soup - a parsed html attraction from a tripadvisor.com attraction webpage.
    return: stats (dict) - containing statistics about a tourist attraction on tripadvisor.com
        stats contains the following data: attraction's score, number of reviewers, and
        ratios of excellent, very good, average, poor, and terrible ratings.
    """
    main_tag = soup.find('div', "yFKLG")  # Find the main div tag containing the statistics

    # Extract the number of reviewers and the score of the attraction
    try:
        reviewers = main_tag.find('span', class_='biGQs _P pZUbB KxBGd').text.strip().split()[0].replace(",", "")
    except AttributeError:
        reviewers = ['empty']
    try:
        score = main_tag.find('div', class_='biGQs _P fiohW hzzSG uuBRH').text.strip()
    except AttributeError:
        score = ['empty']

    # Extract the rating scales and rates from the raw html
    raw_rates = str(soup.findAll('div', "IMmqe"))
    rate_scales_pattern = r'<div class="biGQs _P pZUbB hmDzD">(.+?)</div>'
    scales = re.findall(rate_scales_pattern, raw_rates)
    reviewers_rate_pattern = r'<div class="biGQs _P pZUbB osNWb">(.+?)</div>'
    rates = re.findall(reviewers_rate_pattern, raw_rates)
    rates = [re.sub(",", "", rate) for rate in rates]

    # Calculate and store the ratios of each rating type
    ratios_dict = {
        "Exellent_ratio": int(rates[0]) / int(reviewers),
        "VG_ratio": int(rates[1]) / int(reviewers),
        "Average_ratio": int(rates[2]) / int(reviewers),
        "Poor_ratio": int(rates[3]) / int(reviewers),
        "Terrible_ratio": int(rates[4]) / int(reviewers),
        "Score": score
    }

    # Store the extracted statistics in a dictionary
    stats = {"Score": score, "Reviewers#": reviewers}
    stats.update({key: int(value) for key, value in zip(scales, rates)})
    stats.update(ratios_dict)
    return stats


def attractions_data(lst, batch_size):
    """
    params: lst (list)- a list of urls of tourist attraction webpages from tripadvisor.com
            batch_size (int) - the number of urls to get a response from in an asynchronous grequests get() function.
    return: data_df (pandas.DataFrame) - contains all the statistical data about each attraction
            whose url was passed to this function
    """
    # Initialize variables
    data_df = None
    urls = lst.copy()
    urls_counter = 1
    while urls:
        # update the urls batch and the urls list
        batch, urls = urls[:batch_size], urls[batch_size:]

        # Send requests to retrieve attractions data asynchronously
        while True:  # try to get resonse from the batch until it works
            try:
                responses = [grequests.get(url, headers=headers, timeout=TIMEOUT) for url in batch]
                response_unparsed = grequests.map(responses,
                                                   size=batch_size)  # retrieve attractions data asynchronously
                for response in response_unparsed:
                    if response is None or response.status_code != 200:
                        raise Exception("Couldn't get response from attraction.")
                break
            except Exception as e:
                logger.error(e)
                continue

        for attraction in response_unparsed:
            logger.info(f"Start retrieving attraction information from url #{urls_counter}")
            soup = BeautifulSoup(attraction.text, 'html.parser')  # Parse the HTML response using BeautifulSoup
            logger.debug(f"The response is parsed into a BeautifulSoup object")

            # Scrape the needed stats
            attractions_dict = tripadvisor_name_rate(soup)
            stats = attraction_stats(soup)
            attractions_dict.update(stats)
            attractions_dict['Url'] = attraction.url
            logger.debug(f"Successfully retrieved attraction #'{urls_counter}' stats")

            # Append the attraction data to the DataFrame
            if data_df is None:
                data_df = pd.DataFrame.from_dict(attractions_dict, orient='index').T
                data_df.index = data_df.index + 1
                logger.debug(f"Successfully created the DF for river attractions data")
            else:
                data_df = data_df.append(attractions_dict, ignore_index=True)
                data_df.index = data_df.index + 1
                logger.debug(f"Successfully added the river attractions from url #{urls_counter} to the DF")

            # Log and update the urls counter
            logger.info(f"Data from url #{urls_counter} successfully retrieved")
            urls_counter += 1

    return data_df


if __name__ == '__main__':
    attractions_data()
