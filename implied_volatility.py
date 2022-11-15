import api

from datetime import datetime, timedelta
import numpy as np


FRIDAY = 4
WEEK = 7

RATES = [0.0, 0.0] # [near, next] # Does not seem to have a significant effect on the results, so set to [0.0, 0.0]
MINUTES = [35924, 46394, 43200, 525600] # [near, next, month, year]
YEARS = [0.0683017719979, 0.0882082287626] # [near, next]

def implied_volatility(td_client, symbol):

	today = datetime.today()
	near_timedelta = FRIDAY - today.weekday()
	while near_timedelta < 24:
		near_timedelta += WEEK
	near_date_str = (today + timedelta(near_timedelta)).strftime('%Y-%m-%d')
	opt_chain_near = {
        'symbol': symbol,
        'range': 'ALL',
        'fromDate': near_date_str,
        'toDate': near_date_str
    }
	options_chain_near = api.options_chain(td_client, opt_chain_near)
	next_timedelta = near_timedelta + 7
	next_date_str = (today + timedelta(next_timedelta)).strftime('%Y-%m-%d')
	opt_chain_next = {
        'symbol': symbol,
        'range': 'ALL',
        'fromDate': next_date_str,
        'toDate': next_date_str
    }
	options_chain_next = api.options_chain(td_client, opt_chain_next)
	
	if options_chain_near['status'] == 'SUCCESS' and options_chain_next['status'] == 'SUCCESS':
		near_str = near_date_str + ':' + str(near_timedelta)
		puts_near = options_chain_near['putExpDateMap'][near_str]
		calls_near = options_chain_near['callExpDateMap'][near_str]
		next_str = next_date_str + ':' + str(next_timedelta)
		puts_next = options_chain_next['putExpDateMap'][next_str]
		calls_next = options_chain_next['callExpDateMap'][next_str]
		
		option_data = [[], []]
		for strike in calls_near:
			option_data[0].append([float(strike), float(calls_near[strike][0]['bid']), float(calls_near[strike][0]['ask']), float(puts_near[strike][0]['bid']), float(puts_near[strike][0]['ask'])])
		for strike in calls_next:
			option_data[1].append([float(strike), float(calls_next[strike][0]['bid']), float(calls_next[strike][0]['ask']), float(puts_next[strike][0]['bid']), float(puts_next[strike][0]['ask'])])

		#Step 1: Select the options to be used in the VIX Index calculation
		#Compute F for near term and next term (p6)
		F = [None, None]
		for j in (0,1):
			mindiff = None
			diff = None
			mindiff = None
			Fstrike = None
			Fcall = None
			Fput = None
			for d in option_data[j]:
				diff = abs(0.5 * (d[1] + d[2] - d[3] - d[4]))
				if (mindiff is None or diff < mindiff):
					mindiff = diff
					Fstrike = d[0]
					Fcall = 0.5 * (d[1] + d[2])
					Fput = 0.5 * (d[3] + d[4])
			F[j] = Fstrike + np.exp(RATES[j] * YEARS[j]) * (Fcall - Fput)


		#select the options to be used in the VIX Index calculation (p6,7)
		selectedoptions = [[], []]
		k0 = [None, None]
		for j in (0,1):
			i = 0
			for d in option_data[j]:
				if (d[0] < F[j]): 
					k0[j] = d[0]
					k0i = i
				i += 1

			d = option_data[j][k0i]
			ar = [d[0], 'put/call average', 0.25 * (d[1] + d[2] + d[3] + d[4])]
			selectedoptions[j].append(ar)

			i = k0i - 1
			b = True
			previousbid = None
			while (b and i >= 0):
				d = option_data[j][i]
				if (d[3] > 0):
					ar = [d[0], 'put', 0.5 * (d[3] + d[4])]
					selectedoptions[j].insert(0,ar)
				else:
					if(previousbid == 0): b = False
				previousbid = d[3]
				i -= 1

			i = k0i + 1
			b = True
			previousbid = None
			while (b and i < len(option_data[j])):
				d=option_data[j][i]
				if (d[1] > 0):
					ar = [d[0], 'call', 0.5 * (d[1] + d[2])]
					selectedoptions[j].append(ar)
				else:
					if (previousbid == 0): b = False
				previousbid = d[1]
				i += 1

		#Step 2: Calculate volatility for both near-term and next-term options (p8)
		for j in (0,1):
			i = 0
			for d in selectedoptions[j]:
				if (i == 0): 
					deltak = selectedoptions[j][1][0] - selectedoptions[j][0][0]
				elif (i == len(selectedoptions[j]) - 1):
					deltak = selectedoptions[j][i][0] - selectedoptions[j][i - 1][0]
				else:
					deltak = 0.5 * (selectedoptions[j][i + 1][0] - selectedoptions[j][i - 1][0])
				selectedoptions[j][i].append(deltak * np.exp(RATES[j] * YEARS[j]) * d[2] / (d[0] * d[0]))
				i += 1

		aggregatedcontributionbystrike=[None, None]
		for j in (0,1):
			aggregatedcontributionbystrike[j] = 0
			for d in selectedoptions[j]:
				aggregatedcontributionbystrike[j] += d[3]
			aggregatedcontributionbystrike[j] = 2 * aggregatedcontributionbystrike[j] / YEARS[j]


		sigmasquared=[None, None]
		for j in (0,1):
			sigmasquared[j] = aggregatedcontributionbystrike[j] - (F[j] / k0[j] - 1) * (F[j] / k0[j] - 1) / YEARS[j]

		#Step 3: Calculate the 30-day weighted average of sigmasquared[0] and sigmasquared[1] (p9)
		return np.sqrt(
			(
				(YEARS[0] * sigmasquared[0]) * (MINUTES[1] - MINUTES[2]) / (MINUTES[1] - MINUTES[0])
				+ (YEARS[1] * sigmasquared[1]) * (MINUTES[2] - MINUTES[0]) / (MINUTES[1] - MINUTES[0])
			)
			* MINUTES[3] / MINUTES[2]
		)

	else:

		return None