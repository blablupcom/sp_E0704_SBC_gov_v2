# -*- coding: utf-8 -*-

#### IMPORTS 1.0

import os
import re
import scraperwiki
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup
import requests


#### FUNCTIONS 1.0

def validateFilename(filename):
    filenameregex = '^[a-zA-Z0-9]+_[a-zA-Z0-9]+_[a-zA-Z0-9]+_[0-9][0-9][0-9][0-9]_[0-9QY][0-9]$'
    dateregex = '[0-9][0-9][0-9][0-9]_[0-9QY][0-9]'
    validName = (re.search(filenameregex, filename) != None)
    found = re.search(dateregex, filename)
    if not found:
        return False
    date = found.group(0)
    now = datetime.now()
    year, month = date[:4], date[5:7]
    validYear = (2000 <= int(year) <= now.year)
    if 'Q' in date:
        validMonth = (month in ['Q0', 'Q1', 'Q2', 'Q3', 'Q4'])
    elif 'Y' in date:
        validMonth = (month in ['Y1'])
    else:
        try:
            validMonth = datetime.strptime(date, "%Y_%m") < now
        except:
            return False
    if all([validName, validYear, validMonth]):
        return True


def validateURL(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=20)
        count = 1
        while r.status_code == 500 and count < 4:
            print ("Attempt {0} - Status code: {1}. Retrying.".format(count, r.status_code))
            count += 1
            r = requests.get(url, allow_redirects=True, timeout=20)
        sourceFilename = r.headers.get('Content-Disposition')
        if sourceFilename:
            ext = os.path.splitext(sourceFilename)[1].replace('"', '').replace(';', '').replace(' ', '')
        else:
            ext = os.path.splitext(url)[1]
        validURL = r.status_code == 200
        validFiletype = ext in ['.csv', '.xls', '.xlsx']
        return validURL, validFiletype
    except:
        print ("Error validating URL.")
        return False, False

def validate(filename, file_url):
    validFilename = validateFilename(filename)
    validURL, validFiletype = validateURL(file_url)
    if not validFilename:
        print filename, "*Error: Invalid filename*"
        print file_url
        return False
    if not validURL:
        print filename, "*Error: Invalid URL*"
        print file_url
        return False
    if not validFiletype:
        print filename, "*Error: Invalid filetype*"
        print file_url
        return False
    return True


def convert_mth_strings ( mth_string ):
    month_numbers = {'JAN': '01', 'FEB': '02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09','OCT':'10','NOV':'11','DEC':'12' }
    for k, v in month_numbers.items():
        mth_string = mth_string.replace(k, v)
    return mth_string


#### VARIABLES 1.0

entity_id = "E0704_SBC_gov"
url = "https://www.stockton.gov.uk/stockton-council/good-governance-doing-things-properly/stockton-council-publication-scheme/payments-to-suppliers/"
errors = 0
data = []

#### READ HTML 1.0

html = urllib2.urlopen(url)
soup = BeautifulSoup(html, "lxml")


#### SCRAPE DATA

block = soup.find('div', attrs = 'col-xs-12 col-md-8')
links = block.find_all('a', href = True)
for link in links:
    if '.csv' in link['href']:
        url = 'https://www.stockton.gov.uk' + link['href']
        csvfile = link.text.strip().split('Suppliers')[-1].strip().split('-')[-1].strip()
        if '2011' in link.text.strip().split('Suppliers')[-1].strip().split('-')[0]:
             csvfile = link.text.strip().split('Suppliers')[-1].strip().split('-')[0].strip()
        if 'suppliers ' in csvfile:
            csvfile = csvfile.split('suppliers ')[-1].strip()
        if 'csv V2in CSV' in csvfile:
              csvfile = 'Q3 2010'
        if 'V2'  in csvfile:
              csvfile = 'Q2 2010'
        if '(csv)' in csvfile:
            csvfile = csvfile.split('(csv)')[0].strip()
        if  'csv in CSV Document' in csvfile:
            csvfile = csvfile.split('csv in CSV Document')[0].strip()
        if 'in CSV Document' in csvfile:
            csvfile = csvfile.split('in CSV Document')[0].strip()
        csvMth = csvfile.split(' ')[0][:3]
        csvYr = csvfile.split(' ')[-1]
        if len(csvYr) == 2:
            csvYr = '20'+csvYr

        csvMth = convert_mth_strings(csvMth.upper())
        data.append([csvYr, csvMth, url])


#### STORE DATA 1.0

for row in data:
    csvYr, csvMth, url = row
    filename = entity_id + "_" + csvYr + "_" + csvMth
    todays_date = str(datetime.now())
    file_url = url.strip()

    valid = validate(filename, file_url)

    if valid == True:
        scraperwiki.sqlite.save(unique_keys=['l'], data={"l": file_url, "f": filename, "d": todays_date })
        print filename
    else:
        errors += 1

if errors > 0:
    raise Exception("%d errors occurred during scrape." % errors)


#### EOF

