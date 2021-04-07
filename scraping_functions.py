#build out the loop
from time import sleep
import re
from random import randint #avoid throttling by not sending too many requests one after the other
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

# Scrapes all of the current housing listsings near UBC from Craigslist.
# Returns a Pandas datatable
# May include duplicate listings and listings with a price of $0
# Does not include posts wit hthe keyboards "shared" or "wanted" in the title
def get_current_prices() -> pd.DataFrame:
    #get the first page of housing prices
    response = get('https://vancouver.craigslist.org/search/apa?query=-shared+-wanted&hasPic=1&search_distance=4.2&postal=v6r3e9&availabilityMode=0&sale_date=all+dates')
    html_soup = BeautifulSoup(response.text, 'html.parser')

    #get the macro-container for the housing posts
    posts = html_soup.find_all('li', class_= 'result-row')

    #find the total number of posts to find the limit of the pagination
    results_num = html_soup.find('div', class_= 'search-legend')
    results_total = int(results_num.find('span', class_='totalcount').text) #pulled the total count of posts as the upper bound of the pages array

    #each page has 119 posts so each new page is defined as follows: s=120, s=240, s=360, and so on. So we need to step in size 120 in the np.arange function
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

        #get request
        response = get("https://vancouver.craigslist.org/search/apa?"
                    + "s=" #the parameter for defining the page number 
                    + str(page) #the page number in the pages array from earlier
                    + "query=-shared+-wanted&hasPic=1&search_distance=4.2&postal=v6r3e9&availabilityMode=0&sale_date=all+dates&max_price=4000")

        sleep_time = randint(5,20)
        print('Waiting {} seconds'.format(sleep_time))
        sleep(sleep_time)
        
        #throw warning for status codes that are not 200
        if response.status_code != 200:
            warn('Request: {}; Status code: {}'.format(requests, response.status_code))
            
        #define the html text
        page_html = BeautifulSoup(response.text, 'html.parser')
        
        #define the posts
        posts = page_html.find_all('li', class_= 'result-row')
            
        #extract data item-wise
        for post in posts:

            if True:

                #posting date
                #grab the datetime element 0 for date and 1 for time
                post_datetime = post.find('time', class_= 'result-date')['datetime']
                post_timing.append(post_datetime)

                #title text
                post_title = post.find('a', class_='result-title hdrlnk')
                post_title_text = post_title.text
                post_title_texts.append(post_title_text)

                #post link
                post_link = post_title['href']
                post_links.append(post_link)
                
                #removes the \n whitespace from each side, removes the currency symbol, and turns it into an int
                post_price = int(post.a.text.strip().replace("$", "").replace(',', '')) 
                post_prices.append(post_price)
                
                if post.find('span', class_ = 'housing') is not None:
                    
                    #if the first element is accidentally square footage
                    if 'ft2' in post.find('span', class_ = 'housing').text.split()[0]:
                        
                        #make bedroom nan
                        bedroom_count = np.nan
                        bedroom_counts.append(bedroom_count)
                        
                        #make sqft the first element
                        sqft = int(post.find('span', class_ = 'housing').text.split()[0][:-3])
                        sqfts.append(sqft)
                        
                    #if the length of the housing details element is more than 2
                    elif len(post.find('span', class_ = 'housing').text.split()) > 2:
                        
                        #therefore element 0 will be bedroom count
                        bedroom_count = post.find('span', class_ = 'housing').text.replace("br", "").split()[0]
                        bedroom_counts.append(bedroom_count)
                        
                        #and sqft will be number 3, so set these here and append
                        sqft = int(post.find('span', class_ = 'housing').text.split()[2][:-3])
                        sqfts.append(sqft)
                        
                    #if there is num bedrooms but no sqft
                    elif len(post.find('span', class_ = 'housing').text.split()) == 2:
                        
                        #therefore element 0 will be bedroom count
                        bedroom_count = post.find('span', class_ = 'housing').text.replace("br", "").split()[0]
                        bedroom_counts.append(bedroom_count)
                        
                        #and sqft will be number 3, so set these here and append
                        sqft = np.nan
                        sqfts.append(sqft)                    
                    
                    else:
                        bedroom_count = np.nan
                        bedroom_counts.append(bedroom_count)
                    
                        sqft = np.nan
                        sqfts.append(sqft)
                    
                #if none of those conditions catch, make bedroom nan, this won't be needed    
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

# Saves Pandas datatable with current datetime in file name
def backup_scrape(data: pd.DataFrame):
    file_name = './backups/{}.csv'.format(datetime.now())
    data.to_csv(file_name)
    print("Backed up as {}".format(file_name))

# Returns the latest backup done from the backups folder
def get_latest_backup() -> pd.DataFrame:
    list_of_files = glob.glob('./backups/*.csv')
    latest_file = max(list_of_files, key=os.path.basename)
    print('Getting latest backup {}'.format(latest_file))
    return pd.read_csv(latest_file)

if __name__ == "__main__":
    scraped_data = get_current_prices()
    backup_scrape(scraped_data)