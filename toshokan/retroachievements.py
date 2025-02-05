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


def has_valid_igdb_platform(igdb_data):
    valid_platforms = [
        'Atari 2600',
        'New Nintendo 3DS',
        'Arduboy',
        'Nintendo 3DS',
        'Wii',
        'Wii U',
        'PlayStation Portable',
        'Nintendo DS',
        'Nintendo DSi',
        'Zeebo',
        'PlayStation 2',
        'Arcade',
        'Uzebox',
        'Game Boy Advance',
        'Nintendo 64',
        'WonderSwan Color',
        'WonderSwan',
        'Xbox',
        'Nintendo GameCube',
        'Pokémon mini',
        'PlayStation',
        'Dreamcast',
        'Game Boy Color',
        '64DD',
        'Neo Geo Pocket Color',
        'Super Nintendo Entertainment System',
        'Game Boy',
        'Sega Mega Drive/Genesis',
        'Neo Geo Pocket',
        'Super Famicom',
        'Sega Saturn',
        'Satellaview',
        'Virtual Boy',
        'Atari Jaguar CD',
        'Neo Geo CD',
        'Sega CD 32X',
        'Sega 32X',
        'FM Towns',
        'Sega Master System/Mark III',
        'PC-FX',
        '3DO Interactive Multiplayer',
        'Atari Jaguar',
        'Mega Duck/Cougar Boy',
        'Amiga',
        'Sega CD',
        'Nintendo Entertainment System',
        'Sega Game Gear',
        'Watara/QuickShot Supervision',
        'Atari Lynx',
        'Turbografx-16/PC Engine CD',
        'TurboGrafx-16/PC Engine',
        'Sharp X68000',
        'PC Engine SuperGrafx',
        'PC-9800 Series',
        'Apple IIGS',
        'Sharp X1',
        'Commodore C64/128/MAX',
        'Amstrad CPC',
        'Atari ST/STE',
        'Atari 5200',
        'Atari 7800',
        'MSX2',
        'SG-1000',
        'Vectrex',
        'MSX',
        'TRS-80',
        'ColecoVision',
        'FM-7',
        'Intellivision',
        'ZX Spectrum',
        'Arcadia 2001',
        'PC-8800 Series',
        'DOS',
        'Sinclair ZX81',
        'Atari 8-bit',
        'Odyssey 2 / Videopac G7000',
        'Elektor TV Games Computer',
        'Apple II',
        'VC 4000',
        'Fairchild Channel F',
    ]
    igdb_platforms = [x['name'] for x in igdb_data['platforms']]
    found_platforms = []
    for x in igdb_platforms:
        if x in valid_platforms:
            found_platforms.append(x)
    if len(found_platforms) == 0:
        return False
    return True


def search_for_game(name):
    games = get_gamename_array()
    results = process.extract(name, games, scorer=fuzz.ratio, limit=10)
    results += process.extract(name, games, scorer=fuzz.partial_ratio, limit=10)
    final_results = []
    used_ids = []
    for r in results:
        g = {}
        g['Title'], g['ID'] = r[0].split('||', 1)
        # Skip subsets
        if '[Subset' in g['Title']:
            continue
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
    return json.loads(requests.get('https://retroachievements.org/API/API_GetGameExtended.php', params={'y': user_config['RetroAchievements']['api_key'], 'i': id}).text)


def get_suggested_data(ra_data):
    suggestions = []
    suggestions.append({'Type': 'Platform', 'Value': ra_data['ConsoleName'], 'Confidence': 95})
    if '000002.png' not in ra_data['ImageTitle']:
        suggestions.append({'Type': 'Screenshot', 'Value': 'https://media.retroachievements.org' + ra_data['ImageTitle'], 'Confidence': 71})
    if '000002.png' not in ra_data['ImageIngame']:
        suggestions.append({'Type': 'Screenshot', 'Value': 'https://media.retroachievements.org' + ra_data['ImageIngame'], 'Confidence': 70})
    if '000002.png' not in ra_data['ImageBoxArt']:
        suggestions.append({'Type': 'Cover', 'Value': 'https://media.retroachievements.org' + ra_data['ImageBoxArt'], 'Confidence': 70})
    if ra_data['Released'] is not None:
        suggestions.append({'Type': 'Year', 'Value': ra_data['Released'].split('-')[0], 'Confidence': 60})
    if ra_data['NumAchievements'] > 0:
        suggestions.append({'Type': 'Meta', 'Value': 'RetroAchievements', 'Confidence': 60})
    return suggestions
