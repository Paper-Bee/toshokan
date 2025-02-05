import config
import json
import requests

igdb_categories = {
    0: 'main_game',
    1: 'dlc_addon',
    2: 'expansion',
    3: 'bundle',
    4: 'standalone_expansion',
    5: 'mod',
    6: 'episode',
    7: 'season',
    8: 'remake',
    9: 'remaster',
    10: 'expanded_game',
    11: 'port',
    12: 'fork',
    13: 'pack',
    14: 'update',
}

igdb_statuses = {
    0: 'released',
    2: 'alpha',
    3: 'beta',
    4: 'early_access',
    5: 'offline',
    6: 'cancelled',
    7: 'rumored',
    8: 'delisted',
}


def get_access_details(regen=False):
    user_config = config.get_config()
    if regen or user_config['IGDB']['access_token'] == '':
        resp = requests.post('https://id.twitch.tv/oauth2/token', data={'client_id': user_config['IGDB']['client_id'], 'client_secret': user_config['IGDB']['client_secret'], 'grant_type': 'client_credentials'})
        access_token = json.loads(resp.text)['access_token']
        config.set_option(user_config, 'IGDB', 'access_token', access_token)
        config.save_config(user_config)
        return user_config['IGDB']['client_id'], access_token
    else:
        return user_config['IGDB']['client_id'], user_config['IGDB']['access_token']


def get_full_game_info(igdb_id, regen=False):
    client_id, access_token = get_access_details(regen=regen)
    resp = requests.post('https://api.igdb.com/v4/games', **{'headers': {'Client-ID': client_id, 'Authorization': 'Bearer %s' % access_token}, 'data': 'fields alternative_names.name, alternative_names.comment, artworks.image_id, artworks.url, category, collections.name, collections.type.name, cover.image_id, cover.url, franchises.name, game_engines.name, game_modes.name, genres.name, name, platforms.name, player_perspectives.name, release_dates.platform, release_dates.y, screenshots.image_id, screenshots.url, status, summary, themes.name, url, videos.name, videos.video_id, websites.category, websites.url; where id = %s;' % igdb_id})
    igdb_details = json.loads(resp.text)[0]
    return igdb_details


def search_for_game(name, regen=False):
    client_id, access_token = get_access_details(regen=regen)
    resp = requests.post('https://api.igdb.com/v4/games', **{'headers': {'Client-ID': client_id, 'Authorization': 'Bearer %s' % access_token}, 'data': 'search "%s"; fields name, id, release_dates.human, platforms.name;' % name.replace('"', '')})
    igdb_search = json.loads(resp.text)
    search_results = []
    for game in igdb_search:
        g = {}
        earliest_release_year = 9999
        if 'release_dates' not in game.keys():
            continue
        for y in game['release_dates']:
            if y['human'][-4:].isnumeric() and int(y['human'][-4:]) < earliest_release_year:
                earliest_release_year = int(y['human'][-4:])
        platform_list = ''
        for i in range(0, len(game['platforms'])):
            if i == 0:
                platform_list += game['platforms'][i]['name']
            else:
                platform_list += ", " + game['platforms'][i]['name']
        g['Row'] = '%s (%s) [%s]' % (game['name'], earliest_release_year, platform_list)
        g['ID'] = game['id']
        search_results.append(g)
    return search_results[:21]

def search_for_game_by_steam_appid(appid, regen=False):
    client_id, access_token = get_access_details(regen=regen)
    resp = requests.post('https://api.igdb.com/v4/external_games', **{'headers': {'Client-ID': client_id, 'Authorization': 'Bearer %s' % access_token}, 'data': 'fields category, game, game.name, game.release_dates.human, game.platforms.name, uid, year; where category = 1 & uid = "%s";' % appid})
    igdb_search = json.loads(resp.text)
    search_results = []
    for game in igdb_search:
        g = {}
        earliest_release_year = 9999
        if 'game' not in game.keys():
            continue
        for y in game['game']['release_dates']:
            if y['human'][-4:].isnumeric() and int(y['human'][-4:]) < earliest_release_year:
                earliest_release_year = int(y['human'][-4:])
        platform_list = ''
        for i in range(0, len(game['game']['platforms'])):
            if i == 0:
                platform_list += game['game']['platforms'][i]['name']
            else:
                platform_list += ", " + game['game']['platforms'][i]['name']
        g['Row'] = '%s (%s) [%s]' % (game['game']['name'], earliest_release_year, platform_list)
        g['ID'] = game['game']['id']
        search_results.append(g)
    return search_results[:21]


def get_suggested_data(igdb_data):
    suggestions = []

    if 'alternative_names' in igdb_data.keys():
        for a in igdb_data['alternative_names']:
            suggestions.append({'Type': 'Alias', 'Value': a['name'], 'Confidence': 70})
    # TODO: Are artworks useful?
    if 'category' in igdb_data.keys():
        if igdb_data['category'] == 4:
            suggestions.append({'Type': 'Meta', 'Value': 'Compilation', 'Confidence': 95})
        if igdb_data['category'] in [8, 9]:
            suggestions.append({'Type': 'Meta', 'Value': 'Remake', 'Confidence': 95})
    if 'collections' in igdb_data.keys():
        for c in igdb_data['collections']:
            suggestions.append({'Type': 'Collection', 'Value': c['name'], 'Confidence': 80})
    if 'cover' in igdb_data.keys():
        suggestions.append({'Type': 'Cover', 'Value': 'https:%s' % igdb_data['cover']['url'].replace('t_thumb', 't_cover_big_2x'), 'Confidence': 80})
    if 'franchises' in igdb_data.keys():
        for f in igdb_data['franchises']:
            suggestions.append({'Type': 'Franchise', 'Value': f['name'], 'Confidence': 80})
    if 'game_engines' in igdb_data.keys():
        for ge in igdb_data['game_engines']:
            suggestions.append({'Type': 'Engine', 'Value': ge['name'], 'Confidence': 70})
    if 'game_modes' in igdb_data.keys():
        for gm in igdb_data['game_modes']:
            suggestions.append({'Type': 'Meta', 'Value': gm['name'], 'Confidence': 70})
    if 'genres' in igdb_data.keys():
        for g in igdb_data['genres']:
            suggestions.append({'Type': 'Genre', 'Value': g['name'], 'Confidence': 70})
    if 'name' in igdb_data.keys():
        suggestions.append({'Type': 'Name', 'Value': igdb_data['name'], 'Confidence': 95})
    if 'platforms' in igdb_data.keys():
        for p in igdb_data['platforms']:
            suggestions.append({'Type': 'Platform', 'Value': p['name'], 'Confidence': 80})
    if 'player_perspectives' in igdb_data.keys():
        for p in igdb_data['player_perspectives']:
            suggestions.append({'Type': 'Tag', 'Value': p['name'], 'Confidence': 80})
    if 'release_dates' in igdb_data.keys():
        year = 2999
        for r in igdb_data['release_dates']:
            if 'y' in r.keys() and r['y'] < year:
                year = r['y']
        suggestions.append({'Type': 'Year', 'Value': year, 'Confidence': 80})
    if 'screenshots' in igdb_data.keys():
        for s in igdb_data['screenshots']:
            suggestions.append({'Type': 'Screenshot', 'Value': 'https:%s' % s['url'].replace('t_thumb', 't_1080p'), 'Confidence': 80})
    # TODO: Status
    if 'summary' in igdb_data.keys():
        suggestions.append({'Type': 'Description', 'Value': igdb_data['summary'], 'Confidence': 85})
    if 'themes' in igdb_data.keys():
        for t in igdb_data['themes']:
            suggestions.append({'Type': 'Tag', 'Value': t['name'], 'Confidence': 80})
    suggestions.append({'Type': 'IGDB URL', 'Value': igdb_data['url'].split('/games/')[-1], 'Confidence': 100})
    if 'videos' in igdb_data.keys():
        for v in igdb_data['videos']:
            c = 60
            if 'name' in v.keys() and 'trailer' in v['name'].lower():
                c = 90
            if 'http' not in v['video_id']:
                v['video_id'] = 'https://www.youtube.com/watch?v=' + v['video_id']
            suggestions.append({'Type': 'Video', 'Value': v['video_id'], 'Confidence': c})
    if 'websites' in igdb_data.keys():
        for w in igdb_data['websites']:
            if 'twitch.tv/directory/' in w['url']:
                suggestions.append({'Type': 'Twitch ID', 'Value': w['url'].split('/')[-1], 'Confidence': 95})
            if 'gog.com/' in w['url']:
                suggestions.append({'Type': 'GOG ID', 'Value': w['url'].split('/game/')[1].split('/')[0], 'Confidence': 95})
            if w['category'] == 1:
                suggestions.append({'Type': 'Website', 'Value': w['url'], 'Confidence': 95})
            if 'play.google.com' in w['url']:
                suggestions.append({'Type': 'Google Play ID', 'Value': w['url'].split("id=")[1].split("&")[0], 'Confidence': 95})

    return suggestions
