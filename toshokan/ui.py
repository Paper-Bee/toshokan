import config
import game
import gamefaqs
import howlongtobeat
import igdb
import launchbox
import mobygames
from operator import itemgetter
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
        if 'Type' in options[i].keys() and options[i]['Type'] == 'Description':
            print('------------------------------------------------------------------------------------------')
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
        if 'Type' in options[i].keys() and options[i]['Type'] == 'Description':
            print('------------------------------------------------------------------------------------------')
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
            if category == 'Background':
                down_file = storage.download_image(url, bg=True)
            else:
                down_file = storage.download_image(url)
            old_file_name = os.path.basename(down_file)
            old_file_to_url[old_file_name] = url
            os.rename(down_file, os.path.join(work_dir, '%s-%s-%s' % (confidence, source, old_file_name)))
        except Exception as e:
            print('Error downloading %s: %s' % (url, str(e)))
    images_found = False
    for f in os.listdir(work_dir):
        if f.endswith('.jpg') or f.endswith('.png'):
            images_found = True
    if not images_found:
        return []
    # Open folder
    webbrowser.open('file:///' + str(work_dir))
    # Wait for final selection
    while True:
        wait = False
        for f in os.listdir(work_dir):
            if f.endswith('.jpg') or f.endswith('.png'):
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


def collect_data(g):
    user_config = config.get_config()
    user_input = input("Please input a game name or Steam URL: ").strip()

    if user_config['Toshokan']['use_external_id']:
        g['External ID'] = prompt_for_external_id()

    # Handle Steam
    steam_appid = None
    if user_config['Steam']['enabled']:
        print("\nSearching on Steam...")
        if 'store.steampowered.com/app/' in user_input:
            steam_appid = user_input.split('com/app/')[1].split('/')[0]
        else:
            steam_search_results = steam.search_for_game(user_input)
            chosen = select_from_list(steam_search_results)
            if len(chosen) != 0:
                steam_appid = chosen[0]['ID']
        if steam_appid is not None:
            steam_data = steam.download_data(steam_appid)
            if 'name' not in steam_data.keys():
                user_input = input("Delisted, please input name: ").strip()
            else:
                user_input = steam_data['name']
            steam_suggestions = steam.get_suggested_data(steam_data)
            if len(steam_data.keys()) == 0:
                g['External Links']['Steam']['Is Delisted'] = True
            else:
                webbrowser.open('https://store.steampowered.com/app/%s' % (steam_appid, )) 
            g['External Links']['Steam']['ID'] = steam_appid
            g['External Suggestions']['Steam'] = steam_suggestions

    # Handle PCGamingWiki
    if user_config['PCGamingWiki']['enabled']:
        pcgw_data = None
        if steam_appid is not None:
            pcgw_data = pcgamingwiki.download_data_by_steamid(steam_appid)
            if pcgw_data is not None:
                g['External Links']['PCGamingWiki']['Method'] = 'Steam AppID'
                g['External Links']['PCGamingWiki']['ID'] = steam_appid
        else:
            print("\nSearching on PCGamingWiki...")
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
        print("\nSearching on IGDB...")
        igdb_search_results = igdb.search_for_game(user_input)
        chosen = select_from_list(igdb_search_results)
        if len(chosen) != 0:
            igdb_data = igdb.get_full_game_info(chosen[0]['ID'])
            igdb_suggestions = igdb.get_suggested_data(igdb_data)
            g['External Links']['IGDB']['ID'] = chosen[0]['ID']
            g['External Suggestions']['IGDB'] = igdb_suggestions

    # Handle LaunchBox
    if user_config['LaunchBox']['enabled']:
        print("\nSearching on LaunchBox...")
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
        print("\nSearching on GameFAQs...")
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
                    print("\nUsing HowLongToBeat ID from PCGamingWiki...")
                    g['External Links']['HowLongToBeat']['ID'] = v['Value']
        else:
            try:
                print("\nSearching on HowLongToBeat...")
                hltb_search_results = howlongtobeat.search_for_game(user_input)
                chosen = select_from_list(hltb_search_results)
                if len(chosen) != 0:
                    g['External Links']['HowLongToBeat']['ID'] = chosen[0]['ID']
            except Exception as e:
                print("Unable to fetch HowLongToBeat: %s" % str(e))

    # Handle RetroAchievements
    if user_config['RetroAchievements']['enabled']:
        print("\nSearching on RetroAchievements...")
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
        # Use ID from PCGamingWiki if valid
        if user_config['PCGamingWiki']['enabled'] and pcgw_data is not None:
            for v in g['External Suggestions']['PCGamingWiki']:
                if v['Type'] == 'MobyGames ID':
                    print("\nUsing MobyGames ID from PCGamingWiki...")
                    g['External Links']['MobyGames']['ID'] = v['Value']
                    webbrowser.open('https://www.mobygames.com/game/%s' % (v['Value'], ))
        else:
            try:
                print("\nSearching on MobyGames...")
                mobygames_search_results = mobygames.search_for_game(user_input)
                chosen = select_from_list(mobygames_search_results)
                if len(chosen) != 0:
                    mobygames_data = mobygames.get_game_info(chosen[0]['ID'])
                    mobygames_suggestions = mobygames.get_suggested_data(mobygames_data)
                    g['External Links']['MobyGames']['ID'] = chosen[0]['ID']
                    g['External Suggestions']['MobyGames'] = mobygames_suggestions
                    webbrowser.open('https://www.mobygames.com/game/%s' % (chosen[0]['ID'], ))
            except Exception as e:
                print("Unable to fetch MobyGames: %s" % str(e))

    return g


def consolidate_type(game_data, attribute, cased=False):
    candidates = []
    used_candidates = []
    for data_source in game_data['External Suggestions'].keys():
        if data_source not in ['LaunchBox', 'RetroAchievements']:
            for obj in game_data['External Suggestions'][data_source]:
                if obj['Type'] == attribute:
                    check_term = str(obj['Value'])
                    if not cased:
                        check_term = check_term.lower()
                    if check_term not in used_candidates and check_term != '':
                        used_candidates.append(check_term)
                        candidates.append(obj)
                        candidates[-1]['Source'] = data_source
        else:
            for platform in game_data['External Suggestions'][data_source]:
                for obj in game_data['External Suggestions'][data_source][platform]:
                    if obj['Type'] == attribute:
                        check_term = str(obj['Value'])
                        if not cased:
                            check_term = check_term.lower()
                        if check_term not in used_candidates and check_term != '':
                            used_candidates.append(check_term)
                            candidates.append(obj)
                            candidates[-1]['Source'] = data_source
    candidate_objects = []
    for candid in candidates:
        c = candid.copy()
        c['Row'] = '%s [%s, %s]' % (c['Value'], c['Source'], c['Confidence'])
        candidate_objects.append(c)
    return sorted(candidate_objects, key=itemgetter('Confidence'), reverse=True)


def refine_data(game_data):
    print("\nFiltering aliases...")
    alias_candidate_objects = consolidate_type(game_data, 'Alias')
    aliases = exclude_from_list(alias_candidate_objects)
    game_data['Aliases'] = [x['Value'] for x in aliases]

    print("\nSelecting background...")
    bg_candidate_objects = consolidate_type(game_data, 'Background')
    chosen_bgs = choose_images('Background', bg_candidate_objects)
    if len(chosen_bgs) == 1:
        game_data['Background URL'] = chosen_bgs[0]['URL']
        storage.store_background(game_data['ID'], chosen_bgs[0]['Path'])

    print("\nSelecting cover...")
    cover_candidate_objects = consolidate_type(game_data, 'Cover')
    chosen_covers = choose_images('Cover', cover_candidate_objects)
    if len(chosen_covers) == 1:
        game_data['Cover URL'] = chosen_covers[0]['URL']
        storage.store_cover(game_data['ID'], chosen_covers[0]['Path'])

    print("\nFiltering descriptions...")
    description_candidate_objects = consolidate_type(game_data, 'Description')
    descriptions = select_from_list(description_candidate_objects)
    if len(descriptions) == 1:
        game_data['Description'] = descriptions[0]['Value']

    print("\nFiltering developers...")
    dev_candidate_objects = consolidate_type(game_data, 'Developer')
    devs = exclude_from_list(dev_candidate_objects)
    game_data['Developers'] = [x['Value'] for x in devs]

    print("\nFiltering franchises...")
    dev_candidate_objects = consolidate_type(game_data, 'Franchise')
    devs = exclude_from_list(dev_candidate_objects)
    game_data['Franchises'] = [x['Value'] for x in devs]

    print("\nFiltering genres...")
    genre_candidate_objects = consolidate_type(game_data, 'Genre')
    genres = exclude_from_list(genre_candidate_objects)
    game_data['Genres'] = [x['Value'] for x in genres]

    print("\nFiltering meta attributes...")
    meta_candidate_objects = consolidate_type(game_data, 'Meta')
    metas = exclude_from_list(meta_candidate_objects)
    game_data['Meta Attributes'] = [x['Value'] for x in metas]

    print("\nFiltering names...")
    name_candidate_objects = consolidate_type(game_data, 'Name', cased=True)
    if len(name_candidate_objects) == 1:
        names = name_candidate_objects
    else:
        names = select_from_list(name_candidate_objects)
    if len(names) == 1:
        game_data['Name'] = names[0]['Value']

    print("\nFiltering platforms...")
    platform_objects = consolidate_type(game_data, 'Platform')
    platforms = exclude_from_list(platform_objects)
    game_data['Platforms'] = [x['Value'] for x in platforms]

    print("\nFiltering publishers...")
    pub_candidate_objects = consolidate_type(game_data, 'Publisher')
    pubs = exclude_from_list(pub_candidate_objects)
    game_data['Publishers'] = [x['Value'] for x in pubs]

    print("\nSelecting screenshots...")
    ss_candidate_objects = consolidate_type(game_data, 'Screenshot')
    chosen_screenshots = choose_images('Screenshot', ss_candidate_objects)
    for i in range(0, len(chosen_screenshots)):
        game_data['Screenshot URLs'].append(chosen_screenshots[i]['URL'])
        storage.store_screenshot(game_data['ID'], chosen_screenshots[i]['Path'], i)

    print("\nFiltering series...")
    series_candidate_objects = consolidate_type(game_data, 'Series')
    if len(series_candidate_objects) > 0:
        series = exclude_from_list(series_candidate_objects)
        game_data['Series'] = [x['Value'] for x in series]

    print("\nFiltering tags...")
    tag_candidate_objects = consolidate_type(game_data, 'Tag')
    tags = exclude_from_list(tag_candidate_objects)
    game_data['Tags'] = [x['Value'] for x in tags]

    print("\nWould you like to add any custom tags? If so, input them, separated by spaces, now:")
    user_tags = input().split(' ')
    if user_tags[0] != '':
        game_data['Tags'] += user_tags

    print("\nFiltering videos...")
    video_candidate_objects = consolidate_type(game_data, 'Video')
    if len(video_candidate_objects) == 1:
        videos = video_candidate_objects
    else:
        videos = select_from_list(video_candidate_objects)
    if len(videos) == 1:
        if 'steamstatic' in videos[0]['Value']:
            game_data['Video URL'] = videos[0]['Value'].split('?')[0]
        else:
            game_data['Video URL'] = videos[0]['Value']

    print("\nFiltering years...")
    year_candidate_objects = consolidate_type(game_data, 'Year')
    if len(year_candidate_objects) == 1:
        years = year_candidate_objects
    else:
        years = select_from_list(year_candidate_objects)
    if len(years) == 1:
        if str(years[0]['Value']).isnumeric():
            game_data['Year'] = int(years[0]['Value'])

    print("\nChecking for other external links...")
    gog_candidate_objects = consolidate_type(game_data, 'GOG ID')
    if len(gog_candidate_objects) >= 1:
        game_data['External Links']['GOG'] = {}
        game_data['External Links']['GOG']['ID'] = gog_candidate_objects[0]['Value']
    twitch_candidate_objects = consolidate_type(game_data, 'Twitch ID')
    if len(twitch_candidate_objects) >= 1:
        game_data['External Links']['Twitch'] = {}
        game_data['External Links']['Twitch']['ID'] = twitch_candidate_objects[0]['Value']
    strategywiki_candidate_objects = consolidate_type(game_data, 'StrategyWiki ID')
    if len(strategywiki_candidate_objects) >= 1:
        game_data['External Links']['StrategyWiki'] = {}
        game_data['External Links']['StrategyWiki']['ID'] = strategywiki_candidate_objects[0]['Value']
    wikipedia_candidate_objects = consolidate_type(game_data, 'Wikipedia ID')
    if len(wikipedia_candidate_objects) >= 1:
        game_data['External Links']['Wikipedia'] = {}
        game_data['External Links']['Wikipedia']['ID'] = wikipedia_candidate_objects[0]['Value']
    googleplay_candidate_objects = consolidate_type(game_data, 'Google Play ID')
    if len(googleplay_candidate_objects) >= 1:
        game_data['External Links']['Google Play'] = {}
        game_data['External Links']['Google Play']['ID'] = googleplay_candidate_objects[0]['Value']

    return game_data


def add_new_game():
    g = game.new_game()
    id = storage.get_new_json_id()
    g['ID'] = id
    g = collect_data(g)
    g = refine_data(g)
    storage.store_json(g)
    storage.clean_workzone()
    storage.clean_temp()
