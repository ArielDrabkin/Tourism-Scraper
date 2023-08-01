<div style="background-color:#00AA6C; color:white; text-align:center">
    <h1>TripAdvisor Webscraping Project</h1>
</div>

<div style="text-align:center">
    <img src="https://static.tacdn.com/img2/brand_refresh/Tripadvisor_lockup_horizontal_secondary_registered.svg" width="300" height="100">
</div>
<div style="background-color:#00AA63; color:white; text-align:center">
    <h2>Welcome to the TripAdvisor Webscraping app!</h2>
</div><div style="background-color:#000000; color:white; text-align:center">
    <h3><strong>Overview:</strong></h3>
</div>
<div style="color:white; text-align:justify; padding:20px">
    <p>The purpose of this app is to compare the quality of tourist attractions in tourist cities worldwide, users can input the name of any city in the world that they are interested in researching, as well as keywords related to their specific interests. The web scraper will filter the scraped data to only include tourist attractions that have descriptions related to the specified keywords.</p>
    <p>The app allows users to use a command line interface to scrape TripAdvisor.com for data on tourist attraction popularity in selected cities based on chosen keywords. The data provides insights into the most popular tourist destinations in a given city, allowing users to plan their travel itineraries more efficiently.</p>
    <p>Additionally, the scraper provides relevant meteorological data for the destinations where attraction data is being collected.<p>  
    <p>The web scraper will filter the scraped data to only include tourist attractions that have descriptions related to the specified keywords which a user wants.</p>
</div>

<div style="background-color:#000000; color:white; text-align:center">
    <h3><strong>Objectives:</strong></h3>
</div>

<div style="color:white; text-align:left">
    <ul>
        <li>To scrape data from <strong>TripAdvisor.com</strong> related to the top tourist attractions in all tourist cities.
        <li>To gather relevant data from weather <strong>APIs</strong> to contribute to a holistic picture of a tourist city in conjunction with the top tourist attractions.
        <li>To explore and summarize the popularity of the tourist attractions related to users interested in the desired major cities.
        <li>To conduct statistical analysis for comparison of the collected data to test hypotheses related to the user's objectives.
        <li>To contribute to the development of tourism strategies that can leverage the centrality and prestige of cities' major rivers to attract more tourists.
        </li>
    </ul>
</div>
<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>Methods</h2>
</div>
<div style="text-align:center; ">
    <p>Python programming language is used in this project, specifically the Grequests, and BeautifulSoup packages, to scrape data from<code>tripadvisor.com</code>.<p>
    <p>First, the top attractions for the user's choice cities are scraped, and then filtered for only those that have descriptions related to the keywords which the user desires.<p>
    <p>Alternatively, the user can decide to get all attractions (without filtering). This will be discussed in the detail below.</p>
    <p>The code developed for web scraping is specific to the TripAdvisor.com website and cannot be used for other websites that are organized differently.<p>
    <p>The database which stores this data is called 'Attractions' and will be described in detail below.</p>
    <p>Data is also mined from a weather API from a website<code>https://open-meteo.com</code>. More details will be discussed below.</p>
    <p>With the usage of ydata_profiling package a report is generated with insights regarding the popularity of the desired attractions.<p>
</div>
<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>How to deploy this webscraper</h2>
</div>
<p style="text-align:left; ">
<h4>Configurations:</h4>
<p>
    Connect automatically via the sql configuration file (called mysql_config.json) which contains our mysql user data.<br>
</p>
<p>
   The file <strong>mysql_config.json</strong>, formatted as follows:
</p>
<pre>
    <code style="padding: 10px;">
        {
        "host": data-mining-db1.cttpnp4olbpx.us-west-1.rds.amazonaws.com,
        "user": ariel_yoni,
        "password": ariel_yoni,
        "database": ariel_yoni
        }
    </code>
</pre>

<h4>Running the scraper:</h4>
<p>Run the main script (main.py) from your command line, using the following instructions for the input parameter:</p>
<ul>
    <li> Input the cities and relevant keywords you want to search for, separated by white
    spaces and followed by a comma at the end of each group of arguments.
    <li> Additionally, specify the desired number of attractions per city.
    to search for in each city.
    <li>Finally, select the type output you prefer: "all" to scrape all attractions in chosen cities,
    or "key_words" to scrape attractions by keyword.
    <li>Usage example:  <strong>main.py "Paris, Seoul, Cairo" "museum" 100 "key_words".</strong>
    </li>
</ul>

<h4>Enjoy your output:</h4>
<ul>
    <p>Depending on what you've ask for, you'll receive:
    <li>A "filtered_attraction.csv" file with the data about the attractions you've asked for given your search parameters.<br>
    <li>A "top_attractions.csv" file with the data about all the attractions you've applied the search parameters on.<br>
    <li>A "meteorological_data.csv" file with the data about the weather in the cities you've searched for.<br>
    <li>A "filtered_attractions.html" file with an interactive report of the data about the attractions you've asked given your search parameters.<br>
    </li>
</ul>

<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>Examples from the output report:</h2>
</div>

![city](C:\Users\ariel\TripAdvisor_webscraper\city.jpg)
![words](https://github.com/ArielDrabkin/Tourism_Scraper/blob/readme/words.png)
![stats](C:\Users\ariel\TripAdvisor_webscraper\stats.jpg)
![interactions](C:\Users\ariel\TripAdvisor_webscraper\interactions.jpg)
![correlation.jpg](C:\Users\ariel\TripAdvisor_webscraper\correlation.jpg)


<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>Database structure:</h2>
</div>

![db_diagram](https://github.com/ArielDrabkin/Tourism_Scraper/blob/readme/db_diagram.png)

<div style="text-align:left">
    <h3>Description of Tables in Database:</h3>
    <p><strong>Cities</strong></p>
    <ul>
        <li> id (int) [Auto-Generated]
        <li> name (varchar) [Name of city]
        <li> top_attractions_url (varchar) [tripdvisor url of the top attractions for this city]
        </li>
    </ul>
    <p><strong>Attractions</strong></p>
    <ul>
        <li> id (int) [Auto-Generated]
        <li> name (varchar) [Name of attraction]
        <li> city_id (int) [Foreign key from cities(id)]
        <li> url (varchar) [Tripadvisor url for the attraction]
        </li>
    </ul>
    <p><strong>Attraction_stats</strong></p>
    <ul>
        <li> attraction_id (int) [Foreign key from attractions(id)]
        <li> ranking (int)
        <li> num_reviewers (int)
        <li> excellent_review (int) [Number of "Excellent" reviews]
        <li> very_good_review (int) [Number of...]
        <li> average_review (int) [Number of...]
        <li> poor_review (int) [Number of...]
        <li> terrible_review (int) [Number of...]
        </li>
    </ul>
    <p><strong>Popular_mentions</strong></p>
    <ul>
        <li> id (int) [Auto-generated]
        <li> popular_mention (varchar) [A common phrase/word associated with an attraction]
        </li>
    </ul>
    <p><strong>Popular_mentions_attractions</strong></p>
    <p>(A helper table to reference a popular mention to an attraction and an attraction to all its popular mentions.</p>
    <ul>
        <li> id (int) [Auto-generated]
        <li> attraction_id (int) [Foreign key from attraction(id)]
        <li> popular_mention_id (int) [Foreign key from popular_mentions(id)]
        </li>
    </ul>
    <p><strong>Meteorological_data</strong></p>
    <p>(Annual weather data for a given city</p>
    <ul>
        <li> city_id (int) [Foreign key from cities(id)]
        <li> name (varchar) [City name]
        <li> min_temp (float)
        <li> max_temp (float)
        <li> mean_temp (float)
        <li> total_precipitation (float) [includes both snow and rain]
    </li>
    </ul>
</div>

<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>Contributors</h2>
</div>

<div style="text-align:left;">
<h4>This app was developed as part of the ITC Data Science bootcamp by:</h4>
<ul>
    Ariel Drabkin and Yonatan Abrams
</ul>
</div>

<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>Thank you for visiting!</h2>
</div>



<div style="background-color:#00AA6C; text-align:center; color:#00AA6C"></div>
