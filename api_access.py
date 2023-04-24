import pandas as pd
import requests
import json
import os
import re


def get_annual_data(daily_data_df):
    """
    param: daily_data_df (pd.DataFrame) - This Data Frame has daily values for weather.
    return: (pd.Series) - This Series will contain the following annual weather data, indexed as follows:
    --> min_temp, max_temp, avg_temp, total_annual_precipitation
    """
    min_temp = round(daily_data_df["temperature_2m_min"].min(), 2)
    max_temp = round(daily_data_df["temperature_2m_max"].max(), 2)
    mean_temp = round(daily_data_df["temperature_2m_mean"].mean(), 2)
    total_precipitation = round(daily_data_df["precipitation_sum"].sum(), 2)
    return pd.Series((min_temp, max_temp, mean_temp, total_precipitation),
                     index=("min_temp", "max_temp", "mean_temp", "total_precipitation"))


def get_city_name(filename):
    """
    param: filename (str) - a filename which contains a city name
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


def request_from_weather_api(urls):
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
    if not os.path.exists("weather_files"):
        os.makedirs("weather_files")

    for city, api_url in urls.items():
        response = requests.get(api_url)
        data = response.json()

        city_name_formatted = city.replace(" ", "_")  # filename will be, for example, "buenos_aires_weather.json"
        if weather_data_already_saved_for_city(city_name_formatted):
            continue  # don't save it again!
        filename = f"{city_name_formatted}_weather.json"
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
    met_data = pd.DataFrame.from_dict(all_annual_data, orient='index')
    met_data = met_data.reset_index().rename(columns={'index': 'Name'})

    print(met_data)
    return met_data
