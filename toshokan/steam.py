from bs4 import BeautifulSoup
import json
import requests
import storage


def download_data(steamid):
    resp = requests.get('https://store.steampowered.com/api/appdetails?l=en&appids=%s' % steamid)
    appdetails = json.loads(resp.text)[steamid]
    if appdetails['success']:
        return appdetails['data']
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
            name = game.find('div', 'search_name').find('span', 'title').text.strip()
            release_date = game.find('div', 'search_released').text.strip()
            g['Row'] = '%s (%s)' % (name, release_date)
            g['ID'] = game['data-ds-appid']
            search_results.append(g)
    return search_results[:10]


def is_steamid_valid(steamid):
    resp = requests.get('https://steamcommunity.com/app/%s' % steamid)
    if 'Steam Community :: ' in resp.text():
        return True
    return False


def get_suggested_data(steamdata):
    suggestions = []
    if steamdata['is_free']:
        suggestions.append({'Type': 'Meta', 'Value': 'Freely Available', 'Confidence': 100})
    if steamdata['platforms']['windows']:
        suggestions.append({'Type': 'Platform', 'Value': 'Windows', 'Confidence': 100})
    if steamdata['platforms']['mac']:
        suggestions.append({'Type': 'Platform', 'Value': 'Mac', 'Confidence': 100})
    if steamdata['platforms']['linux']:
        suggestions.append({'Type': 'Platform', 'Value': 'Linux', 'Confidence': 100})
    for c in steamdata['categories']:
        suggestions.append({'Type': 'Meta', 'Value': c['description'], 'Confidence': 100})
    for g in steamdata['genres']:
        suggestions.append({'Type': 'Genre', 'Value': g['description'], 'Confidence': 50})
    for s in steamdata['screenshots']:
        suggestions.append({'Type': 'Screenshot', 'Value': s['path_full'].split('?')[0], 'Confidence': 100})
    m_count = 0
    for m in steamdata['movies']:
        suggestions.append({'Type': 'Video', 'Value': m['webm']['max'].split('?')[0], 'Confidence': 90 - m_count})
        m_count += 1
    if steamdata['release_date']['date'][-4:].isnumeric():
        # Steam dates are often inaccurate for re-releases as developers try to make them seem new
        suggestions.append({'Type': 'Year', 'Value': steamdata['release_date']['date'][-4:], 'Confidence': 80})

    # Let's find a cover!
    best_cover_confidence = 0
    best_cover_url = ''
    try:
        temp_cover_2x_url = 'https://steamcdn-a.akamaihd.net/steam/apps/%s/library_600x900_2x.jpg' % steamdata['steam_appid']
        storage.download_image(temp_cover_2x_url)
        best_cover_url = temp_cover_2x_url
        best_cover_confidence = 100
    except Exception as e:
        print(e)
    # If the 2x doesn't exist, try a regular cover
    if best_cover_confidence == 0:
        try:
            temp_cover_url = 'https://steamcdn-a.akamaihd.net/steam/apps/%s/library_600x900.jpg' % steamdata['steam_appid']
            storage.download_image(temp_cover_url)
            best_cover_url = temp_cover_url
            best_cover_confidence = 100
        except Exception as e:
            print(e)
    # If no cover exists, go for the header!
    if best_cover_confidence == 0:
        best_cover_url = 'https://steamcdn-a.akamaihd.net/steam/apps/%s/header.jpg' % steamdata['steam_appid']
        best_cover_confidence = 60
    if best_cover_confidence != 0:
        suggestions.append({'Type': 'Cover', 'Value': best_cover_url, 'Confidence': best_cover_confidence})

    return suggestions
