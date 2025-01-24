from bs4 import BeautifulSoup
import config
import os
import sqlite3
from thefuzz import fuzz, process


def get_sqlite_path():
    user_config = config.get_config()
    return os.path.join(user_config['Toshokan']['storage_path'], 'launchbox.sqlite')


def xml_to_sqlite():
    user_config = config.get_config()
    sqlite_path = get_sqlite_path()
    launchbox_settings = user_config['LaunchBox']
    launchbox_size = os.path.getsize(launchbox_settings['path_to_metadata_xml'])
    # Only update if size is different
    if launchbox_size != launchbox_settings['last_db_size']:
        with open(launchbox_settings['path_to_metadata_xml'], 'r', encoding='utf-8') as in_file:
            temp_data = in_file.read()
        launchbox_db = BeautifulSoup(temp_data, "xml")
        # Delete old DB
        if os.path.exists(sqlite_path):
            os.remove(sqlite_path)
        # Create new DB
        with sqlite3.connect(sqlite_path) as con:
            cur = con.cursor()
            # Extract game data
            cur.execute('''CREATE TABLE Game(Name, ReleaseYear, Overview,
            MaxPlayers, ReleaseType, Cooperative, VideoURL, DatabaseID,
            CommunityRating, Platform, ESRB, CommunityRatingCount, Genres,
            Developer, Publisher)''')
            temp_games = launchbox_db.find_all('Game')
            for g in temp_games:
                g_dict = {}
                for param in ['Name', 'ReleaseYear', 'Overview', 'MaxPlayers', 'ReleaseType',
                              'Cooperative', 'VideoURL', 'DatabaseID', 'CommunityRating', 'Platform',
                              'ESRB', 'CommunityRatingCount', 'Genres', 'Developer', 'Publisher']:
                    souped_param = g.find(param)
                    if souped_param is not None:
                        g_dict[param] = g.find(param).text
                    else:
                        g_dict[param] = None
                cur.execute('''INSERT INTO Game VALUES(:Name, :ReleaseYear, :Overview,
                :MaxPlayers, :ReleaseType, :Cooperative, :VideoURL, :DatabaseID,
                :CommunityRating, :Platform, :ESRB, :CommunityRatingCount, :Genres,
                :Developer, :Publisher)''', g_dict)
            # Extract alternate name data
            cur.execute('''CREATE TABLE GameAlternateName(AlternateName,
            DatabaseID, Region)''')
            temp_games = launchbox_db.find_all('GameAlternateName')
            for g in temp_games:
                g_dict = {}
                for param in ['AlternateName', 'DatabaseID', 'Region']:
                    souped_param = g.find(param)
                    if souped_param is not None:
                        g_dict[param] = g.find(param).text
                    else:
                        g_dict[param] = None
                cur.execute('''INSERT INTO GameAlternateName VALUES(:AlternateName,
                :DatabaseID, :Region)''', g_dict)
            # Extract game image data
            cur.execute('''CREATE TABLE GameImage(DatabaseID,
            FileName, Type, Region, CRC32)''')
            temp_games = launchbox_db.find_all('GameImage')
            for g in temp_games:
                g_dict = {}
                for param in ['DatabaseID', 'FileName', 'Type', 'Region', 'CRC32']:
                    souped_param = g.find(param)
                    if souped_param is not None:
                        g_dict[param] = g.find(param).text
                    else:
                        g_dict[param] = None
                cur.execute('''INSERT INTO GameImage VALUES(:DatabaseID,
                :FileName, :Type, :Region, :CRC32)''', g_dict)
        # Store size for future reference
        user_config = config.set_option(user_config, 'LaunchBox', 'last_db_size', launchbox_size)
        config.save_config(user_config)
    else:
        # DB hasn't changed since last update
        pass


def get_gamename_array():
    sqlite_path = get_sqlite_path()
    with sqlite3.connect(sqlite_path) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        official_names = cur.execute("SELECT DatabaseID, Name FROM Game").fetchall()
        aliases = cur.execute("SELECT DatabaseID, AlternateName as Name FROM GameAlternateName").fetchall()
    results = []
    for g in official_names:
        results.append(g["Name"]+"||"+g["DatabaseID"])
    for g in aliases:
        results.append(g["Name"]+"||"+g["DatabaseID"])
    return list(set(results))


def search_for_game(name):
    games = get_gamename_array()
    results = process.extract(name, games, scorer=fuzz.ratio, limit=10)
    results += process.extract(name, games, scorer=fuzz.partial_ratio, limit=10)
    final_results = []
    used_gids = []
    for r in results:
        g = {}
        g['Name'], g['DatabaseID'] = r[0].split('||', 1)
        g['SearchScore'] = r[1]
        if g['DatabaseID'] not in used_gids:
            final_results.append(g)
            used_gids.append(g['DatabaseID'])
    final_results = sorted(final_results, key=lambda x: x['SearchScore'], reverse=True)
    return expand_search_results(final_results[:21])


def expand_search_results(results):
    expanded_results = []
    sqlite_path = get_sqlite_path()
    with sqlite3.connect(sqlite_path) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        for r in results:
            info = cur.execute("SELECT ReleaseYear, Platform FROM Game WHERE DatabaseID = ?", (r['DatabaseID'], )).fetchone()
            expanded = {}
            expanded['Row'] = '%s (%s) [%s]' % (r['Name'], info['ReleaseYear'], info['Platform'])
            expanded['ID'] = r['DatabaseID']
            expanded_results.append(expanded)
    return expanded_results


# Given a DatabaseID, return everything from LaunchBox
def get_full_game_info(id):
    sqlite_path = get_sqlite_path()
    with sqlite3.connect(sqlite_path) as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        game_info = dict(cur.execute("SELECT * FROM Game WHERE DatabaseID = ?", (id, )).fetchone())
        aliases = cur.execute("SELECT * FROM GameAlternateName WHERE DatabaseID = ?", (id, )).fetchall()
        images = cur.execute("SELECT * FROM GameImage WHERE DatabaseID = ?", (id, )).fetchall()
        game_info['Aliases'] = []
        for a in aliases:
            game_info['Aliases'].append({'Name': a['AlternateName'], 'Region': a['Region']})
        game_info['Images'] = []
        for i in images:
            game_info['Images'].append({'URL': 'https://images.launchbox-app.com/' + i['FileName'], 'Type': i['Type'], 'Region': i['Region']})
    return game_info


def get_suggested_data(lbdata):
    suggestions = []
    for g in [x.strip() for x in lbdata['Genres'].split(';')]:
        suggestions.append({'Type': 'Genre', 'Value': g, 'Confidence': 90})
    if lbdata['Developer'] is not None and len(lbdata['Developer']) > 0:
        suggestions.append({'Type': 'Developer', 'Value': lbdata['Developer'], 'Confidence': 90})
    if lbdata['Publisher'] is not None and len(lbdata['Publisher']) > 0:
        suggestions.append({'Type': 'Publisher', 'Value': lbdata['Publisher'], 'Confidence': 90})
    suggestions.append({'Type': 'Platform', 'Value': lbdata['Platform'], 'Confidence': 100})
    if lbdata['ReleaseYear'] is not None:
        suggestions.append({'Type': 'Year', 'Value': lbdata['ReleaseYear'], 'Confidence': 90})
    if lbdata['MaxPlayers'] is not None:
        if int(lbdata['MaxPlayers']) > 1:
            suggestions.append({'Type': 'Meta', 'Value': 'Multiplayer', 'Confidence': 70})
            if lbdata['Cooperative']:
                suggestions.append({'Type': 'Meta', 'Value': 'Co-op', 'Confidence': 70})
    if lbdata['Overview'] is not None and len(lbdata['Overview']) > 0:
        suggestions.append({'Type': 'Description', 'Value': lbdata['Overview'], 'Confidence': 90})
    if lbdata['VideoURL'] is not None and len(lbdata['VideoURL']) > 0:
        suggestions.append({'Type': 'Video', 'Value': lbdata['VideoURL'], 'Confidence': 90})
    for a in lbdata['Aliases']:
        suggestions.append({'Type': 'Alias', 'Value': a['Name'].strip(), 'Confidence': 70})
    for i in lbdata['Images']:
        if i['Type'] == 'Box - Front':
            suggestions.append({'Type': 'Cover', 'Value': i['URL'], 'Confidence': 90})
        # Reconstructed boxart is normally fine but should be scrutinized for AI
        if i['Type'] == 'Box - Front - Reconstructed':
            suggestions.append({'Type': 'Cover', 'Value': i['URL'], 'Confidence': 80})
        # Fliers and posters should normally not be used, but are good for things like Arcade
        if i['Type'] == 'Advertisement Flyer - Front':
            suggestions.append({'Type': 'Cover', 'Value': i['URL'], 'Confidence': 60})
        if i['Type'] == 'Advertisement Flyer - Back':
            suggestions.append({'Type': 'Cover', 'Value': i['URL'], 'Confidence': 50})
        if i['Type'] == 'Poster':
            suggestions.append({'Type': 'Cover', 'Value': i['URL'], 'Confidence': 50})
        # Fan art is a last resort but is good for fan games and hacks
        if i['Type'] == 'Fanart - Box - Front':
            suggestions.append({'Type': 'Cover', 'Value': i['URL'], 'Confidence': 25})
        # Title screens get a slight boost in confidence to encourage them being first
        if i['Type'] == 'Screenshot - Game Title':
            suggestions.append({'Type': 'Screenshot', 'Value': i['URL'], 'Confidence': 81})
        if i['Type'] == 'Screenshot - Gameplay':
            suggestions.append({'Type': 'Screenshot', 'Value': i['URL'], 'Confidence': 80})
        # Banners have potential as backgrounds
        if i['Type'] == 'Banner':
            suggestions.append({'Type': 'Background', 'Value': i['URL'], 'Confidence': 50})
        # Deprioritize fan art backgrounds, but keep it in case there's nothing else
        if i['Type'] == 'Fanart - Background':
            suggestions.append({'Type': 'Background', 'Value': i['URL'], 'Confidence': 25})
    return suggestions
