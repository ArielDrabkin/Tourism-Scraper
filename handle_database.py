import pymysql
import pandas as pd
import json

with open("mysql_config.json", "r") as mysql_config:
    config = json.load(mysql_config)

HOST = config["host"]
USER = config["user"]
PASSWORD = config["password"]

DEBUG_MODE = False

# TODO HIDE PASSWORD SOMEHOW
# TODO add Pandas to requirements.
# TODO add pymysql to requirements.


def city_already_recorded(city):
    """
    param: city: A string of the city name
    return: Return True if the city is aleady in the cities table of the Attractions database
    """
    with pymysql.connect(host=HOST, user=USER, password=PASSWORD, database="Attractions") as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM cities WHERE name="{}";'.format(city))
        existing_records = c.fetchall()
        if existing_records is None or len(existing_records) == 0:
            return False
        else:
            return True


def attraction_already_recorded(attraction):
    """
    param: attraction: A string of the attraction name
    return: Return True if the attraction is aleady in the attractions table of the Attractions database
    """
    with pymysql.connect(host=HOST, user=USER, password=PASSWORD, database="Attractions") as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM attractions WHERE name="{}";'.format(attraction))
        existing_records = c.fetchall()
        if existing_records is None or len(existing_records) == 0:
            return False
        else:
            return True


def popular_mention_already_recorded(popular_mention):
    """
    param: popular_mention: A string of the popular_mention text
    return: Return True if the popular_mention has already been recorded in the popular_mention table.
    """
    with pymysql.connect(host=HOST, user=USER, password=PASSWORD, database="Attractions") as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM popular_mentions WHERE popular_mention="{}"'.format(popular_mention))
        existing_records = c.fetchall()
        if existing_records is None or len(existing_records) == 0:
            return False
        else:
            return True


def populate_tables(df):
    """
    params: Pandas.DataFrame
    return: None

    Populate the tables in the Attractions database using additional lines of data from a pandas dataframe.
    The structure of the dataframe is as follows (generated using * pd.DataFrame.columns *)
    ['City', 'Name', 'Tripadvisor Rate', 'Popular Mentions', 'Score',
       'Reviewers#', 'Excellent', 'Very good', 'Average', 'Poor', 'Terrible',
       'Exellent_ratio', 'VG_ratio', 'Average_ratio', 'Poor_ratio', 'Terrible_ratio']
    """
    with pymysql.connect(host=HOST, user=USER, password=PASSWORD, database="Attractions") as conn:
        c = conn.cursor()

        # 0) populate city table:
        sql_insert_cities = (
            " INSERT INTO cities (name) "
            " VALUES (%s);"
        )

        # 1) populate attractions table:
        sql_insert_attraction = (
            " INSERT INTO attractions (name, city_id) "
            " VALUES (%s, (SELECT id FROM cities WHERE cities.name=%s));"
        )

        # 2) populate attraction_stats table:
        sql_insert_attraction_stats = (
            " INSERT INTO attraction_stats "
            "(attraction_id, ranking, num_reviewers, excellent_review, very_good_review, average_review, poor_review, terrible_review) "
            "VALUES ((SELECT id FROM attractions WHERE attractions.name=%s), %s, %s, %s, %s, %s, %s, %s) "
        )

        # 3) populate popular_mentions:
        sql_insert_pop_mentions = (
            " INSERT INTO popular_mentions (popular_mention) "
            " VALUES (%s) "
        )

        # 4) populate popular_mentions_attractions:
        sql_insert_pop_mention_attraction = (
            " INSERT INTO popular_mentions_attractions (attraction_id, popular_mention_id) "
            " VALUES ((SELECT id FROM attractions WHERE name=%s), (SELECT id FROM popular_mentions WHERE popular_mention=%s)) "
        )

        for index, attraction in df.iterrows():
            if attraction_already_recorded(attraction["Name"]):
                continue # move to the next attraction

            if not city_already_recorded(attraction["City"]):
                c.execute(sql_insert_cities, (attraction["City"],))

            c.execute(sql_insert_attraction, (attraction["Name"], attraction["City"]))
            c.execute(sql_insert_attraction_stats, (attraction["Name"], attraction["Tripadvisor Rate"], attraction["Reviewers#"], attraction["Excellent"], attraction["Very good"], attraction["Average"], attraction["Poor"], attraction["Terrible"]))
            conn.commit()

            for popular_mention in attraction["Popular Mentions"]:  # only add the record if it isn't there already
                if popular_mention_already_recorded(popular_mention):
                    c.execute(sql_insert_pop_mention_attraction, (attraction["Name"], popular_mention))
                    conn.commit()
                else:  # popular mention not yet recorded
                    c.execute(sql_insert_pop_mentions, (popular_mention,))
                    c.execute(sql_insert_pop_mention_attraction, (attraction["Name"], popular_mention))
                    conn.commit()


def create_database():
    """
    This function is used to create the Attractions database, whose design can be found
    """
    with pymysql.connect(host=HOST, user=USER, password=PASSWORD) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE database IF NOT EXISTS Attractions;")

    with pymysql.connect(host=HOST, user=USER, password=PASSWORD, database="Attractions") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                top_attractions_url VARCHAR(255)
            );""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attractions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                city_id INT,
                url VARCHAR(255),
                FOREIGN KEY (city_id) REFERENCES cities(id)
            );""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attraction_stats (
                attraction_id INT,
                ranking INT,
                num_reviewers INT,
                excellent_review INT,
                very_good_review INT,
                average_review INT,
                poor_review INT,
                terrible_review INT,
                FOREIGN KEY (attraction_id) REFERENCES attractions(id)
            );""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS popular_mentions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                popular_mention VARCHAR(255)
            );""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS popular_mentions_attractions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                attraction_id INT,
                popular_mention_id INT,
                FOREIGN KEY (attraction_id) REFERENCES attractions(id),
                FOREIGN KEY (popular_mention_id) REFERENCES popular_mentions(id)
            );""")

    if DEBUG_MODE:
        cursor.execute("SHOW TABLES;")
        results = cursor.fetchall()
        for result in results:
            print(result)


if __name__ == "__main__":
    with open("top_attractions.csv", "r", encoding="utf8") as file:
        df = pd.read_csv(file)
        populate_tables(df)

    with pymysql.connect(host=HOST, user=USER, password=PASSWORD, database="Attractions") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cities;")
        results1 = cursor.fetchall()
        print("CITIES")
        for result in results1:
            print(result)

        cursor.execute("SELECT * FROM attractions;")
        results2 = cursor.fetchall()
        print("ATTRACTIONS")
        for result in results2:
            print(result)

        cursor.execute("SELECT * FROM popular_mentions_attractions;")
        results3 = cursor.fetchall()
        print("POPULAR MENTIONS/ATTRACTIONS")
        for r in results3:
            print(r)

        cursor.execute("SELECT * FROM popular_mentions;")
        results4 = cursor.fetchall()
        print("POPULAR MENTIONS")
        for r in results4:
            print(r)

        cursor.execute("SELECT * FROM attraction_stats;")
        results5 = cursor.fetchall()
        print("ATTRACTION STATS")
        for r in results5:
            print(r)

    #main()
