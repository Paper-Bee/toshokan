import config
import game
import gamefaqs
import howlongtobeat
import igdb
import launchbox
import mobygames
import os
import pcgamingwiki
import retroachievements
import steam
import storage
import time
import webbrowser


def select_from_list(options):
    for i in range(0, len(options)):
        print('%s. %s' % (i, options[i]['Row']))
    print()
    user_input = input("Select an option (or multiple separated by space): ").strip().split(' ')
    for num in user_input:
        if not num.isnumeric():
            return []
    return [options[int(x)] for x in user_input]


def exclude_from_list(options):
    valid_numbers = list(range(0, len(options)))
    for i in valid_numbers:
        print('%s. %s' % (i, options[i]['Row']))
    print()
    user_input = input("Exclude an option (or multiple separated by space): ").strip().split(' ')
    for num in user_input:
        if num.isnumeric():
            valid_numbers.remove(int(num))
    return [options[int(x)] for x in valid_numbers]


def prompt_for_external_id():
    user_config = config.get_config()
    external_id = input("External ID: ")
    if external_id.isnumeric():
        external_id = int(external_id)
    else:
        external_id = user_config['Toshokan']['highest_seen_external_id'] + 1
    # Update the highest seen external ID if it's larger than the previous
    if external_id > user_config['Toshokan']['highest_seen_external_id']:
        user_config = config.set_option(user_config, 'Toshokan', 'highest_seen_external_id', external_id)
        config.save_config(user_config)
    return external_id


def choose_images(category, url_objects):
    # URL Objects are dictionaries containing Source, Value, and Confidence
    user_config = config.get_config()
    # Make the workzone directory if it does not exist
    workzone_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Workzone')
    if not os.path.exists(workzone_dir):
        os.mkdir(workzone_dir)
    # Make the subfolders as needed:
    work_dir = os.path.join(workzone_dir, category)
    if not os.path.exists(work_dir):
        os.mkdir(work_dir)
    keep_dir = os.path.join(work_dir, 'Keep')
    if not os.path.exists(keep_dir):
        os.mkdir(keep_dir)
    # Keep track of mappings between old file names and URL's
    old_file_to_url = {}
    # Download images
    for obj in url_objects:
        source = obj['Source']
        url = obj['Value']
        # Invert confidence to display images in descending order
        confidence = str(100 - obj['Confidence'])
        while len(confidence) < 3:
            confidence = '0' + confidence
        try:
            down_file = storage.download_image(url)
            old_file_name = os.path.basename(down_file)
            old_file_to_url[old_file_name] = url
            os.rename(down_file, os.path.join(work_dir, '%s-%s-%s' % (confidence, source, old_file_name)))
        except Exception as e:
            print('Error downloading %s: %s' % (url, str(e)))
    # Open folder
    webbrowser.open('file:///' + str(work_dir))
    # Wait for final selection
    while True:
        wait = False
        for f in os.listdir(work_dir):
            if f.endswith('.jpg'):
                wait = True
        if wait:
            time.sleep(0.5)
        else:
            break
    selected_files = []
    selected_files_raw = os.listdir(keep_dir)
    if len(selected_files_raw) > 0:
        for r in selected_files_raw:
            s = {}
            s['Path'] = os.path.join(keep_dir, r)
            for old_file_name in old_file_to_url.keys():
                if s['Path'].endswith(old_file_name):
                    s['URL'] = old_file_to_url[old_file_name]
            selected_files.append(s)
    return selected_files


def choose_tags(options):
    user_config = config.get_config()
    pass


def choose_platforms(options):
    user_config = config.get_config()
    pass


def collect_data(g):
    user_config = config.get_config()
    user_input = input("Please input a game name or Steam URL: ").strip()

    if user_config['Toshokan']['use_external_id']:
        g['External ID'] = prompt_for_external_id()

    # Handle Steam
    steam_appid = None
    if user_config['Steam']['enabled']:
        print("Searching on Steam...")
        if 'store.steampowered.com/app/' in user_input:
            steam_appid = user_input.split('com/app/')[1].split('/')[0]
        else:
            steam_search_results = steam.search_for_game(user_input)
            chosen = select_from_list(steam_search_results)
            if len(chosen) != 0:
                steam_appid = chosen[0]['ID']
        if steam_appid is not None:
            steam_data = steam.download_data(steam_appid)
            user_input = steam_data['name']
            steam_suggestions = steam.get_suggested_data(steam_data)
            if len(steam_data.keys()) == 0:
                g['External Links']['Steam']['Is Delisted'] = True
            g['External Links']['Steam']['ID'] = steam_appid
            g['External Suggestions']['Steam'] = steam_suggestions

    # Handle PCGamingWiki
    if user_config['PCGamingWiki']['enabled']:
        pcgw_data = None
        if steam_appid is not None:
            pcgw_data = pcgamingwiki.download_data_by_steamid(steam_appid)
            g['External Links']['PCGamingWiki']['Method'] = 'Steam AppID'
            g['External Links']['PCGamingWiki']['ID'] = steam_appid
        else:
            print("Searching on PCGamingWiki...")
            pcgw_search_results = pcgamingwiki.search_for_game(user_input)
            chosen = select_from_list(pcgw_search_results)
            if len(chosen) != 0:
                pcgw_data = pcgamingwiki.download_data_by_page_title(chosen[0]['Row'])
                g['External Links']['PCGamingWiki']['Method'] = 'Title'
                g['External Links']['PCGamingWiki']['ID'] = chosen[0]['Row']
        # Get suggestions if we have data
        if pcgw_data is not None:
            pcgamingwiki_suggestions = pcgamingwiki.get_suggested_data(pcgw_data['Data'])
            g['External Suggestions']['PCGamingWiki'] = pcgamingwiki_suggestions

    # Handle IGDB
    if user_config['IGDB']['enabled']:
        # TODO: Use ID from PCGamingWiki if valid
        print("Searching on IGDB...")
        igdb_search_results = igdb.search_for_game(user_input)
        chosen = select_from_list(igdb_search_results)
        if len(chosen) != 0:
            igdb_data = igdb.get_full_game_info(chosen[0]['ID'])
            igdb_suggestions = igdb.get_suggested_data(igdb_data)
            g['External Links']['IGDB']['ID'] = chosen[0]['ID']
            g['External Suggestions']['IGDB'] = igdb_suggestions

    # Handle LaunchBox
    if user_config['LaunchBox']['enabled']:
        print("Searching on LaunchBox...")
        launchbox_search_results = launchbox.search_for_game(user_input)
        chosen = select_from_list(launchbox_search_results)
        if len(chosen) != 0:
            g['External Suggestions']['LaunchBox'] = {}
            g['External Links']['LaunchBox'] = {}
            for c in chosen:
                launchbox_data = launchbox.get_full_game_info(c['ID'])
                platform = launchbox_data['Platform']
                g['External Links']['LaunchBox'][platform] = {}
                g['External Links']['LaunchBox'][platform]['ID'] = c['ID']
                launchbox_suggestions = launchbox.get_suggested_data(launchbox_data)
                g['External Suggestions']['LaunchBox'][platform] = launchbox_suggestions

    # Handle GameFAQs
    if user_config['GameFAQs']['enabled']:
        print("Searching on GameFAQs...")
        gamefaqs_search_results = gamefaqs.search_for_game(user_input)
        chosen = select_from_list(gamefaqs_search_results)
        if len(chosen) != 0:
            g['External Links']['GameFAQs']['URL'] = chosen[0]['URL']

    # Handle HowLongToBeat
    if user_config['HowLongToBeat']['enabled']:
        # Use ID from PCGamingWiki if valid
        if user_config['PCGamingWiki']['enabled'] and pcgw_data is not None:
            for v in g['External Suggestions']['PCGamingWiki']:
                if v['Type'] == 'HowLongToBeat ID':
                    print("Using HowLongToBeat ID from PCGamingWiki...")
                    g['External Links']['HowLongToBeat']['ID'] = v['Value']
        else:
            try:
                print("Searching on HowLongToBeat...")
                hltb_search_results = howlongtobeat.search_for_game(user_input)
                chosen = select_from_list(hltb_search_results)
                if len(chosen) != 0:
                    g['External Links']['HowLongToBeat']['ID'] = chosen[0]['ID']
            except Exception as e:
                print("Unable to fetch HowLongToBeat: %s" % str(e))

    # Handle RetroAchievements
    if user_config['RetroAchievements']['enabled']:
        print("Searching on RetroAchievements...")
        retroachievements_search_results = retroachievements.search_for_game(user_input)
        chosen = select_from_list(retroachievements_search_results)
        if len(chosen) != 0:
            g['External Suggestions']['RetroAchievements'] = {}
            g['External Links']['RetroAchievements'] = {}
            for c in chosen:
                retroachievements_data = retroachievements.get_game_info(c['ID'])
                retroachievements_suggestions = retroachievements.get_suggested_data(retroachievements_data)
                platform = retroachievements_data['ConsoleName']
                g['External Links']['RetroAchievements'][platform] = {}
                g['External Links']['RetroAchievements'][platform]['ID'] = c['ID']
                g['External Suggestions']['RetroAchievements'][platform] = retroachievements_suggestions

    # Handle MobyGames
    if user_config['MobyGames']['enabled']:
        try:
            print("Searching on MobyGames...")
            mobygames_search_results = mobygames.search_for_game(user_input)
            chosen = select_from_list(mobygames_search_results)
            if len(chosen) != 0:
                mobygames_data = mobygames.get_game_info(chosen[0]['ID'])
                mobygames_suggestions = mobygames.get_suggested_data(mobygames_data)
                g['External Links']['MobyGames']['ID'] = chosen[0]['ID']
                g['External Suggestions']['MobyGames'] = mobygames_suggestions
        except Exception as e:
            print("Unable to fetch MobyGames: %s" % str(e))

    return g


def consolidate_type(game_data, attribute):
    candidates = []
    used_candidates = []
    for data_source in game_data['External Suggestions'].keys():
        if data_source != 'LaunchBox':
            for obj in game_data['External Suggestions'][data_source]:
                if obj['Type'] == attribute:
                    if obj['Value'] not in used_candidates:
                        used_candidates.append(obj['Value'])
                        candidates.append(obj)
                        candidates[-1]['Source'] = data_source
        else:
            for platform in game_data['External Suggestions'][data_source]:
                for obj in game_data['External Suggestions'][data_source][platform]:
                    if obj['Type'] == attribute:
                        if obj['Value'] not in used_candidates:
                            used_candidates.append(obj['Value'])
                            candidates.append(obj)
                            candidates[-1]['Source'] = data_source
    candidate_objects = []
    for candid in candidates:
        c = candid.copy()
        c['Row'] = '%s [%s]' % (c['Value'], c['Source'])
        candidate_objects.append(c)
    return candidate_objects


def refine_data(game_data):
    print("Filtering aliases...")
    alias_candidate_objects = consolidate_type(game_data, 'Alias')
    aliases = exclude_from_list(alias_candidate_objects)
    game_data['Aliases'] = [x['Value'] for x in aliases]

    print("Selecting background...")
    bg_candidate_objects = consolidate_type(game_data, 'Background')
    chosen_bgs = choose_images('Background', bg_candidate_objects)
    if len(chosen_bgs) == 1:
        game_data['Background URL'] = chosen_bgs[0]['URL']
        storage.store_background(game_data['ID'], chosen_bgs[0]['Path'])
    return game_data


def add_new_game():
    g = game.new_game()
    id = storage.get_new_json_id()
    g['ID'] = id
    g = collect_data(g)
    g = refine_data(g)
    storage.store_json(g)
