import json
import os

config_path = os.path.join(os.path.expanduser('~'), '.toshokan.json')

base_options = {
    "GameFAQs": {
        "enabled": False,
        # What search engine to use for GameFAQs - not recommended if
        # enough other data sources are enabled, as they'll often have
        # GameFAQs links to pull automatically.
        "search_method": 'none',
    },
    "HowLongToBeat": {
        "enabled": False,
    },
    "IGDB": {
        "enabled": False,
    },
    "LaunchBox": {
        "enabled": False,
        # The size the last time the DB was imported - do not edit this manually.
        "last_db_size": 0,
        # The path to the LaunchBox XML.
        "path_to_metadata_xml": str(os.path.join(os.path.join(os.path.expanduser('~')), 'LaunchBox/Metadata/Metadata.xml')),
    },
    "MobyGames": {
        "enabled": False,
    },
    "PCGamingWiki": {
        "enabled": False,
    },
    "RetroAchievements": {
        "enabled": False,
    },
    "Steam": {
        "enabled": False,
    },
    "SteamGridDB": {
        "enabled": False,
    },
    "Toshokan": {
        # The maximum number of screenshots to store when building an entry
        "screenshots": 4,
        # The directory that Toshokan should store harvested data in.
        "storage_path": "",
        # Whether or not you want to store a legacy ID for converting old entries.
        # If you don't already have a database from another program, you don't need this.
        "use_legacy_id": False,
    }
}


def template_config(user_config):
    for data_source in base_options.keys():
        # Add each data source if it does not yet exist
        if data_source not in user_config.keys():
            user_config[data_source] = {}
        # Add sub options for the current data source if they do not exist
        for sub_option in base_options[data_source].keys():
            if sub_option not in user_config[data_source].keys():
                user_config[data_source][sub_option] = base_options[data_source][sub_option]
    return user_config


def get_config():
    if os.path.exists(config_path):
        with open(config_path) as in_file:
            user_config = json.load(in_file)
    else:
        user_config = {}
    user_config = template_config(user_config)
    return user_config


def save_config(user_config):
    with open(config_path, 'w') as out_file:
        out_file.write(json.dumps(user_config, indent=4, sort_keys=True))


def set_option(user_config, data_source, sub_option, data_value):
    if data_source not in user_config.keys():
        raise ValueError("%s is not a valid data source!" % str(data_source))
    if sub_option not in user_config[data_source].keys():
        raise ValueError("%s is not a valid option for %s!" % (str(sub_option), str(data_source)))
    user_config[data_source][sub_option] = data_value
    return user_config
