from time import sleep
import re
# avoid throttling by not sending too many requests one after the other
from random import randint
from warnings import warn
from time import time
from IPython.core.display import clear_output
import numpy as np
from bs4 import BeautifulSoup
from requests import get
import pandas as pd
from datetime import datetime
import glob
import os
from tinydb import TinyDB, Query

# Base URL
# Go to craigslist, set up a search for the apartments you want (price, location, pictures, keywords)
# Then enter the URL here to scrape
base_url = "https://vancouver.craigslist.org/search/apa?query=-shared+-wanted&hasPic=1&search_distance=4.2&postal=v6r3e9&availabilityMode=0&sale_date=all+dates&max_price=4000"


def get_current_prices(base_url: str) -> pd.DataFrame:
    # Scrapes all of the current housing listsings near UBC from Craigslist.
    # Returns a Pandas datatable
    # May include duplicate listings and listings with a price of $0
    # Does not include posts wit hthe keyboards "shared" or "wanted" in the title

    # get the first page of housing prices
    response = get(base_url)
    html_soup = BeautifulSoup(response.text, 'html.parser')

    # get the macro-container for the housing posts
    posts = html_soup.find_all('li', class_='result-row')

    # find the total number of posts to find the limit of the pagination
    results_num = html_soup.find('div', class_='search-legend')
    # pulled the total count of posts as the upper bound of the pages array
    results_total = int(results_num.find('span', class_='totalcount').text)

    # each page has 119 posts so each new page is defined as follows: s=120, s=240, s=360, and so on. So we need to step in size 120 in the np.arange function
    pages = np.arange(0, results_total+1, 120)

    iterations = 0

    post_timing = []
    post_title_texts = []
    bedroom_counts = []
    sqfts = []
    post_links = []
    post_prices = []

    for page in pages:
        print('Scraping page {}'.format(page))

        # get request
        response = get(base_url
                       + "&s="  # the parameter for defining the page number
                       + str(page))  # the page number in the pages array from earlier)

        sleep_time = randint(5, 20)
        print('Waiting {} seconds'.format(sleep_time))
        sleep(sleep_time)

        # throw warning for status codes that are not 200
        if response.status_code != 200:
            warn('Request: {}; Status code: {}'.format(
                requests, response.status_code))

        # define the html text
        page_html = BeautifulSoup(response.text, 'html.parser')

        # define the posts
        posts = page_html.find_all('li', class_='result-row')

        # extract data item-wise
        for post in posts:

            if True:

                # posting date
                # grab the datetime element 0 for date and 1 for time
                post_datetime = post.find(
                    'time', class_='result-date')['datetime']
                post_timing.append(post_datetime)

                # title text
                post_title = post.find('a', class_='result-title hdrlnk')
                post_title_text = post_title.text
                post_title_texts.append(post_title_text)

                # post link
                post_link = post_title['href']
                post_links.append(post_link)

                # removes the \n whitespace from each side, removes the currency symbol, and turns it into an int
                post_price = int(post.a.text.strip().replace(
                    "$", "").replace(',', ''))
                post_prices.append(post_price)

                if post.find('span', class_='housing') is not None:

                    # if the first element is accidentally square footage
                    if 'ft2' in post.find('span', class_='housing').text.split()[0]:

                        # make bedroom nan
                        bedroom_count = np.nan
                        bedroom_counts.append(bedroom_count)

                        # make sqft the first element
                        sqft = int(
                            post.find('span', class_='housing').text.split()[0][:-3])
                        sqfts.append(sqft)

                    # if the length of the housing details element is more than 2
                    elif len(post.find('span', class_='housing').text.split()) > 2:

                        # therefore element 0 will be bedroom count
                        bedroom_count = post.find(
                            'span', class_='housing').text.replace("br", "").split()[0]
                        bedroom_counts.append(bedroom_count)

                        # and sqft will be number 3, so set these here and append
                        sqft = int(
                            post.find('span', class_='housing').text.split()[2][:-3])
                        sqfts.append(sqft)

                    # if there is num bedrooms but no sqft
                    elif len(post.find('span', class_='housing').text.split()) == 2:

                        # therefore element 0 will be bedroom count
                        bedroom_count = post.find(
                            'span', class_='housing').text.replace("br", "").split()[0]
                        bedroom_counts.append(bedroom_count)

                        # and sqft will be number 3, so set these here and append
                        sqft = np.nan
                        sqfts.append(sqft)

                    else:
                        bedroom_count = np.nan
                        bedroom_counts.append(bedroom_count)

                        sqft = np.nan
                        sqfts.append(sqft)

                # if none of those conditions catch, make bedroom nan, this won't be needed
                else:
                    bedroom_count = np.nan
                    bedroom_counts.append(bedroom_count)

                    sqft = np.nan
                    sqfts.append(sqft)

        iterations += 1
        print("Page " + str(iterations) + " scraped successfully!")

    eb_apts = pd.DataFrame({'date_posted': post_timing,
                            'post_title': post_title_texts,
                            'number_bedrooms': bedroom_counts,
                            'sqft': sqfts,
                            'URL': post_links,
                            'price': post_prices,
                            'date_read': datetime.now()})
    return eb_apts


def backup_scrape(data: pd.DataFrame):
    # Saves Pandas datatable with current datetime in file name
    data = clean_data(data)
    file_name = './backups/{}.csv'.format(datetime.now())
    data.to_csv(file_name)
    print("Backed up as {}".format(file_name))


def get_latest_backup() -> pd.DataFrame:
    # Returns the latest backup done from the backups folder
    list_of_files = glob.glob('./backups/*.csv')
    latest_file = max(list_of_files, key=os.path.basename)
    print('Getting latest backup {}'.format(latest_file))
    return pd.read_csv(latest_file)


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    # Cleans scraped data by removing listings with <$500/mo and duplicate URLs and duplicate names
    # (not sure how one does duplicate URLs on craigslist but whatever)
    # takes in DataTable and returns clean one
    eb_apts = data.drop_duplicates(subset='URL')
    eb_apts = data.drop_duplicates(subset='post_title')
    eb_apts = eb_apts.drop(eb_apts[eb_apts['price'] < 500].index)
    eb_apts['number_bedrooms'] = eb_apts['number_bedrooms'].apply(
        lambda x: float(x))
    from datetime import datetime
    eb_apts['date_posted'] = pd.to_datetime(eb_apts['date_posted'])
    return eb_apts


def update_listings(scraped_data: pd.DataFrame):
    # update the unique listing of apartments in the database
    # if listing does not exist, add it to the database for the first time and add it's first price
    # if listing does exist, update it's current price
    db = TinyDB('./db/listings.json')
    unique_listings_table = db.table('unique_listings')
    price_snapshots_table = db.table('prices')
    listing = Query()
    price_snapshot = Query()
    for scraped_listing in scraped_data.itertuples():
        # for each listing, see if it's in the
        number_of_matches: int = len(unique_listings_table.search(
            listing.URL == scraped_listing.URL))
        if number_of_matches == 0:
            # listing does not exist, add it to unique house listing
            unique_listings_table.insert({
                'date_posted': scraped_listing.date_posted,
                'post_title': scraped_listing.post_title,
                'number_bedrooms': scraped_listing.number_bedrooms,
                'sqft': scraped_listing.sqft,
                'URL': scraped_listing.URL,
            })
            price_snapshots_table.insert({
                'URL': scraped_listing.URL,
                'timestamp': scraped_listing.date_read,
                'price': scraped_listing.price
            })
            print("Inserted {} into database".format(
                scraped_listing.post_title))
        else:
            # listing already exists, update it's last-seen time and last price
            if len(price_snapshots_table.search(
                    price_snapshot.URL == scraped_listing.URL and
                    price_snapshot.timestamp == scraped_listing.date_read)) == 0:
                price_snapshots_table.insert({
                    'URL': scraped_listing.URL,
                    'timestamp': scraped_listing.date_read,
                    'price': scraped_listing.price
                })
                print("Updated price for {} in database".format(
                    scraped_listing.post_title))


if __name__ == "__main__":
    #scraped_data = get_current_prices(base_url)
    scraped_data = get_latest_backup()
    update_listings(scraped_data)
