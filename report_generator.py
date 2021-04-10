from tinydb import TinyDB, Query
import pandas as pd
from matplotlib import figure
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
import subprocess
from datetime import datetime
from datetime import timedelta, date
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

def drop_prefix(self, prefix):
    self.columns = self.columns.str.lstrip(prefix)
    return self

pd.core.frame.DataFrame.drop_prefix = drop_prefix

def generate_graph_price_listings(listings: pd.DataFrame):
    listings_1_br = filter_1_br(listings)
    prices = listings_1_br.filter(regex='snapshot_date_').drop_prefix('snapshot_date_')
    prices_aggregate = prices.agg([np.mean, np.std]).transpose()
    #prices_aggregate.plot(kind = "line", y = "mean", legend = False, capsize=4, title = "Average Rental Prices", yerr = "std", color="#ADD8E6")
    prices_aggregate.plot(kind = "line", y = "mean", legend = False, title = "Average Rental Prices", color="#ADD8E6")
    plt.xlabel("Date")
    plt.ylabel("Price (CAD) of 1-bedroom Active Listings")

def generate_graph_num_listings(listings: pd.DataFrame):
    listings_1_br = filter_1_br(listings)
    prices = listings_1_br.filter(regex='snapshot_date_').drop_prefix('snapshot_date_')
    postings = prices.count()
    postings.plot(kind = "line",title = "Number of Active Listings", color="#ADD8E6")
    plt.xlabel("Date")
    plt.ylabel("Number of Active 1-bedroom Listings")


def generate_graph_new_removed_listings(listings: pd.DataFrame):
    prices = listings.filter(regex='snapshot_date_').drop_prefix('snapshot_date_')
    dates = []
    number_removed = []
    number_added = []
    for ind_col, column in enumerate(prices.columns):
        if ind_col == 0:
            break
        for ind_row, row in enumerate(prices.index):
            prices[ind]
    postings.plot(kind = "line",title = "Number of Active Listings", color="#ADD8E6")
    plt.xlabel("Date")
    plt.ylabel("Number of Added or Removed Listings")

def get_first_seen(listings: pd.DataFrame):
    #returns the first time any posting has been recorded
    return pd.to_datetime(listings['first_seen'].min()).date()

def get_last_seen(listings: pd.DataFrame):
    #returns the latest time any posting has been recorded
    return pd.to_datetime(listings['last_seen'].max()).date()

def modify_listings(listings: pd.DataFrame):
    #modifies listings table with various parameters which are useful for when it comes time to make charts
    listings['first_seen'] = listings.apply(lambda row: get_data_first_seen(row), axis=1)
    listings['last_seen'] = listings.apply(lambda row: get_data_last_seen(row), axis=1)
    first_seen_date = get_first_seen(listings)
    last_seen_date = get_last_seen(listings)
    prices = listings.apply(lambda row: get_price_on_each_day(row, first_seen_date, last_seen_date), axis=1)
    listings = listings.join(prices, lsuffix='_caller', rsuffix='_other')
    return listings

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)+1):
        yield start_date + timedelta(n)

def get_price_on_each_day(row,start_date, end_date):
    dates = []
    prices = []
    for single_date in daterange(start_date, end_date):
        price = None
        for snapshot in row.snapshots:
            if pd.to_datetime(snapshot['timestamp']).date() == single_date:
                #found date, add the price to prices
                price = snapshot['price']
                break
        prices.append(price)
        dates.append("snapshot_date_"+str(single_date))
    return pd.Series(prices, index =dates)

def get_data_first_seen(row):
    return min([x['timestamp'] for x in row.snapshots])

def get_data_last_seen(row):
    return max([x['timestamp'] for x in row.snapshots])

def get_dataframe():
    # loads from the file the database of listings and timestamped prices
    db = TinyDB('./db/listings.json')
    listings = db.table('listings')
    listings = listings.all()
    return pd.DataFrame(listings)

def update_database():
    rc = subprocess.call("./download_db.sh")

def save_and_close(pdf):
    pdf.savefig()
    plt.close()

def filter_1_br(listings):
    return listings[listings['number_bedrooms'] == 1.0]


if __name__ == "__main__":
    #update_database()
    data = get_dataframe()
    data = modify_listings(data)

    with PdfPages('craigslist_rental_report.pdf') as pdf:
        generate_graph_num_listings(data)
        save_and_close(pdf)
        generate_graph_price_listings(data)
        save_and_close(pdf)
        #generate_graph_new_removed_listings(data)
        #save_and_close(pdf)
