"""
The Python script to get podcast data from given sites and organize it into .csv table
"""
import xml.etree.ElementTree as ET
from datetime import date
from typing import Tuple, List
from urllib.request import urlopen

import gspread


def get_podcast_data(feed_url: str, last_download: date) -> List[dict]:
	"""
	Function to extract podcast data from RSS feed

	:param feed_url: URL of the RSS feed
	:param last_download: Date when the program run last time
	:return: List of episodes of a podcast with given RSS feed since the last_download
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
				# noinspection PyUnresolvedReferences
				split_date = attr.text.split()
				# noinspection PyUnresolvedReferences
				attr.text = date(int(split_date[3]), dates_map[split_date[2]], int(split_date[1]))
			elif attr.tag == 'duration':
				match len(attr.text.split(':')):
					case 1:
						attr.text = f'0:0:{attr.text}'
					case 2:
						attr.text = f'0:{attr.text}'

			episode[attr.tag] = attr.text
		if episode['pubDate'] < last_download:
			break
		episodes.append(episode)
	return episodes


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


def load_internal_data() -> Tuple[date]:
	"""
	Function to load data from previous downloads. If no file found, assumes it's the first time.

	:return: Tuple of that data
	"""
	try:
		with open("internal_data.txt") as f:
			data = f.readlines()
			data = [line.strip().split() for line in data]
			last_download = date(*[int(i) for i in data[0]])
	except Exception:
		last_download = today
	return last_download,


def save_data(podcasts: dict) -> None:
	"""
	Function to save data to .csv file

	:param podcasts: Podcasts to be saved
	"""
	gc = gspread.service_account(filename='credentials.json')
	with open('output_worksheet_info.txt',encoding='utf-8')as f:
		key = f.readline().strip().split(':')[1]
		sheet = f.readline().strip().split(':')[1]
	sh = gc.open_by_key(key)
	worksheet = sh.worksheet(sheet)
	to_save = []
	for name, episodes in podcasts.items():
		for ep in episodes:
			title = ep['title'].split('|')[0]
			to_save.append([name, title, str(ep['pubDate']), str(today), ep['duration'], '0'])
	worksheet.append_rows(to_save, value_input_option='USER_ENTERED')

	with open("internal_data.txt", 'w') as f:
		f.write(f"{today.year} {today.month} {today.day}")


def main() -> None:
	"""
	Main function of the script
	"""
	podcast_sources = "podcast_sources.csv"

	sources = load_podcast_sources(podcast_sources)
	last_download, = load_internal_data()
	podcasts = {}

	for name, feed_url in sources.items():
		try:
			podcasts[name] = get_podcast_data(feed_url, last_download)
		except Exception:
			print(f"There's a problem with {name} podcast, probably access forbidden")

	save_data(podcasts)


if __name__ == '__main__':
	dates_map = {
		'Jan': 1, 'Feb': 2, 'Mar': 3,
		'Apr': 4, 'May': 5, 'Jun': 6,
		'Jul': 7, 'Aug': 8, 'Sep': 9,
		'Oct':10, 'Nov':11, 'Dec':12
	}
	today = date.today()
	main()
