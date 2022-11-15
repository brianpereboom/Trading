from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import data
import requests
import lxml.html as lh

MATURITY = {'month': 30, 'year': 365}

MONTHS = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12'
}

def firefox_html(browser, json_input):
    browser.get(json_input['URL'])
    header = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, json_input['Header']))
    )
    body = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, json_input['Body']))
    )
    return (header.text, body.text)

def sort(X, Y):
    sort = False
    while not sort:
        sort = True
        for (i, x) in enumerate(X[:-1]):
            if x > X[i + 1]:
                X[i] = X[i + 1]
                X[i + 1] = x
                y = Y[i]
                Y[i] = Y[i + 1]
                Y[i + 1] = y
                sort = False
    return {'EXPIRATION': X, 'VIX': Y}

def term_structure(browser, term_structure_json):

    (header, body) = firefox_html(browser, term_structure_json)

    columns = []
    while '\n' in header:
        found = header.find('\n')
        columns.append(header[0:found])
        header = header[found + 1:]
    columns.append(header)
    expirations = []
    vix_terms = []

    column = 0
    while '\n' in body:
        found = body.find('\n')
        elem = body[0 : found]
        if columns[column] == 'Expiration Date':
            expirations.append(elem[7:] + '-' + MONTHS[elem[3:6]] + '-' + elem[:2])
        elif columns[column] == 'VIX':
            vix_terms.append(float(elem))
        body = body[found + 1:]
        column += 1
        column %= len(columns)
    if columns[column] == 'Expiration Date':
        expirations.append(elem[7:] + '-' + MONTHS[elem[3:6]] + '-' + elem[:2])
    elif columns[column] == 'VIX':
        vix_terms.append(float(body))

    table = sort(expirations, vix_terms)

    return table

def futures(browser, futures_json):

    vix = None

    while vix == None:
        try:
            (header, body) = firefox_html(browser, futures_json)

            columns = []
            while ' ' in header:
                found = header.find(' ')
                columns.append(header[0:found])
                header = header[found + 1:]
            columns.append(header)

            column = 0
            while '\n' in body:
                found = body.find('\n')
                elem = body[0 : found]
                if vix == None and columns[column] == 'LAST':
                    vix = float(elem)
                    break
                body = body[found + 1:]
                column += 1
        except:
            vix = float(input("VIX: "))

    return vix

def vix_data():

    vix_json = data.read_json('vix.json')

    # Open Firefox and minimize window
    browser = webdriver.Firefox()
    browser.minimize_window()

    # Get term structure
    term_structure_table = term_structure(browser, vix_json['Term Structure'])

    # Get futures
    vix = futures(browser, vix_json['Futures'])

    # Close Firefox
    browser.quit()

    return (vix, term_structure_table)

def bank_rates():
    # Create a handle, page, to handle the contents of the website
    page = requests.get('http://www.worldgovernmentbonds.com/central-bank-rates/')
    # Store the contents of the website under doc
    doc = lh.fromstring(page.content)
    # Parse data that are stored between <tr>..</tr> of HTML
    tr_elements = doc.xpath('//tr')
    # Create empty table with header
    bank_rates = {}
    # Populate table
    for j in range(len(tr_elements)):
        # T is our j'th row
        T = tr_elements[j]
        
        # If row is not of size 10, the //tr data is not from our table
        if len(T) == 5:
            # i is the index of our column
            i = 0
            
            # Iterate through each element of the row
            country = ""
            for t in T.iterchildren():
                if i == 1:
                    data = t.text_content().replace(' ', '').replace('\n', '').replace('\t', '').replace('(*)', '')
                    for j in range(1, len(data)):
                        if data[j].isupper() and data[j - 1] != ' ':
                            data = data[:j] + ' ' + data[j:]
                    country = data
                elif i == 2:
                    data = t.text_content().replace('%', '')
                    # Convert any numerical value to floats
                    try:
                        data = 0.01 * float(data)
                    except:
                        pass
                    bank_rates[country] = data
                # Increment i for the next column
                i += 1
                
    return bank_rates

def yield_curve(bank_rate, url):
    # Create a handle, page, to handle the contents of the website
    page = requests.get(url)
    # Store the contents of the website under doc
    doc = lh.fromstring(page.content)
    # Parse data that are stored between <tr>..</tr> of HTML
    tr_elements = doc.xpath('//tr')
    # Create empty table with header
    table = {'Maturity': [1], 'Yield': [bank_rate]}
    # Populate table
    for j in range(0, len(tr_elements)):

        # T is our j'th row
        T = tr_elements[j]
        
        # If row is not of size 10, the //tr data is not from our table
        if len(T) == 10:
            # i is the index of our column
            i = 0
            
            # Iterate through each element of the row
            for t in T.iterchildren():
                if i == 1:
                    data = t.text_content().replace(' ', '').replace('\n', '').replace('s', '')
                    days = 0
                    if data.find('month') != -1:
                        days = MATURITY['month']
                        days *= int(data.replace('month', ''))
                    elif data.find('year') != -1:
                        days = MATURITY['year']
                        days *= int(data.replace('year', ''))
                    # Append the data to the empty list of the i'th column
                    table['Maturity'].append(days)
                elif i == 2:
                    data = t.text_content().replace('%', '')
                    # Convert numerical value to float
                    data = 0.01 * float(data)
                    # Append the data to the empty list of the i'th column
                    table['Yield'].append(data)
                # Increment i for the next column
                i += 1
    return table