import json
import csv
import logging
from top_attractions import get_all_top_links
from attraction_mining import attractions_data

# Load configuration settings from a JSON file
with open("config.json", "r") as config_file:
    configs = json.load(config_file)

# Get the URL for the list of top attractions in 5 major cities
ALL_CITY_HOMEPAGES = configs["urls"]  # dictionary of urls for 5 cities

LOG_FORMAT = configs["logger_format_string"]
REQUEST_BATCH_SIZE = 10

logger = logging.getLogger("scrape-log")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(LOG_FORMAT)
handler = logging.FileHandler("tripadvisor.log")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False


def main():
    # Call a function to get a list of URLs for the top Paris attractions
    """
    urls = list()
    for city_url in ALL_CITY_HOMEPAGES.values():
        urls.extend(get_all_top_links(city_url))
    """
    urls = get_all_top_links(ALL_CITY_HOMEPAGES["paris_top_url"])

    # Scrape attraction data from each URL and return a Pandas dataframe
    data_df = attractions_data(urls, REQUEST_BATCH_SIZE)

    # Print the dataframe to the console
    print(data_df.to_string())

    # write the data to csv
    data_df.to_csv('top_attractions.csv', index=False)


if __name__ == '__main__':
    main()
