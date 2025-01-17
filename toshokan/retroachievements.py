import config
import json
import os
import requests
import sqlite3
from thefuzz import fuzz, process


def get_sqlite_path():
    user_config = config.get_config()
    return os.path.join(user_config['Toshokan']['storage_path'], 'retroachievements.sqlite')


def create_db():
    user_config = config.get_config()
    sqlite_path = get_sqlite_path()
    # Delete old DB
    if os.path.exists(sqlite_path):
        os.remove(sqlite_path)
    # Fetch console list
    print("Fetching console ID's...")
    console_list = json.loads(requests.get('https://retroachievements.org/API/API_GetConsoleIDs.php', params={'y': user_config['RetroAchievements']['api_key'], 'g': 1}).text)
    game_list = []
    # Fetch games per console
    for c in console_list:
        print("Fetching sets for %s games..." % c['Name'])
        game_list += json.loads(requests.get('https://retroachievements.org/API/API_GetGameList.php', params={'y': user_config['RetroAchievements']['api_key'], 'i': c['ID']}).text)
    # Create new DB
    print("Building database...")
    with sqlite3.connect(sqlite_path) as con:
        cur = con.cursor()
        # Extract game data
        cur.execute('''CREATE TABLE Game(ID, Title, ConsoleName,
        ImageIcon, NumAchievements, NumLeaderboards, Points, DateModified)''')
        for g in game_list:
            g_dict = {}
            for param in ['ID', 'Title', 'ConsoleName', 'ImageIcon', 'NumAchievements',
                          'NumLeaderboards', 'Points', 'DateModified']:
                g_dict[param] = g[param]
            cur.execute('''INSERT INTO Game VALUES(:ID, :Title, :ConsoleName,
        :ImageIcon, :NumAchievements, :NumLeaderboards, :Points, :DateModified)''', g_dict)


def get_gamename_array():
    sqlite_path = get_sqlite_path()
    with sqlite3.connect(sqlite_path) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        game_names = cur.execute("SELECT ID, Title FROM Game").fetchall()
    results = []
    for g in game_names:
        results.append(g["Title"]+"||"+str(g["ID"]))
    return results


def search_for_game(name):
    games = get_gamename_array()
    results = process.extract(name, games, scorer=fuzz.ratio, limit=10)
    results += process.extract(name, games, scorer=fuzz.partial_ratio, limit=10)
    final_results = []
    used_ids = []
    for r in results:
        g = {}
        g['Title'], g['ID'] = r[0].split('||', 1)
        g['ID'] = int(g['ID'])
        g['SearchScore'] = r[1]
        if g['ID'] not in used_ids:
            final_results.append(g)
            used_ids.append(g['ID'])
    final_results = sorted(final_results, key=lambda x: x['SearchScore'], reverse=True)
    return expand_search_results(final_results[:21])


def expand_search_results(results):
    expanded_results = []
    sqlite_path = get_sqlite_path()
    with sqlite3.connect(sqlite_path) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        for r in results:
            info = cur.execute("SELECT Title, ConsoleName, Points FROM Game WHERE ID = ?", (r['ID'], )).fetchone()
            expanded = {}
            expanded['Row'] = '%s (%s) [%sp]' % (r['Title'], info['ConsoleName'], info['Points'])
            expanded['ID'] = r['ID']
            expanded_results.append(expanded)
    return expanded_results


# Given an ID, fetch more info from RA
def get_game_info(id):
    user_config = config.get_config()
    return json.loads(requests.get('https://retroachievements.org/API/API_GetGame.php', params={'y': user_config['RetroAchievements']['api_key'], 'i': id}).text)


def get_suggested_data(ra_data):
    suggestions = []
    suggestions.append({'Type': 'Platform', 'Value': ra_data['ConsoleName'], 'Confidence': 95})
    if '000002.png' not in ra_data['ImageTitle']:
        suggestions.append({'Type': 'Screenshot', 'Value': ra_data['ImageTitle'], 'Confidence': 71})
    if '000002.png' not in ra_data['ImageIngame']:
        suggestions.append({'Type': 'Screenshot', 'Value': ra_data['ImageIngame'], 'Confidence': 70})
    if '000002.png' not in ra_data['ImageBoxArt']:
        suggestions.append({'Type': 'Cover', 'Value': ra_data['ImageBoxArt'], 'Confidence': 70})
    if ra_data['Released'] is not None:
        suggestions.append({'Type': 'Year', 'Value': ra_data['Released'].split('-')[0], 'Confidence': 60})
    return suggestions
