import pandas as pd
import csv
from pprint import pprint

def SP500():
    try:
        table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        td = table[0]
        td.to_csv("S&P500.csv", columns= ['Symbol', 'Security', 'GICS Sector'])
        symbols = td['Symbol']
        sectors = td['GICS Sector']
        sp500 = {}
        for (symbol, sector) in zip(symbols, sectors):
            sp500[symbol] = sector
        return sp500
    except Exception:
        pprint("Alert: S&P 500 failed to update")
        with open("S&P500.csv") as File:
            Line_Reader = csv.reader(File)
            sp500 = {}
            for row in Line_Reader:
                sp500[row[1]] = row[3]
        return sp500

def SP600():
    try:
        table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_600_companies')
        td = table[1]
        td.to_csv("S&P600.csv", columns= ['Ticker symbol', 'Company', 'GICS Sector'])
        symbols = td['Ticker symbol']
        sectors = td['GICS Sector']
        sp600 = {}
        for (symbol, sector) in zip(symbols, sectors):
            sp600[symbol] = sector
        return sp600
    except Exception:
        pprint("Alert: S&P 600 failed to update")
        with open("S&P600.csv") as File:
            Line_Reader = csv.reader(File)
            sp600 = {}
            for row in Line_Reader:
                sp600[row[1]] = row[3]
        return sp600