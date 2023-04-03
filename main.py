import json
import logging
from top_attractions import get_all_top_links
from attraction_mining import attractions_data
from handle_database import populate_tables
import argparse

# Load configuration settings from a JSON file
with open("config.json", "r") as config_file:
    configs = json.load(config_file)

# Get the URL for the list of top attractions in 5 major cities
ALL_CITY_HOMEPAGES = configs["urls"]  # dictionary of urls for 5 cities

LOG_FORMAT = configs["logger_format_string"]
REQUEST_BATCH_SIZE = 5
URL_VARIABLE_SUFFIX = configs["url_variable_suffix"]
LOGGER_NAME = configs["logger_name"]

logger = logging.getLogger(LOGGER_NAME)
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
                        help="""Enter attraction key words from the list:
                                'river, boat, fairy, opera house, guided tour, 
                             beautiful building, free museum, art, sculptures, architecture' , etc. etc.
                             """)
    parser.add_argument('attractions_num', type=int,
                        help='Enter the number of attractions you would like to scrape from each city.')
    parser.add_argument('select_output', type=str,
                        help='Choose "all" to scrape all data or "key_words" by keyword example: all/key_words.')
    args = parser.parse_args()

    # Test if there is enough user inputs
    if args.cities is None or args.key_words is None or args.attractions_num is None:
        print("Not enough input argument specified.\nBye Bye.")
        return
    else:
        cities = args.cities.split(",")
        key_words = args.key_words.split(",")
        attractions_num = int(args.attractions_num)
        select_output = args.select_output

    for city in cities:
        if city not in ("Cairo", "Buenos_Aires", "Paris", "Seoul", "Washington"):
            print("You either picked an invalid city, or you spelled it wrong.\n"
                  "By Bye.")
            return

    # Get the urls for the top attractions webpage of the chosen cities
    cities_urls = [ALL_CITY_HOMEPAGES[city + URL_VARIABLE_SUFFIX] for city in cities
                   if city + URL_VARIABLE_SUFFIX in ALL_CITY_HOMEPAGES]

    # Call a function to get a list of URLs for the top attractions of the desired cities
    ranks, urls = [], []
    for i, city in enumerate(cities_urls):
        city_attractions_urls = get_all_top_links(city, attractions_num)
        ranks += list(range(1, len(city_attractions_urls) + 1))
        urls += city_attractions_urls
        logger.info(f"Received {round(len(urls) / (i + 1))} urls for the attractions of {cities[i]}")

    # Scrape attraction data from each URL and return a Pandas dataframe
    data_df = attractions_data(urls, ranks, REQUEST_BATCH_SIZE)

    # input the scraped data to the project database
    populate_tables(data_df)

    # give user their desired output:
    if select_output == "all":
        data_df.to_csv("top_attractions.csv", index=False)
    else:  # filter for the data which the user is interested in.
        try:
            filtered_attractions = data_df[
                data_df["Popular Mentions"].apply(lambda x: all(word in x for word in key_words))]
            filtered_attractions.to_csv("filtered_attractions.csv", index=False)
        except TypeError as e:
            logging.error(f"{e} There were no results to the user's filter")
            print("There were no results to your filter. Try a broader search.")


if __name__ == "__main__":
    main()
