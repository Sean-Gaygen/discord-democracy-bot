import requests
import json
import time

class RecognizedRegion:

	def __init__(self, x, y):

		self.region_name = x
		self.is_recognized = y

auth_key = {'auth_key': '|Vav?q&O>b{5Gp?>Ng4jZJ-pBmvF|iSLewwr~.zOSv02N23,3mbJA5Nb_I1o#O`'}
#
# payload = RecognizedRegion('Schmuckserver'.lower().strip(), True)
#
# print(requests.post('http://127.0.0.1:8000/voting/add_region', json=payload.__dict__ | auth_key).status_code)

with open('countries.txt') as f:

	for country in f.readlines():

		url = 'http://127.0.0.1:8000/voting/add_region'

		payload = RecognizedRegion(country.lower().strip(), True)

		print(requests.post(url, json=payload.__dict__ | auth_key).status_code)

		time.sleep(0.1)