from bs4 import BeautifulSoup
import html
import json
import requests
import storage


def download_data(steamid):
    resp = requests.get('https://store.steampowered.com/api/appdetails?l=en&appids=%s' % steamid)
    appdetails = json.loads(resp.text)[steamid]
    if appdetails['success']:
        steam_data = appdetails['data']
        resp = requests.get('https://store.steampowered.com/app/%s/' % steamid)
        if '<h2>AI Generated Content Disclosure</h2>' in resp.text:
            steam_data['ai_generated'] = True
        return steam_data
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
            g['Row'] = '%s (%s) [%s]' % (name, release_date, game['data-ds-appid'])
            g['ID'] = game['data-ds-appid']
            search_results.append(g)
    return search_results[:21]


def is_steamid_valid(steamid):
    resp = requests.get('https://steamcommunity.com/app/%s' % steamid)
    if 'Steam Community :: ' in resp.text():
        return True
    return False


def get_suggested_data(steamdata):
    suggestions = []
    if len(steamdata) == 0:
        return suggestions
    if 'name' in steamdata.keys():
        suggestions.append({'Type': 'Name', 'Value': steamdata['name'].strip(), 'Confidence': 95})
    if 'short_description' in steamdata.keys():
        suggestions.append({'Type': 'Description', 'Value': html.unescape(steamdata['short_description'].strip()), 'Confidence': 95})
    if 'website' in steamdata.keys():
        suggestions.append({'Type': 'Homepage', 'Value': steamdata['website'], 'Confidence': 100})
    if 'background_raw' in steamdata.keys():
        suggestions.append({'Type': 'Background', 'Value': steamdata['background_raw'].split('?')[0], 'Confidence': 90})
    if steamdata['is_free']:
        suggestions.append({'Type': 'Meta', 'Value': 'Freely Available', 'Confidence': 100})
    if steamdata['platforms']['windows']:
        suggestions.append({'Type': 'Platform', 'Value': 'Windows', 'Confidence': 100})
    if steamdata['platforms']['mac']:
        suggestions.append({'Type': 'Platform', 'Value': 'Mac', 'Confidence': 100})
    if steamdata['platforms']['linux']:
        suggestions.append({'Type': 'Platform', 'Value': 'Linux', 'Confidence': 100})
    if 'developers' in steamdata.keys():
        for d in steamdata['developers']:
            suggestions.append({'Type': 'Developer', 'Value': d.strip(), 'Confidence': 100})
    if 'publishers' in steamdata.keys():
        for p in steamdata['publishers']:
            suggestions.append({'Type': 'Publisher', 'Value': p.strip(), 'Confidence': 100})
    if 'ai_generated' in steamdata.keys():
        suggestions.append({'Type': 'Meta', 'Value': 'AI-Generated Content', 'Confidence': 100})
    for c in steamdata['categories']:
        suggestions.append({'Type': 'Meta', 'Value': c['description'].strip(), 'Confidence': 100})
    if 'genres' in steamdata.keys():
        for g in steamdata['genres']:
            if g['description'].strip() == 'Early Access':
                suggestions.append({'Type': 'Meta', 'Value': g['description'].strip(), 'Confidence': 100})
            else:
                suggestions.append({'Type': 'Genre', 'Value': g['description'].strip(), 'Confidence': 50})
    for s in steamdata['screenshots']:
        suggestions.append({'Type': 'Screenshot', 'Value': s['path_full'].split('?')[0], 'Confidence': 100})
    m_count = 0
    if 'movies' in steamdata.keys():
        for m in steamdata['movies']:
            suggestions.append({'Type': 'Video', 'Value': m['webm']['max'].split('?')[0].replace('http:', 'https:'), 'Confidence': 90 - m_count})
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
