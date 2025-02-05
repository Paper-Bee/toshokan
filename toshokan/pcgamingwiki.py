import json
import re
import requests


def download_data_by_steamid(steamid):
    resp = json.loads(requests.get('https://www.pcgamingwiki.com/w/api.php', params={'action': 'cargoquery', 'tables': 'Infobox_game', 'fields': 'Infobox_game._pageID=PageID,Infobox_game.Steam_AppID', 'where': 'Infobox_game.Steam_AppID HOLDS "%s"' % steamid, 'format': 'json'}).text)
    if len(resp['cargoquery']) == 0:
        return None
    pcgw_id = resp['cargoquery'][0]['title']['PageID']

    resp = json.loads(requests.get('https://www.pcgamingwiki.com/w/api.php', params={'action': 'parse', 'format': 'json', 'pageid': pcgw_id, 'prop': 'wikitext'}).text)

    return {'ID': resp['parse']['pageid'], 'Data': resp['parse']['wikitext']['*']}


def download_data_by_page_title(title):
    resp = json.loads(requests.get('https://www.pcgamingwiki.com/w/api.php', params={'action': 'cargoquery', 'tables': 'Infobox_game', 'fields': 'Infobox_game._pageID=PageID,Infobox_game.Steam_AppID', 'where': 'Infobox_game._pageName="%s"' % title, 'format': 'json'}).text)
    pcgw_id = resp['cargoquery'][0]['title']['PageID']

    resp = json.loads(requests.get('https://www.pcgamingwiki.com/w/api.php', params={'action': 'parse', 'format': 'json', 'pageid': pcgw_id, 'prop': 'wikitext'}).text)

    return {'ID': resp['parse']['pageid'], 'Data': resp['parse']['wikitext']['*']}


def search_for_game(name):
    resp = requests.get('https://www.pcgamingwiki.com/w/api.php', params={'action': 'opensearch', 'search': name})
    _, titles, _, links = json.loads(resp.text)

    search_results = []
    for i in range(0, len(titles)):
        g = {}
        g['Row'] = titles[i] + ' []'
        g['URL'] = links[i]
        search_results.append(g)
    return search_results[:21]


def get_suggested_data(pcgw_data, exclude_developers=False, exclude_publishers=False):
    suggestions = []

    # Game Name
    name = re.findall('\\|title *= (.*)\\n', pcgw_data)
    if len(name) == 1 and '|' not in name[0]:
        suggestions.append({'Type': 'Name', 'Value': name[0].strip(), 'Confidence': 95})
    # Developers
    if not exclude_developers:
        developers = re.findall('game/row/developer\\|(.*)}}', pcgw_data)
        for d in developers:
            suggestions.append({'Type': 'Developer', 'Value': d.split('|')[0].strip(), 'Confidence': 95})
    # Publishers
    if not exclude_publishers:
        publishers = re.findall('game/row/publisher\\|(.*)}}', pcgw_data)
        for p in publishers:
            suggestions.append({'Type': 'Publisher', 'Value': p.split('|')[0].strip(), 'Confidence': 95})
    # Tags
    tags = []
    for tag_category in ['monetization', 'microtransactions', 'modes', 'pacing', 'perspectives', 'controls', 'sports', 'vehicles', 'art styles', 'themes']:
        tags += re.findall('Infobox game/row/taxonomy/%s.*\\|(.*)}}' % tag_category, pcgw_data)
    for raw_tag_list in tags:
        for t in [x.strip() for x in raw_tag_list.split(',')]:
            # Skip none entries
            if t.strip() == 'None' or t.strip() == '':
                continue
            suggestions.append({'Type': 'Tag', 'Value': t.strip(), 'Confidence': 75})
    # Genres
    genres = re.findall('Infobox game/row/taxonomy/genres.*\\|(.*)}}', pcgw_data)
    for raw_genre_list in genres:
        for g in [x.strip() for x in raw_genre_list.split(',')]:
            if g != '':
                suggestions.append({'Type': 'Genre', 'Value': g.strip(), 'Confidence': 75})
    # Series
    series = re.findall('Infobox game/row/taxonomy/series.*\\|(.*)}}', pcgw_data)
    for raw_series_list in series:
        for s in [x.strip() for x in raw_series_list.split(',')]:
            suggestions.append({'Type': 'Franchise', 'Value': s.strip(), 'Confidence': 75})
    # Steam ID
    steam_id = re.findall('\\|steam appid * = (.*)\\n', pcgw_data)
    for x in steam_id:
        if x == '':
            continue
        suggestions.append({'Type': 'Steam ID', 'Value': x.strip(), 'Confidence': 95})
    # HowLongToBeat ID
    hltb_id = re.findall('\\|hltb * = (.*)\\n', pcgw_data)
    for x in hltb_id:
        if x == '':
            continue
        suggestions.append({'Type': 'HowLongToBeat ID', 'Value': x.strip(), 'Confidence': 95})
    # IGDB ID
    igdb_id = re.findall('\\|igdb * = (.*)\\n', pcgw_data)
    for x in igdb_id:
        if x == '':
            continue
        suggestions.append({'Type': 'IGDB ID', 'Value': x.strip(), 'Confidence': 95})
    # MobyGames ID
    mobygames_id = re.findall('\\|mobygames * = (.*)\\n', pcgw_data)
    for x in mobygames_id:
        if x == '':
            continue
        suggestions.append({'Type': 'MobyGames ID', 'Value': x.strip(), 'Confidence': 95})
    # StrategyWiki ID
    strategywiki_id = re.findall('\\|strategywiki * = (.*)\\n', pcgw_data)
    for x in strategywiki_id:
        if x == '':
            continue
        suggestions.append({'Type': 'StrategyWiki ID', 'Value': x.strip(), 'Confidence': 95})
    # Wikipedia ID
    wikipedia_id = re.findall('\\|wikipedia * = (.*)\\n', pcgw_data)
    for x in wikipedia_id:
        if x == '':
            continue
        suggestions.append({'Type': 'Wikipedia ID', 'Value': x.strip(), 'Confidence': 95})

    return suggestions
