import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

class CountyNotFound(Exception):
    pass

def parse_results(results):
    categories=[]
    figures=[]
    for i in results.split('\n'):
        if '%' in i:
            if re.search('[0-9]',i):
                figures.append(i)
        else:
            categories.append(i)
    # Check that num categories equals num figures
    if len(categories)!=len(figures):
        raise ValueError('Length mismatch: Categories list has '+str(len(categories))+' elements, Figures list has '+str(len(figures))+' elements')
    return [categories,figures]

def fetch_county_vax(county):
    edge_options=Options()
    edge_options.headless=True
    driver_path='/users/ericphillips/personal_ds_projects/msedgedriver'
    driver=webdriver.Edge(driver_path,options=edge_options)
    # Go to webpage
    driver.get('https://covid19.ca.gov/vaccines/')
    # Wait for search bar to load
    WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'//cagov-county-search/div/form/div/div/div/input')))
    # Find search bar and enter county
    search_bar=driver.find_element('xpath','//cagov-county-search/div/form/div/div/div/input')
    search_bar.send_keys(county)
    try:
        # Check that result matches input
        found_county=driver.find_element('xpath','//mark').get_attribute('innerHTML')
    except NoSuchElementException as e:
        driver.close()
        raise CountyNotFound('County not found on CDPH vaccination website')
    # Select county
    if county==found_county:
        search_bar.send_keys(Keys.RETURN)
        ## Extract data
        data={}
        # Iterate through available data types (race/ethnicity, age, gender)
        buttons=driver.find_elements('xpath','//cagov-chart-filter-buttons-vaccines/div/button')
        for button in buttons:
            # Select data type
            data_type=button.get_attribute('innerHTML')
            driver.execute_script('arguments[0].click();',button)
            #button.click()
            # Find chart
            chart=driver.find_element('xpath', '//*[starts-with(name(),"cagov-chart-vaccination-groups")][@class="chart"]')
            holder=chart.find_element('xpath','.//*/div[@class="svg-holder"]')
            # Get results
            results = holder.find_element('xpath', './*').text
            # Get when data was updated
            updated_elem = chart.find_elements('xpath', './/*/div[@class="row"]')[-1]
            updated_text=updated_elem.text.split('.')[0]
            # Parse and store results
            data[data_type] = [parse_results(results),updated_text]
        driver.close()
        return data
    else:
        driver.close()
        raise CountyNotFound('Incorrect county found')

