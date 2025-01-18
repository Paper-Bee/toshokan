import config
from duckduckgo_search import DDGS
import json
import requests


def get_game_info(game_id):
    user_config = config.get_config()
    resp = requests.get('https://api.mobygames.com/v1/games', params = {'id': game_id, 'api_key': user_config['MobyGames']['api_key']})
    mobygames_details = json.loads(resp.text)['games'][0]
    return mobygames_details


def search_for_game(name):
    resp = DDGS().text('%s site:mobygames.com' % name, max_results=40)
    search_results = []
    for i in range(0, len(resp)):
        g = {}
        g['Row'] = resp[i]['title']
        g['ID'] = resp[i]['href'].split('/game/')[-1].split('/')[0]
        # Skip non-game pages
        if '/game/' not in resp[i]['href']:
            continue
        # Skip non-main game pages
        if '/reviews/' in resp[i]['href']:
            continue
        if '/screenshots/' in resp[i]['href']:
            continue
        if '/specs/' in resp[i]['href']:
            continue
        search_results.append(g)
    return search_results[:21]


def get_suggested_data(mobygames_data):
    suggestions = []
    if 'title' in mobygames_data.keys():
        suggestions.append({'Type': 'Name', 'Value': mobygames_data['title'], 'Confidence': 70})
    if 'alternate_titles' in mobygames_data.keys():
        for a in mobygames_data['alternate_titles']:
            suggestions.append({'Type': 'Alias', 'Value': a['title'], 'Confidence': 50})
    if 'genres' in mobygames_data.keys():
        for g in mobygames_data['genres']:
            if g['genre_category'] == 'Basic Genres':
                suggestions.append({'Type': 'Genre', 'Value': g['genre_name'], 'Confidence': 80})
            else:
                suggestions.append({'Type': 'Tag', 'Value': g['genre_name'], 'Confidence': 80})
    if 'platforms' in mobygames_data.keys():
        for p in mobygames_data['platforms']:
            suggestions.append({'Type': 'Platform', 'Value': p['platform_name'], 'Confidence': 40})
    if 'sample_cover' in mobygames_data.keys():
        suggestions.append({'Type': 'Cover', 'Value': mobygames_data['sample_cover']['image'], 'Confidence': 70})
    if 'sample_screenshots' in mobygames_data.keys():
        for s in mobygames_data['sample_screenshots']:
            suggestions.append({'Type': 'Screenshot', 'Value': s['image'], 'Confidence': 70})

    return suggestions
