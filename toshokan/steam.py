from bs4 import BeautifulSoup
import json
import requests


def download_data(steamid):
    resp = requests.get('https://store.steampowered.com/api/appdetails?l=en&appids=%s' % steamid)
    appdetails = json.loads(resp.text)[steamid]
    if appdetails['success']:
        return json.loads(resp.text)["data"]
    else:
        return {}


def search_for_game(name):
    resp = requests.get('https://store.steampowered.com/search/', params={'term': name})
    search_soup = BeautifulSoup(resp.text, 'html.parser')
    result_soup = search_soup.find_all('a', 'search_result_row')
    search_results = []
    for game in result_soup:
        if '/app/' in game['href']:
            g = {}
            g['Name'] = game.find('div', 'search_name').find('span', 'title').text.strip()
            g['Release Date'] = game.find('div', 'search_released').text.strip()
            g['Appid'] = game['data-ds-appid']
            search_results.append(g)
    return search_results[:10]
