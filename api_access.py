import requests
import json
import os


# WEBSITE: https://open-meteo.com

WEATHER_API_URLS = {
    "paris":        "https://archive-api.open-meteo.com/v1/archive?latitude=48.85&longitude=2.35&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT",
    "buenos aires": "https://archive-api.open-meteo.com/v1/archive?latitude=-34.61&longitude=-58.38&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT",
    "cairo":        "https://archive-api.open-meteo.com/v1/archive?latitude=30.06&longitude=31.25&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT",
    "washington":   "https://archive-api.open-meteo.com/v1/archive?latitude=38.89&longitude=-77.04&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT",
    "seoul":        "https://archive-api.open-meteo.com/v1/archive?latitude=37.57&longitude=126.98&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT",
    "london":       "https://archive-api.open-meteo.com/v1/archive?latitude=51.51&longitude=-0.13&&start_date=2022-04-01&end_date=2023-04-01&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum&timezone=GMT"
}


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


def request_from_weather_api():
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

    for city, api_url in WEATHER_API_URLS.items():
        response = requests.get(api_url)
        data = response.json()

        city_name_formatted = city.replace(" ", "_")  # filename will be, for example, "buenos_aires_weather.json"
        if weather_data_already_saved_for_city(city_name_formatted):
            continue  # don't save it again!
        filename = f"{city_name_formatted}_weather.json"
        with open(f"weather_files/{filename}", "w") as file:
            json.dump(data, file)  # write json to json file


if __name__ == "__main__":
    request_from_weather_api()