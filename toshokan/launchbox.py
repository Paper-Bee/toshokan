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


def find_game_by_name(name):
    games = get_gamename_array()
    results = process.extract(name, games, scorer=fuzz.ratio, limit=10)
    results += process.extract(name, games, scorer=fuzz.partial_ratio, limit=10)
    final_results = []
    used_gids = []
    for r in results:
        g = {}
        g['Name'], g['DatabaseID'] = r[0].split('||', 1)
        g['Score'] = r[1]
        if g['DatabaseID'] not in used_gids:
            final_results.append(g)
            used_gids.append(g['DatabaseID'])
    final_results = sorted(final_results, key=lambda x: x['Score'], reverse=True)
    return final_results[:10]