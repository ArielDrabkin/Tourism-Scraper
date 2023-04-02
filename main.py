import json
import logging
from top_attractions import get_all_top_links
from attraction_mining import attractions_data
from handle_database import populate_tables
import argparse
import pandas as pd

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
    """
    This script scrapes TripAdvisor.com for data on tourist attraction popularity in selected cities by chosen keywords.
    It provides insights into the most popular tourist destinations in a given city, allowing users to plan their
    travel itineraries more efficiently.
    To start using the web scraper, input the cities and relevant keywords you want to search for, separated by white
    spaces and followed by a comma at the end of each argument. Additionally, specify the desired number of attractions
    to search for in each city. List the cities and keywords one after the other.
    For example, to retrieve popularity data for attractions related to rivers in Paris and Cairo, one can input:
    "Paris,Cairo" "river,boat,bridge" 420.
    """


    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('cities', nargs='?', type=str,
                        help="Enter chosen city/cites from the list: 'Paris, Buenos_Aires, Cairo, Washington, Seoul")
    parser.add_argument('key_words', nargs='?', type=str,
                        help="""Enter attraction key words from the list: "river, boat, fairy, opera house, guided tour, 
                             beautiful building, free museum, art, sculptures, architecture" and etc.
                             """)
    parser.add_argument('attractions_num', type=int,
                        help='Enter the number of attractions you would like to scrape from each city.')

    args = parser.parse_args()

    # Test if there is enough user inputs
    if args.cities is None or args.key_words is None or args.attractions_num is None:
        print("Not enough input argument specified.\nBye Bye")
        return
    else:
        cities = args.cities.split(",")
        key_words = args.key_words.split(",")
        attractions_num = int(args.attractions_num)

    # Get the urls for the top attractions webpage of the chosen cities
    cities_urls = [ALL_CITY_HOMEPAGES[city + '_top_url'] for city in cities if city + '_top_url' in ALL_CITY_HOMEPAGES]

    # Call a function to get a list of URLs for the top attractions of the desired cities
    urls = []
    for i,city in enumerate(cities_urls):
        city_attractions_urls = get_all_top_links(city, attractions_num)
        urls.append(city_attractions_urls)
        logger.info(f"Recieved {len(city_attractions_urls)} urls for the attractions of {cities[i]}")

    urls = [url for sublist in urls for url in sublist]

    df = pd.DataFrame(urls)
    df.to_csv('urls.csv', index=False)

    # Scrape attraction data from each URL and return a Pandas dataframe
    data_df = attractions_data(urls, REQUEST_BATCH_SIZE)

    # filter the data frame by the given key_words
    # filtered_attractions = data_df[data_df["Popular Mentions"].apply(lambda x: all(word in x for word in key_words))]

    # write the two data frames to csv
    # data_df.to_csv('top_attractions.csv', index=False)
    # filtered_attractions.to_csv('filtered_attractions.csv', index=False)

    populate_tables(data_df)


if __name__ == "__main__":
    main()
