import json
import os

config_path = os.path.join(os.path.expanduser('~'), '.toshokan.json')


def get_base_options():
    return {
        # GameFAQs is store-only, we never reach out to their site.
        "GameFAQs": {
            "enabled": False,
        },
        "HowLongToBeat": {
            "enabled": False,
        },
        "IGDB": {
            # Access token is automatically obtained/updated
            "access_token": '',
            # Client ID and Secret are obtained from Twitch
            "client_id": '',
            "client_secret": '',
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
            "api_key": "",
            "enabled": False,
        },
        "PCGamingWiki": {
            "enabled": False,
        },
        "RetroAchievements": {
            "api_key": "",
            "enabled": False,
        },
        "Steam": {
            "enabled": False,
        },
        "Toshokan": {
            # If use_external_id is true and you don't input one when prompted,
            # it will instead use this value + 1. Automatically updated when you
            # input an external ID.
            "highest_seen_external_id": 0,
            # The maximum number of screenshots to store when building an entry
            "screenshots": 4,
            # The directory that Toshokan should store harvested data in.
            "storage_path": "",
            # Whether or not you want to store a external ID for syncing external entries.
            # If you don't already have a database from another program, you don't need this.
            "use_external_id": False,
        }
    }


def template_config(user_config):
    base_options = get_base_options()
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
