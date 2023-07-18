from td.client import TDClient
from datetime import datetime
import data

import time

from pprint import pprint

# Enter your account number here
ACCOUNT_NUMBER = ''

# Create a new instance of the client and login
def init():
    keys = data.read_json('apikeys.json')
    td_client = TDClient(client_id= keys['CONSUMER_KEY'], redirect_uri= keys['REDIRECT_URI'], credentials_path= keys['JSON_PATH'])
    td_client.login()
    
    return td_client

def account(td_client):
    account = td_client.get_accounts(account= ACCOUNT_NUMBER, fields= ['positions', 'orders'])['securitiesAccount']
    
    positions = {
        'CASH_EQUIVALENT': {},
        'EQUITY': {},
        'OPTION': {}
    }
    for position in account['positions']:
        if position['instrument']['assetType'] == 'EQUITY':
            positions[position['instrument']['assetType']][position['instrument']['symbol']] = {
                'price': position['marketValue'] / position['longQuantity'],
                'quantity': position['longQuantity']
            }
        elif position['instrument']['assetType'] == 'OPTION':
            positions[position['instrument']['assetType']][position['instrument']['symbol']] = {
                'price': position['marketValue'] / (position['longQuantity'] - position['shortQuantity']),
                'quantity': position['longQuantity'] - position['shortQuantity'],
                'underlyingSymbol': position['instrument']['underlyingSymbol']
            }
        elif position['instrument']['assetType'] == 'CASH_EQUIVALENT':
            positions[position['instrument']['assetType']][position['instrument']['symbol']] = {
                'quantity': position['longQuantity']
            }

    # Wait 500ms
    time.sleep(0.5)

    return positions

def open_markets(td_client):
    markets = {'EQUITY': [], 'OPTION': [], 'FUTURE': [], 'BOND': [], 'FOREX': []}
    market_hours = td_client.get_market_hours(markets= list(markets.keys()), date= datetime.now())
    for i, key in enumerate(markets):
        sub_markets = list(market_hours[key.lower()].keys())
        for j in sub_markets:
            if market_hours[key.lower()][j]['isOpen']:
                markets[key].append(j)

    # Wait 500ms
    time.sleep(0.5)

    return markets

def search_instrument(td_client, symbol):
    instrument = td_client.search_instruments(symbol= symbol, projection= 'symbol-search')

    # Wait 500ms
    time.sleep(0.5)

    return instrument

def quotes(td_client, symbols):
    quotes = td_client.get_quotes(instruments= symbols)

    # Wait 500ms
    time.sleep(0.5)

    return quotes

def daily_prices(td_client, symbol):
    prices = td_client.get_price_history(symbol= symbol, period_type= 'year', period= 1, frequency_type= 'daily', frequency= 1, extended_hours= False)['candles']

    # Wait 500ms
    time.sleep(0.5)

    return prices

def half_hour_prices(td_client, symbol):
    prices = td_client.get_price_history(symbol= symbol, period_type= 'day', period= 10, frequency_type= 'minute', frequency= 30, extended_hours= False)['candles']

    # Wait 500ms
    time.sleep(0.5)

    return prices

def fundamentals(td_client, symbol):
    fundamentals = td_client.search_instruments(symbol= symbol, projection= 'fundamental')[symbol]['fundamental']

    # Wait 500ms
    time.sleep(0.5)

    return fundamentals

def options_chain(td_client, opt_chain= {
        'symbol': 'SPY',
        'contractType': 'CALL',
        'includeQuotes': True,
        'range': 'ITM',
        'fromDate': '2021-11-30',
        'toDate': '2021-12-6'
    }):
    chain = td_client.get_options_chain(opt_chain)

    # Wait 500ms
    time.sleep(0.5)

    return chain

def watchlist(td_client):
    watchlist = td_client.get_watchlist_accounts(account= ACCOUNT_NUMBER)

    # Wait 500ms
    time.sleep(0.5)

    return watchlist

def new_order(td_client, order= {
        'orderType': 'LIMIT',
        'session': 'NORMAL',
        'duration': 'DAY',
        'price': 8.00,
        'orderStrategyType': 'SINGLE',
        'orderLegCollection': [
            {
                'instruction': 'BUY',
                'quantity': 1,
                'instrument': {
                    'symbol': 'AA',
                    'assetType': 'EQUITY'
                }
            }
        ]
    }):
    order_response = td_client.place_order(account= ACCOUNT_NUMBER, order= order)
    pprint(order_response)

    # Wait 500ms
    time.sleep(0.5)

    return order_response['order_id']

def modify_order(td_client, order_id, order= {
        'orderType': 'LIMIT',
        'session': 'NORMAL',
        'duration': 'DAY',
        'price': 8.20,
        'orderStrategyType': 'SINGLE',
        'orderLegCollection': [
            {
                'instruction': 'BUY',
                'quantity': 1,
                'instrument': {
                    'symbol': 'AA',
                    'assetType': 'EQUITY'
                }
            }
        ]
    }):
    
    order_response = td_client.modify_order(account= ACCOUNT_NUMBER, order= order, order_id= order_id)
    pprint(order_response)

    # Wait 500ms
    time.sleep(0.5)

    return order_response['order_id']

def cancel_order(td_client, order_id):
    order_response = td_client.cancel_order(account= ACCOUNT_NUMBER, order_id= order_id)

    # Wait 500ms
    time.sleep(0.5)

    pprint(order_response)
