from tinydb import TinyDB, Query
import pandas as pd
from matplotlib import figure
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
import subprocess

def generate_graph_num_listings(data: pd.DataFrame):
    data.head(10)
    return 0


def get_dataframe():
    # loads from the file the database of listings and timestamped prices
    db = TinyDB('./db/listings.json')
    listings = db.table('listings')
    listings = listings.all()
    return pd.DataFrame(listings)

def update_database():
    rc = subprocess.call("./download_db.sh")

if __name__ == "__main__":
    update_database()
    data = get_dataframe()
    generate_graph_num_listings(data)