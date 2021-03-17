import pandas as pd
import urllib
import time

# Get list of all counties in CA
counties = pd.read_html('https://en.wikipedia.org/wiki/List_of_counties_in_California')[1]['County']
# Format county names
county_urls = (counties.str.replace(' ', '').str.strip().str.lower() + 'california').values
county_filenames = (counties.str.replace(' ', '_').str.strip().str.lower()).values
for i in range(len(counties)):
    # Get county name for URL/filename
    county_url = county_urls[i]
    county_filename = county_filenames[i]
    # Download data
    base_url = 'https://www.census.gov/quickfacts/fact/csv/'
    urllib.request.urlretrieve(base_url + county_url, 'datasets/county_demographics/' + county_filename + '.csv')
    print('Fetched ' + str(i + 1) + ' of ' + str(len(counties)) + ' counties!')
    time.sleep(0.5)
