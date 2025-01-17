import config
import game
import gamefaqs
import howlongtobeat
import igdb
import launchbox
import pcgamingwiki
import retroachievements
import steam
import storage


def select_from_list(options):
    for i in range(0, len(options)):
        print('%s. %s' % (i, options[i]['Row']))
    print()
    user_input = input("Select an option: ").strip()
    if not user_input.isnumeric():
        return None
    else:
        return options[int(user_input)]


def prompt_for_external_id():
    user_config = config.get_config()
    external_id = input("External ID: ")
    if external_id.isnumeric():
        external_id = int(external_id)
    else:
        external_id = user_config['Toshokan']['highest_seen_external_id'] + 1
    # Update the highest seen external ID if it's larger than the previous
    if external_id > user_config['Toshokan']['highest_seen_external_id']:
        config.set_option(user_config, 'Toshokan', 'highest_seen_external_id', external_id)
    return external_id


def choose_background(options):
    pass


def choose_cover(options):
    pass


def choose_screenshots(options):
    pass


def choose_tags(suggestions):
    pass


def choose_platforms(suggestions):
    pass


def add_new_game():
    g = game.new_game()
    id = storage.get_new_json_id()
    g['ID'] = id
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
            if chosen is not None:
                steam_appid = chosen['ID']
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
            if chosen is not None:
                pcgw_data = pcgamingwiki.download_data_by_page_title(chosen['Row'])
                g['External Links']['PCGamingWiki']['Method'] = 'Title'
                g['External Links']['PCGamingWiki']['ID'] = chosen['Row']
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
        if chosen is not None:
            igdb_data = igdb.get_full_game_info(chosen['ID'])
            igdb_suggestions = igdb.get_suggested_data(igdb_data)
            g['External Links']['IGDB']['ID'] = chosen['ID']
            g['External Suggestions']['IGDB'] = igdb_suggestions

    # Handle LaunchBox
    if user_config['LaunchBox']['enabled']:
        print("Searching on LaunchBox...")
        launchbox_search_results = launchbox.search_for_game(user_input)
        chosen = select_from_list(launchbox_search_results)
        if chosen is not None:
            launchbox_data = launchbox.get_full_game_info(chosen['ID'])
            launchbox_suggestions = launchbox.get_suggested_data(launchbox_data)
            g['External Links']['LaunchBox']['ID'] = chosen['ID']
            g['External Suggestions']['LaunchBox'] = launchbox_suggestions

    # Handle GameFAQs
    if user_config['GameFAQs']['enabled']:
        print("Searching on GameFAQs...")
        gamefaqs_search_results = gamefaqs.search_for_game(user_input)
        chosen = select_from_list(gamefaqs_search_results)
        if chosen is not None:
            g['External Links']['GameFAQs']['URL'] = chosen['URL']

    # Handle HowLongToBeat
    if user_config['HowLongToBeat']['enabled']:
        # TODO: Use ID from PCGamingWiki if valid
        print("Searching on HowLongToBeat...")
        hltb_search_results = howlongtobeat.search_for_game(user_input)
        chosen = select_from_list(hltb_search_results)
        if chosen is not None:
            g['External Links']['HowLongToBeat']['ID'] = chosen['ID']

    # Handle RetroAchievements
    if user_config['RetroAchievements']['enabled']:
        print("Searching on RetroAchievements...")
        retroachievements_search_results = retroachievements.search_for_game(user_input)
        chosen = select_from_list(retroachievements_search_results)
        if chosen is not None:
            retroachievements_data = retroachievements.get_game_info(chosen['ID'])
            retroachievements_suggestions = retroachievements.get_suggested_data(retroachievements_data)
            g['External Links']['RetroAchievements']['ID'] = chosen['ID']
            g['External Suggestions']['RetroAchievements'] = retroachievements_suggestions

    storage.store_json(g)
