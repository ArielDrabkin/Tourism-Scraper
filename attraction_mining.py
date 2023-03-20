from bs4 import BeautifulSoup
import json
import re
from fake_useragent import UserAgent
import pandas as pd
import logging
import warnings
import grequests

TIMEOUT = 5
BATCH_SIZE = 10
# Dismiss warnings for updating packages
warnings.filterwarnings("ignore", category=FutureWarning)

with open("config.json", "r") as config_file:
    config_data = json.load(config_file)

LOG_FORMAT = config_data["logger_format_string"]

# Set up logging to write messages to a file
# with a specific format and logging level.
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
        Extracts the name, location, and TripAdvisor rating of an attraction from its TripAdvisor page.
        Args: soup (BeautifulSoup object): Parsed HTML of the attraction's TripAdvisor page.
        Returns: dict: A dictionary containing the attraction's name, location, and TripAdvisor rating.
        """
    # Find the main section tag that contains the needed data
    main_tag = soup.find('section', "vwOfI nlaXM")
    # Get rate, city name, tags and attraction's name info
    try:
        rate = main_tag.find('div', class_='biGQs _P pZUbB KxBGd').text.strip()
    except AttributeError:
        rate = ['empty']
    rate_tag, city = int(rate.split()[0][1:]), rate.split()[-1]
    name = soup.find('h1', "biGQs _P fiohW eIegw").text.strip()
    main_tag = soup.find('div', "qWPrE XCaFq bSHRx")  # Find the main div tag that contains attraction descriptions
    try:
        popular_mentions = [elem.text.strip() for elem in
                            main_tag.findAll('span', class_='biGQs _P vvmrG')]  # scrapes attraction tags
    except AttributeError:
        popular_mentions = ['empty']
    info_dict = {"City": city, "Name": name, "Tripadvisor Rate": rate_tag, "Popular Mentions": popular_mentions}
    return info_dict


def attraction_stats(soup):
    """
       Extracts various statistics about an attraction from its TripAdvisor page.
       Args: soup (BeautifulSoup object): Parsed HTML of the attraction's TripAdvisor page.
       Returns: dict: A dictionary containing the attraction's score, number of reviewers, and ratios of excellent, very good,
           average, poor, and terrible ratings.
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
    Retrieve attraction information from a list of URLs and create a Pandas DataFrame.
    Args: lst (list): A list of URLs of attractions to retrieve information from. BATCH_size (int): The number of URLs to retrieve at once.
    Returns: DataFrame: A Pandas DataFrame containing information on the attractions of the chosen city.
    """
    # Initialize variables
    data_df = None
    urls = lst.copy()
    urls_counter = 1
    while urls:
        # update the urls batch and the urls list
        batch, urls = urls[:batch_size], urls[batch_size:]

        # Send requests to retrieve attractions data asynchronously
        response = [grequests.get(url, headers=headers, timeout=TIMEOUT) for url in batch]
        response_unparsed = grequests.imap(response, size=batch_size)
        for attraction in response_unparsed:
            if attraction.status_code != 200 or attraction is None:  # Check if the request was successful
                logger.error(f"Error retrieving attraction from {attraction}")
                continue
            else:
                logger.info(f"Start retrieving attraction information from url #{urls_counter}")
            soup = BeautifulSoup(attraction.text, 'html.parser')  # Parse the HTML response using BeautifulSoup
            logger.debug(f"The response is parsed into a BeautifulSoup object")

            # Scrape the needed stats
            attractions_dict = tripadvisor_name_rate(soup)
            stats = attraction_stats(soup)
            attractions_dict.update(stats)
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
