from tinydb import TinyDB, Query
import pandas as pd

db = TinyDB('./db/listings.json')
listings = db.table('listings')
listings = listings.all()
listings = pd.DataFrame(listings)

from matplotlib import figure
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab

def get_max_price(row):
    return max([x['price'] for x in row.snapshots])

plt.figure(figsize=(12, 8))
listings['max_price'] = listings.apply(lambda row: get_max_price(row), axis=1)
# sns.regplot(x='max_price', y='sqft', data=listings.dropna())
# plt.title('Price vs. Square Footage Regression Plot')
# plt.xlabel("Price (CAD)")
# plt.ylabel("Square Feet")
# plt.show()

from tinydb import TinyDB, Query
import pandas as pd

y = [x['lat'] for x in listings['coordinates']]
x = [x['lng'] for x in listings['coordinates']]
z = listings['max_price']
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(x, y, z)
plt.show()