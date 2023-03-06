"""
The Python script to get podcast data from given sites and organize it into .csv table
"""
import time
import urllib.error
import xml.etree.ElementTree as ET
from datetime import date
from dateutil import parser
from urllib.request import urlopen

import gspread


def get_podcast_data(feed_url: str, start_date: date, end_date: date = date.today()) -> list[dict]:
	"""
	Function to extract podcast data from RSS feed

	:param feed_url: URL of the RSS feed
	:param start_date: The earliest day from which podcasts are to be added
	:param end_date: The latest day from which podcasts are to be added
	:return: List of episodes of a podcast with given RSS feed since the start_date
	"""
	episodes = []
	root = ET.parse(urlopen(feed_url)).getroot()

	for ep in root[0]:
		if ep.tag != 'item':  # It means that we reached episode in XML tree
			continue
		episode = {}
		for attr in ep:
			attr.tag = attr.tag.split("{http://www.itunes.com/dtds/podcast-1.0.dtd}")[-1]
			if attr.tag == "pubDate":
				attr.text = parser.parse(attr.text).date()
			elif attr.tag == 'duration':
				match len(attr.text.split(':')):
					case 1:
						attr.text = f'0:0:{attr.text}'
					case 2:
						attr.text = f'0:{attr.text}'

			episode[attr.tag] = attr.text
		if episode['pubDate'] < start_date:
			break
		elif episode['pubDate'] > end_date:
			continue
		episodes.append(episode)
	return episodes


def load_data() -> tuple[dict, date, date]:
	"""
	Function to load all necessary data

	:return: Tuple of podcast sources, start and end dates
	"""
	podcast_sources = "podcast_sources.csv"
	sources = load_podcast_sources(podcast_sources)
	while True:
		s_date = input("Input start date in yyyy/mm/dd format or press 'Enter' for today")
		try:
			start_date = parser.parse(s_date)
			break
		except ValueError:
			if s_date == '':
				start_date = today
				break
	while True:
		e_date = input("Input end date in yyyy/mm/dd format or press 'Enter' for today")
		try:
			end_date = parser.parse(e_date)
			break
		except Exception:
			if e_date == '':
				end_date = today
				break
	return sources, start_date, end_date


def load_podcast_sources(podcast_sources: str):
	"""
	Function to load podcast sources

	:param podcast_sources: name of the csv file
	:return: list of tuples “podcast_name“, “url“
	"""
	with open(podcast_sources, encoding='utf-8') as f:
		f.readline()
		data = f.readlines()
		data = {el[0]: el[1] for el in [line.strip().split(',') for line in data]}
		return data


def save_data(podcasts: dict) -> None:
	"""
	Function to save data to .csv file

	:param podcasts: Podcasts to be saved
	"""
	gc = gspread.service_account(filename='credentials.json')
	with open('output_worksheet_info.txt', encoding='utf-8') as f:
		key = f.readline().strip().split(':')[1]
		sheet = f.readline().strip().split(':')[1]
		main_sheet_name = f.readline().strip().split(':')[1]
	sh = gc.open_by_key(key)
	worksheet = sh.worksheet(sheet)
	main_sheet = sh.worksheet(main_sheet_name)
	for name, episodes in podcasts.items():
		for ep in episodes:
			title = ep['title'].split('|')[0]
			worksheet.append_row([name, title, str(ep['pubDate']), str(today), ep['duration'], '0'],
			                     value_input_option='USER_ENTERED')
			time.sleep(1)

	while True:
		reply = input("Enter 's' to sort the main list, 'e' to exit the program").lower()
		if reply == 'e':
			return
		if reply == 's':
			break
	var = main_sheet.row_count
	main_sheet.sort((1, 'asc'), (3, 'asc'), (2, 'asc'), range=f'A2:G{var}')


def main() -> None:
	"""
	Main function of the script
	"""
	sources, start_date, end_date = load_data()

	podcasts = {}

	for name, feed_url in sources.items():
		try:
			podcasts[name] = get_podcast_data(feed_url, start_date, end_date)
			print(f'Podcast {name} has been prepared')
		except urllib.error.HTTPError:
			print(f"There's a problem with {name} podcast, probably access forbidden")
		except urllib.error.URLError:
			print(f"There's a problem with {name} podcast, probably there's no internet connection")
			raise Exception("There's no Internet")

	save_data(podcasts)


if __name__ == '__main__':
	today = date.today()  # initiated here to make these two variables global
	main()
