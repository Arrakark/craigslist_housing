# craigslist_housing
A set of Python scripts to record and analyze trends in Craigslist housing.

## What does it do?
There are two main scripts in this repository. **scraper.py** and **report_generator.py**. The other Python files are for reference only.

**scraper.py** scrapes Craigslist postings that are found at a given query URL and saves them in a tinydb format; which is basically a large JSON file; tinydb is a misnomer. This script also saves dated and named backups.

**report_generator.py** creates a PDF with several graphs that show trends in prices, quantity, etc. Some of the outputs included in this PDF look like this:

![Number of active listings over time](/examples/ex1.png)

![Average rental prices](/examples/ex2.png)

![1 br price distributions](/examples/ex3.png)

![Price Regression](/examples/ex4.png)

![Price Regression #2](/examples/ex5.png)

![Prices of added/removed postings](/examples/ex6.png)

You can use the information generated in the report to make better educated decisions when looking for a place to rent. You can also write you own script that loads the tinydb data into a Dataframe, and run your own custom analysis. See **test.py** for an example of that.

## How do I set this up to run if I have a server?
If you have a server that can run Python (I assume you are a normal person and run some sort of Linux distro on your server), then you can run the scraper on your server, and run the report generator on your computer.

1. Clone repo on your server and on your local machine
2. Install pip Python requirements on both machines using `pip install -r requirements.txt` (technically the requirements are not the same on both)
3. Go to Craigslist housing, and set up a search query that includes a postal code location.
4. Copy the URL from the search query and insert it on line 21 in **scraper.py**
5. Set up a cron job on your server that runs **scraper.py**. I suggest once a day maximum.
6. Create a file named *download_db.sh* on your local machine in root dir
7. Write some code in *download_db.sh* that duplicates the file **./db/listings.json** generated on the server, onto your local machine. My script looks like:
`#!/bin/sh
scp vlad@srv1:/home/vlad/craigslist_housing/db/listings.json ./db/listings.json`. For authentication, set up [SSH keys](https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-2)
8. When you want a report, simply run **report_generator.py** on your local machine and look at **craigslist_rental_report.pdf** generated in the main directory

## How do I set this up to run if I don't have a server?
If you don't have a server, that's ok. You just need to remember to run the script **scraper.py** regularly on your computer. Set it up to run automatically somehow, and make sure your computer is on during that time. 

1. Clone repo on your your local machine
2. Install pip Python requirements using `pip install -r requirements.txt`
3. Go to Craigslist housing, and set up a search query that includes a postal code location.
4. Copy the URL from the search query and insert it on line 21 in **scraper.py**
5. Run **scraper.py** regularly on your computer somehow; I suggest once a day
6. When you want a report, simply run **report_generator.py** on your local machine and look at **craigslist_rental_report.pdf** generated in the main directory

## Credits
Special thank you to Ripley Predum, who provided the [starter code](https://github.com/rileypredum/East-Bay-Housing-Web-Scrape).

Hope you use this repo to get yourself a good deal on rental!
