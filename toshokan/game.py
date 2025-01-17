import config
import storage


def _add_missing_fields(game_data):
    toshokan_defaults = {
        'Aliases': [],
        'Background URL': None,
        'Base Rating': 60,
        'Cover URL': None,
        'Description': None,
        'External Links': {},
        'External Suggestions': {},
        'Genres': [],
        'Meta Attributes': [],
        'Name': None,
        'Platforms': [],
        'Screenshot URLs': [],
        'Tags': [],
        'Video URL': None,
        'Year': 2999,
    }
    user_config = config.get_config()
    # Add base data fields if missing
    for field in toshokan_defaults.keys():
        if field not in game_data.keys():
            game_data[field] = toshokan_defaults[field]
    # Add External ID field if enabled
    if user_config['Toshokan']['use_external_id']:
        game_data['External ID'] = None
    # Add external data fields if missing and enabled
    for data_source in user_config.keys():
        if data_source not in game_data['External Links'].keys():
            game_data['External Links'][data_source] = {}
    # Add some misc. data
    print(game_data)
    game_data['External Links']['Steam']['Is Delisted'] = False
    return game_data


def new_game():
    template = {}
    template = _add_missing_fields(template)
    return template


def load_game_from_file(id):
    game_data = storage.load_json(id)
    # We need to add fields on load, just in case it's an old file
    return _add_missing_fields(game_data)


def get_platform_template():
    return {
        'External Links': {},
        'Platform': None,
        'Year': None,
    }
