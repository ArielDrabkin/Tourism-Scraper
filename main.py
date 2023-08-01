import json
import logging
from scripts.top_attractions import get_all_top_links, get_city_top_attractions_url
import pandas as pd
from scripts.attraction_mining import attractions_data
from scripts.handle_database import populate_tables, meteorological_data, create_database
import argparse
from scripts.api_access import generate_weather_df, request_from_weather_api
from ydata_profiling import ProfileReport
import warnings
warnings.filterwarnings("ignore")

# Load configuration settings from a JSON file
with open("config.json", "r") as config_file:
    configs = json.load(config_file)

# Get the URL for the list of top attractions in 5 major cities
ALL_CITY_HOMEPAGES = configs["urls"]  # dictionary of urls for 5 cities

# Get the URL for the list of met data in 5 major cities
WEATHER_API_URLS = configs["WEATHER_API_URLS"]

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


def create_argparse():
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('cities', nargs='?', type=str,
                        help="Enter chosen city/cites")
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

    # Split the comma-separated list of cities and keywords provided in the command-line arguments strip any whitespace
    cities = [city.strip().title() for city in args.cities.split(",")]
    key_words = [key.strip() for key in args.key_words.lower().split(",")]

    # Convert the number of attractions to an integer
    attractions_num = int(args.attractions_num)

    # Convert the select_output argument to lowercase
    select_output = args.select_output.lower()
    return cities, key_words, attractions_num, select_output


def checking_inputs(select_output, cities, key_words):
    # Check the select_output argument and update accordingly
    if select_output == "all":
        logger.info(
            f"Will start working on retrieving data for all attractions and meteorological data "
            f"in {', '.join(cities)}.")
    elif select_output == "key_words":
        logger.info(
            f"Will start working on retrieving data for meteorological and {','.join(key_words)} attractions "
            f"data in {', '.join(cities)}.")

    # If the select_output argument is not "all" or "key_words", print an error message and exit the script.
    elif (select_output != "key_words") and (select_output != "all"):
        print("You picked an Invalid output select option.\n"
              "Bye Bye.")
        return
    # Get the urls for the top attractions webpage of the chosen cities
    cities_urls = list()
    for city in cities:
        if city.title() + "_top_url" in ALL_CITY_HOMEPAGES.keys():
            cities_urls.append(ALL_CITY_HOMEPAGES[city.title() + "_top_url"])
        else:
            city_url = get_city_top_attractions_url(city)
            if city_url is None:
                print("Sorry, the url was not right, please try again.")
                return
            else:
                cities_urls.append(city_url)
    return cities_urls


def storing_data(cities, attractions_num, cities_urls):
    ranks, urls = [], []
    for i, city in enumerate(cities_urls):
        city_attractions_urls = get_all_top_links(city, attractions_num)
        ranks += list(range(1, len(city_attractions_urls) + 1))
        urls += city_attractions_urls
        logger.info(f"Received {round(len(urls) / (i + 1))} urls for the attractions of {cities[i]}")

    # Scrape attraction data from each URL and return a Pandas dataframe
    attraction_df = attractions_data(urls, ranks, REQUEST_BATCH_SIZE)

    # Download meteorological data from api's
    for city in cities:
        request_from_weather_api(city)

    # create a Pandas dataframe with the meteorological data
    met_df = generate_weather_df()
    logger.info(f"Created Data frame with annual weather data in {','.join(cities)}")

    # create_database
    create_database()
    logger.info(f"Created attraction Data-Base")

    # input the scraped data to the project database
    populate_tables(attraction_df)  # attractions data
    meteorological_data(met_df)  # meteorological data
    logger.info(f"populate_tables and meteorological_data added to DB")
    return attraction_df, met_df


def main():
    """
    This script scrapes TripAdvisor.com for data on tourist attraction popularity in selected cities by chosen keywords.
    It provides insights into the most popular tourist destinations in a given city, allowing users to plan their
    travel itineraries more efficiently.
    To start using the web scraper, input the cities and relevant keywords you want to search for, separated by white
    spaces and followed by a comma at the end of each argument. Additionally, specify the desired number of attractions
    to search for in each city. List the cities and keywords one after the other.
    Finally, select the type output you prefer: "all" to scrape all attractions in chosen cities,
    or "key_words" to scrape attractions by keyword.
    For example, to retrieve popularity data for attractions related to rivers, boats or bridges
    in Paris and Cairo, one can input: "Paris,Cairo" "river,boat,bridge" 420 "key_words".
    """
    # initiate argparse
    cities, key_words, attractions_num, select_output = create_argparse()
    # check inputs
    cities_urls = checking_inputs(select_output, cities, key_words)
    if cities_urls is None:
        return
    # store data
    attraction_df, met_df = storing_data(cities, attractions_num, cities_urls)

    # give user their desired output
    if select_output == "all":
        attraction_df.to_csv("top_attractions.csv", index=False)
        ProfileReport(attraction_df).to_file("attractions_report.html")
        logger.info(f"Attractions report stored successfully")
        met_df.to_csv("meteorological_data.csv", index=False)
        logger.info(f"Attractions and weather data stored successfully")

    # filter only for the data which the user is interested in
    elif select_output == "key_words":
        try:
            # filtered attraction data
            attraction_df.to_csv("top_attractions.csv", index=False)
            filtered_df = pd.read_csv("top_attractions.csv")
            filtered_attractions = filtered_df[
                filtered_df["Popular Mentions"].apply(lambda x: any(word in x for word in key_words))]
            # Save filtered attraction data and meteorological data to CSV files
            filtered_attractions.to_csv("filtered_attractions.csv", index=False)
            ProfileReport(filtered_attractions).to_file("filtered_attractions_report.html")
            logger.info(f"Filtered attractions report stored successfully")
            met_df.to_csv("meteorological_data.csv", index=False)
            logger.info(f"Filtered and weather data stored successfully")
        except TypeError as e:
            logging.error(f"{e} There were no results to the user's filter")
            print("There were no results to your filter. Try a broader search.")


if __name__ == "__main__":
    main()
