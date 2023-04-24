import pandas as pd
import requests
import json
import os
import regex as re
import urllib.parse

with open("config.json", "r") as config_file:
    configs = json.load(config_file)

LAT_LON_API_KEY = configs["lat_lon_api_key"]
RESOURCE_NOT_FOUND_RESPONSE_CODE = 404
WEATHER_API_BASE_URL = "https://archive-api.open-meteo.com/v1/archive?"
WEATHER_API_URL_PARAMS = {
    "latitude": "",
    "longitude": "",
    "start_date": "2022-04-01",
    "end_date": "2023-04-01",
    "daily": ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean", "precipitation_sum"],
    "timezone": "GMT"
}

WEATHER_API_URLS = {
    "paris":        "https://archive-api.open-meteo.com/v1/archive?latitude=48.85&longitude=2.35&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT",
    "buenos aires": "https://archive-api.open-meteo.com/v1/archive?latitude=-34.61&longitude=-58.38&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT",
    "cairo":        "https://archive-api.open-meteo.com/v1/archive?latitude=30.06&longitude=31.25&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT",
    "washington":   "https://archive-api.open-meteo.com/v1/archive?latitude=38.89&longitude=-77.04&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT",
    "seoul":        "https://archive-api.open-meteo.com/v1/archive?latitude=37.57&longitude=126.98&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT",
    "london":       "https://archive-api.open-meteo.com/v1/archive?latitude=51.51&longitude=-0.13&&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT"
}


def get_annual_data(daily_data_df):
    """
    param: daily_data_df (pd.DataFrame) - This Data Frame has daily values for weather.
    return: (pd.Series) - This Series will contain the following annual weather data, indexed as follows:
    --> min_temp, max_temp, avg_temp, total_annual_precipitation
    """
    min_temp = daily_data_df["temperature_2m_min"].min()
    max_temp = daily_data_df["temperature_2m_max"].max()
    mean_temp = daily_data_df["temperature_2m_mean"].mean()
    total_precipitation = daily_data_df["precipitation_sum"].sum()
    return pd.Series((min_temp, max_temp, mean_temp, total_precipitation),
                     index=("min_temp", "max_temp", "mean_temp", "total_precipitation"))


def get_city_name(filename):
    """
    param: filename (str) - a filename which contains a cityname
    return: str of city name
    Example:
    """
    pattern = r"([\w\s]+)_weather\.json"
    return re.search(pattern, filename).group(1)


def weather_data_already_saved_for_city(city_name):
    """
    param: city_name (str) - a name of a city
    returns True or False, depending on whether there is a file in the
    weather_files directory with the city_name in it.
    The format for the city name should be all lowercase and with "_" instead of " "
    if the city_name is formatted wrong, this function will correct that
    """
    if not os.path.exists("weather_files"):
        os.makedirs("weather_files")

    # correct format of city_name if it's wrong
    city_name = city_name.lower().replace(" ", "_")
    filenames = os.listdir("weather_files")
    for filename in filenames:
        if filename.find(city_name) != -1:
            return True  # weather data already saved for this city

    return False  # weather data has not been saved for this city


def lat_lon_of_city(city, country=None):
    """
    param: city (str) - a city name
    param: country (str) - a country name.
        - None by default. some cities appear in multiple countries,
            so this might be a helpful parameter
    return (tuple) - a tuple in the following form: (latitude of city, longitude of city)
    The data for this function is requested from the following url:
    https://api-ninjas.com/api/geocoding
    """
    if country:
        api_url = "https://api.api-ninjas.com/v1/geocoding?city={}&country={}{}".format(city, country, city)
    else:
        api_url = "https://api.api-ninjas.com/v1/geocoding?city={}".format(city)
    while True:
        response = requests.get(api_url, headers={"X-Api-Key": LAT_LON_API_KEY})
        if response.status_code == requests.codes.ok:
            break
        elif response.status_code == RESOURCE_NOT_FOUND_RESPONSE_CODE:
            return None, None
        else:
            continue  # try again
    result = response.json()[0]
    return result["latitude"], result["longitude"]


def request_from_weather_api(city, country=None):
    """
    This function is designed to connect to the weather API, https://open-meteo.com
    Using a dictionary whose keys are cities and whose values are the URL from open-meteo we collect all desired data
    The data is then written to a city-specific file, which is saved in a "weather_files" directory
    The data which is gathered from each city includes the following features:
    General Features:
        Latitude, Longitude, Elevation
    Daily Features:
        [For 2022-04-01 to 2023-04-01]
        Max Temp, Min Temp, Mean Temp, Precipitation Sum (rain+snow)
    """
    """
    if not os.path.exists("weather_files"):
        os.makedirs("weather_files")
    
    for city, api_url in WEATHER_API_URLS.items():
        response = requests.get(api_url)
        data = response.json()

        city_name_formatted = city.replace(" ", "_")  # filename will be, for example, "buenos_aires_weather.json"
        if weather_data_already_saved_for_city(city_name_formatted):
            continue  # don't save it again!
        filename = f"{city_name_formatted}_weather.json"
        with open(f"weather_files/{filename}", "w") as file:
            json.dump(data, file)  # write json to json file
    """
    city = city.lower().replace(" ", "_")  # filename will be, for example, "buenos_aires_weather.json"
    if weather_data_already_saved_for_city(city):  # TODO - This function doesn't take into account country
        return
    else:  # if we already have data for this city
        if country:
            latitude, longitude = lat_lon_of_city(city, country)
        else:
            latitude, longitude = lat_lon_of_city(city)

        WEATHER_API_URL_PARAMS["latitude"] = latitude
        WEATHER_API_URL_PARAMS["longitude"] = longitude

        url = WEATHER_API_BASE_URL + urllib.parse.urlencode(WEATHER_API_URL_PARAMS, doseq=True)
        print(url)
        response = requests.get(url)
        data = response.json()

        filename = f"{city}_weather.json"
        with open(f"weather_files/{filename}", "w") as file:
            json.dump(data, file)  # write json to json file


def generate_weather_df():
    """
    param: --
    returns: Pandas DataFrame of annual weather data for various cities
    This function will take all weather data json files from a given directory (weather_files)
    and will return data into a pd.DataFrame which will then be used to populate a tourist attraction database.
    The weather features are all DAILY values for the year 2022-04-01 to 2023-04-01, but annual data will be
    calculated using a helper function. The final output will be a dataframe with the following columns:
        --> Min_temp, Max_temp, mean_temp, total_precipitation
    """
    if not os.path.exists("weather_files"):
        os.makedirs("weather_files")

    all_annual_data = dict()
    filenames = os.listdir("weather_files")
    for filename in filenames:
        with open(f"weather_files/{filename}", "r") as file:
            json_str = file.read()
        data_dict = json.loads(json_str)
        daily_data_df = pd.DataFrame.from_dict(data_dict["daily"])
        annual_data = get_annual_data(daily_data_df)
        all_annual_data[get_city_name(filename)] = annual_data
    print(pd.DataFrame.from_dict(all_annual_data, orient='index'))
    return pd.DataFrame.from_dict(all_annual_data, orient='index')


if __name__ == "__main__":
    request_from_weather_api("Moscow", "Russia")