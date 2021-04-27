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

def generate_graph_correlation(listings, title=""):
    #plt.figure(figsize=(12, 8))
    sns.regplot(x='sqft', y='price', data=listings.dropna());
    plt.title(title);
    plt.ylabel("Price (CAD)");
    plt.xlabel("Square Feet");

def generate_table_corr(listings):
    listings_without_snapshots = listings[listings.columns.drop(list(listings.filter(regex='snapshot_date_')))]
    listings_without_snapshots = listings_without_snapshots.dropna()
    generate_table(listings_without_snapshots.corr().round(2))

def generate_table(data):
    fig, ax = plt.subplots()
    table = pd.plotting.table(ax, data, rowLabels=None, colLabels=None)
    table.set_fontsize(14)
    #table.scale(1,4)
    ax.axis('off')

def add_latest_prices(listings):
    prices = listings.filter(regex='snapshot_date_').drop_prefix('snapshot_date_')
    latest_prices = prices.iloc[:, -1]
    latest_prices.name = "price"
    return listings.join(latest_prices)

def generate_graph_latest_distribution_of_prices(listings, title=""):
    plt.figure()
    binwidth = 100
    y = listings['price']
    plt.hist(y, edgecolor='black', bins=range(int(y.min()), int(y.max() + binwidth), binwidth));
    plt.xlabel("Price")
    plt.ylabel('Count')
    plt.title(title);

def price_per_square_foot(listings, title=""):
    sns.scatterplot(x='sqft', y='price', hue='number_bedrooms', palette='summer', x_jitter=True, y_jitter=True, s=125, data=listings.dropna())
    plt.ylabel("Price")
    plt.xlabel("Square Footage");
    plt.title(title)

def generate_graph_price_listings(listings: pd.DataFrame, show_std=False, title=""):
    prices = listings.filter(regex='snapshot_date_').drop_prefix('snapshot_date_')
    prices_aggregate = prices.agg([np.mean, np.std]).transpose()
    if show_std is True: 
        prices_aggregate.plot(kind = "line", y = "mean", legend = False, capsize=4, title = title, yerr = "std", color="#ADD8E6")
    else:
        prices_aggregate.plot(kind = "line", y = "mean", legend = False, title = title)
    plt.xlabel("Date")
    plt.ylabel("Price (CAD) of Active Listings")

def generate_graph_num_listings(listings: pd.DataFrame, title=""):
    prices = listings.filter(regex='snapshot_date_').drop_prefix('snapshot_date_')
    postings = prices.count()
    postings.plot(kind = "line",title=title)
    plt.xlabel("Date")
    plt.ylabel("Number of Active Listings")


def generate_graph_new_removed_listings(listings: pd.DataFrame,title=""):
    prices = listings.filter(regex='snapshot_date_').drop_prefix('snapshot_date_')
    start_date = get_first_seen(listings) + timedelta(1)
    end_date = get_last_seen(listings)
    for date in daterange(start_date, end_date):
        #for each valid date
        day_ago = str(date - timedelta(1))
        date = str(date)
        conditions = [
            ~np.isnan(prices[date]) & np.isnan(prices[day_ago]), 
            np.isnan(prices[date]) & ~np.isnan(prices[day_ago])
        ]
        choices = [1, -1]
        output = np.select(conditions, choices, default=0)
        prices['added_'+date] = output
    prices = prices.filter(regex='added_').drop_prefix('added_')
    prices = prices.apply(pd.value_counts)
    prices = prices.drop(0)
    prices = prices.transpose()
    prices.columns = ["Removed Listings", "Added Listings"]
    prices.plot(kind = "bar",title = title)
    plt.xlabel("Date")
    plt.ylabel("Change in Number Listings")


def generate_graph_new_removed_listings_price(listings: pd.DataFrame, title=""):
    prices = listings.filter(regex='snapshot_date_').drop_prefix('snapshot_date_')
    start_date = get_first_seen(listings) + timedelta(1)
    end_date = get_last_seen(listings)
    for date in daterange(start_date, end_date):
        #for each valid date
        day_ago = str(date - timedelta(1))
        date = str(date)
        conditions = [
            ~np.isnan(prices[date]) & np.isnan(prices[day_ago]), 
            np.isnan(prices[date]) & ~np.isnan(prices[day_ago])
        ]
        #conditions are: added today, removed today
        choices = [prices[date], -prices[day_ago]]
        output = np.select(conditions, choices, default=np.nan)
        prices['added_'+date] = output
    prices = prices.filter(regex='added_').drop_prefix('added_')
    prices_added = prices.where(lambda x: (x > 0)).mean()
    prices_removed = prices.where(lambda x: (x < 0)).mean() * -1
    prices = pd.concat([prices_removed, prices_added], axis=1)
    prices.columns = ["Removed Listings", "Added Listings"]
    prices.plot(kind = "bar",title = title)
    plt.xlabel("Date")
    plt.ylabel(title)

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
    listings = add_latest_prices(listings)
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
    plt.tight_layout()
    pdf.savefig()
    plt.close()

def filter_1_br(listings):
    return listings[listings['number_bedrooms'] == 1.0]


if __name__ == "__main__":
    update_database()
    data = get_dataframe()
    data = modify_listings(data)
    #data = filter_1_br(data)

    params = {'legend.fontsize': 'large',
         'figure.figsize': (8, 5),
         'axes.labelsize': 'large',
         'axes.titlesize':'large',
         'xtick.labelsize':'large',
         'ytick.labelsize':'large'}
    pylab.rcParams.update(params)

    with PdfPages('craigslist_rental_report.pdf') as pdf:
        generate_graph_num_listings(data, title="Number of Active Listings")
        plt.xticks(rotation=90)
        save_and_close(pdf)
        generate_graph_price_listings(data, show_std=False, title="Average Rental Prices")
        plt.xticks(rotation=90)
        save_and_close(pdf)
        plt.xticks(rotation=0)
        generate_graph_new_removed_listings(data, title="Number of Added/Removed Listings")
        save_and_close(pdf)
        generate_graph_new_removed_listings_price(data, title="Average Price of Added/Removed Listings")
        save_and_close(pdf)
        generate_graph_latest_distribution_of_prices(data, title="Latest Distribution of Prices")
        save_and_close(pdf)
        price_per_square_foot(data, title="Square Footage  vs. Price Colored by Number of Bedrooms")
        save_and_close(pdf)
        generate_graph_correlation(data, title='Square Footage vs. Price Regression Plot')
        save_and_close(pdf)
        #generate_table_corr(data)
        #save_and_close(pdf)

        #do the same thing but with 1br data and with propper labels
        data = filter_1_br(data)
        generate_graph_num_listings(data, title="Number of Active 1br Listings")
        plt.xticks(rotation=90)
        save_and_close(pdf)
        generate_graph_price_listings(data, show_std=False, title="Average Rental Prices for 1br")
        plt.xticks(rotation=90)
        save_and_close(pdf)
        plt.xticks(rotation=0)
        generate_graph_new_removed_listings(data, title="Number of Added/Removed 1br Listings")
        save_and_close(pdf)
        generate_graph_new_removed_listings_price(data, title="Average Price of Added/Removed 1br Listings")
        save_and_close(pdf)
        generate_graph_latest_distribution_of_prices(data, title="Latest Distribution of 1br Prices")
        save_and_close(pdf)
        price_per_square_foot(data, title="Square Footage vs. Price for 1br")
        save_and_close(pdf)
        generate_graph_correlation(data, title='Square Footage vs. Price Regression Plot for 1br')
        save_and_close(pdf)
        #generate_table_corr(data)
        #save_and_close(pdf)

