<div style="background-color:#00AA6C; color:white; text-align:center">
    <h1>TripAdvisor Webscraping Project</h1>
</div>

<div style="text-align:center">
    <img src="https://static.tacdn.com/img2/brand_refresh/Tripadvisor_lockup_horizontal_secondary_registered.svg" width="300" height="100">
</div>

<div style="background-color:#00AA63; color:white; text-align:center">
    <h2>Welcome to our TripAdvisor Webscraping Project!</h2>
</div>

<div style="background-color:#000000; color:white; text-align:center">
    <h3><strong>Overview:</strong></h3>
</div>

<div style="color:white; text-align:justify; padding:20px">
    <p>The purpose of this research project is to investigate the relationship between major rivers and the popularity of tourist attractions in five major cities worldwide: Paris, France; Cairo, Egypt; Washington, D.C., USA; Seoul, South Korea; and Buenos Aires, Argentina.</p>
    <p>The project allows users to use a command line interface to scrape TripAdvisor.com for data on tourist attraction popularity in selected cities based on chosen keywords. The data provides insights into the most popular tourist destinations in a given city, allowing users to plan their travel itineraries more efficiently.</p>
    <p>The web scraper will filter the scraped data to only include tourist attractions that have descriptions related to the specified keywords which a user wants.</p>
    <p>User input: This webscraping tool will provide users with a more focused and relevant dataset according to their interests. The collected data will be used to explore and compare the popularity of tourist attractions related to their major rivers in the selected cities.</p>
    <p>More details of the user input will be discussed in the "How to" section of this intro.</p>
</div>

<div style="background-color:#000000; color:white; text-align:center">
    <h3><strong>Objectives:</strong></h3>
</div>

<div style="color:white; text-align:left">
    <ul>
        <li>To scrape data from <strong>TripAdvisor.com</strong> related to the top tourist attractions in five major cities worldwide: Paris, Cairo, Washington, D.C., Seoul, and Buenos Aires.
        <li>To filter the scraped data for only those tourist attractions that have descriptions related to rivers.
        <li>To explore and summarize the popularity of the tourist attractions related to river in the tested major cities.
        <li>To conduct statistical analysis for comparison of the collected data to test hypotheses related to the project's objectives.
        <li>To contribute to the development of tourism strategies that can leverage the centrality and prestige of cities' major rivers to attract more tourists.
        </li>
    </ul>
</div>

<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>Methods</h2>
</div>

<div style="text-align:center; ">
    <p>Python programming language is used in this project, specifically the Grequests, and BeautifulSoup packages, to scrape data from TripAdvisor.com.<p>
    <p>First, the top attractions in each of the five cities were scraped, and then filtered for only those that have descriptions related to rivers.<p>
    <p>The code developed for web scraping is specific to the TripAdvisor.com website and cannot be used for other websites that are organized differently.<p>
    <p>The next step is to conduct statistical analysis on the collected data to test hypotheses related to the project's objectives.<p>
</div>

<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>How to deploy this webscraper</h2>
</div>
<div style="text-align:left; ">
<p>Run the main script (main.py) from your command line, using the following instructions for the input parameter:</p>
<ul>
    <li> Input the cities and relevant keywords you want to search for, separated by white
    spaces and followed by a comma at the end of each group of arguments.
    <li> Additionally, specify the desired number of attractions per city.
    to search for in each city.
    <li><strong>Usage example: Cairo,Paris river,boat,bridge 420.</strong>
    </li>
</ul>
</div>

<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>Database structure:</h2>
</div>

![image](https://user-images.githubusercontent.com/124047859/229366709-f54c0a51-df96-48ea-a3b4-8e1944b8d159.png)

<div style="text-align:center">
    <p><strong>(Generated on dbdiagram.io)</strong></p>
</div>
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
</div>

<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>Contributors</h2>
</div>

<div style="text-align:center;">
    <p>This project is brought to you by Ariel Drabkin and Yonatan Abrams.</p>
    <hr></hr
    <p>We would also like to extend a special thanks to the following outstanding individuals:
    <p>Felipe, Yoni K, Yoni M, Merav</p>
    <p>Thank you for the inspiration and guidance.</p>
</div>

<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>Repository</h2>
</div>

<div style="text-align:center;">
    <p>The project is available on a public repository, Please feel free to check it out and contribute!
        <a href="https://github.com/yoniabrams/scrape_tripadvisor">https://github.com/yoniabrams/scrape_tripadvisor</a>.
</div>

<div style="background-color:#00AA6C; color:white; text-align:center">
    <h2>Thank you for visiting!</h2>
</div>

<div style="text-align:center; padding:20px">
    <img src="https://avatars.githubusercontent.com/u/127224022?v=4" alt width="100" height="100">
        <h3>Ariel Drabkin, M.Sc. </h3>
        <p><a href="https://github.com/ArielDrabkin">Ariel's GitHub</a></p>
        <p><a href="https://www.linkedin.com/in/ariel-drabkin-6b361212a">Ariel's LinkedIn profile</a></p>
</div>

<div style="background-color:#00AA6C; text-align:center; color:#00AA6C"></div>

<div style="text-align:center; padding:20px">
    <img src="https://media.licdn.com/dms/image/C4D03AQGoE8meIrOy1Q/profile-displayphoto-shrink_800_800/0/1655661599542?e=1684368000&v=beta&t=d3FckhqY3t4eca_wY-TIbBWJcyHRukO4gIukw7urZQE" alt height="100" width="100">
        <h3>Yoni Abrams</h3>
        <p><a href="https://www.linkedin.com/in/yabrams/">LinkedIn profile</a></p>
</div>

<div style="background-color:#00AA6C; text-align:center; color:#00AA6C"></div>
