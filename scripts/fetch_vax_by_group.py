import time
from datetime import datetime
import pandas as pd
import csv
import re
from selenium import webdriver
#from selenium.webdriver.edge.options import Options
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

driver_path='/opt/homebrew/Caskroom/chromedriver/89.0.4389.23/chromedriver'
#driver_path = '/users/ericphillips/personal_ds_projects/msedgedriver'


class CountyNotFound(Exception):
    pass


def parse_results(results):
    parsed_result = {}
    for i in results.split('\n'):
        if '%' in i:
            if re.search('[0-9]', i):
                figure = i
        else:
            category = i
            parsed_result[category] = figure
    return parsed_result


def process_date(date_str):
    updated_date = date_str.split('Updated')[1].split('with')[0].strip()
    data_date = date_str.split('from')[1].strip()
    updated_date_formatted = datetime.strptime(updated_date, '%B %d, %Y').strftime('%Y-%m-%d')
    data_date_formatted = datetime.strptime(data_date, '%B %d, %Y').strftime('%Y-%m-%d')
    return updated_date_formatted, data_date_formatted


def fetch_county_vax(county):
    #edge_options = Options()
    #edge_options.headless = True
    #driver = webdriver.Edge(driver_path, options=edge_options)
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    driver=webdriver.Chrome(driver_path,options=chrome_options)
    # Go to webpage
    driver.get('https://covid19.ca.gov/vaccines/')
    # Wait for search bar to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//cagov-county-search/div/form/div/div/div/input')))
    # Find search bar and enter county
    search_bar = driver.find_element('xpath', '//cagov-county-search/div/form/div/div/div/input')
    search_bar.send_keys(county)
    try:
        # Check that result matches input
        found_county = driver.find_element('xpath', '//mark').get_attribute('innerHTML')
    except NoSuchElementException as e:
        driver.close()
        raise CountyNotFound('County not found on CDPH vaccination website')
    # Select county
    if county == found_county:
        search_bar.send_keys(Keys.RETURN)
        ## Extract data
        data = {}
        # Iterate through available data types (race/ethnicity, age, gender)
        buttons = driver.find_elements('xpath', '//cagov-chart-filter-buttons-vaccines/div/button')
        for button in buttons:
            # Select data type
            data_type = button.get_attribute('innerHTML')
            driver.execute_script('arguments[0].click();', button)
            # Find chart
            chart = driver.find_element('xpath',
                                        '//*[starts-with(name(),"cagov-chart-vaccination-groups")][@class="chart"]')
            holder = chart.find_element('xpath', './/*/div[@class="svg-holder"]')
            # Get results
            results = holder.find_element('xpath', './*').text
            # Get when data was updated
            updated_elem = chart.find_elements('xpath', './/*/div[@class="row"]')[-1]
            updated_text = updated_elem.text.split('.')[0]
            # Parse and store results/date
            formatted_result = parse_results(results)
            formatted_result['County'] = county
            updated_date, data_date = process_date(updated_text)
            formatted_result['Date Updated'] = updated_date
            formatted_result['Date Data'] = data_date
            formatted_result['Date Scraped'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data[data_type] = formatted_result
        driver.close()
        return data
    else:
        driver.close()
        raise CountyNotFound('Incorrect county found')


def fetch_vax_by_group():
    # Get list of all counties in CA
    counties = pd.read_html('https://en.wikipedia.org/wiki/List_of_counties_in_California')[1]['County'].str.replace(
        'County', '').str.strip().values
    current_time = datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
    with open('data/raw/county_vaccine_data/race_ethnicity_by_county_' + current_time + '.csv', 'w') as race_csv, open(
            'data/raw/county_vaccine_data/age_by_county_' + current_time + '.csv', 'w') as age_csv, open(
            'data/raw/county_vaccine_data/gender_by_county_' + current_time + '.csv', 'w') as gender_csv:
        # Create dict with writer objects
        writers = {'Race and ethnicity': race_csv, 'Age': age_csv, 'Gender': gender_csv}
        header_flag = False
        counter = 0
        for county in counties:
            # Fetch county data
            county_data = fetch_county_vax(county)
            for key in county_data.keys():
                writer = csv.DictWriter(writers[key], fieldnames=county_data[key].keys())
                # Write columns only once per CSV
                if not header_flag:
                    writer.writeheader()
                writer.writerow(county_data[key])
            header_flag = True
            counter += 1
            print('Fetched ' + str(counter) + ' of ' + str(len(counties)) + ' counties!')

# Fetch data
fetch_vax_by_group()
