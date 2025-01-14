from bs4 import BeautifulSoup
import config
import os


def load_db():
    user_config = config.get_config()
    launchbox_settings = user_config['LaunchBox']
    launchbox_size = os.path.getsize(launchbox_settings['path_to_metadata_xml'])
    if launchbox_size != launchbox_settings['last_db_size']:
        with open(launchbox_settings['path_to_metadata_xml'], 'r', encoding='utf-8') as in_file:
            temp_data = in_file.read()
        launchbox_db = BeautifulSoup(temp_data, "xml")
        user_config = config.set_option('LaunchBox', 'last_db_size', launchbox_size)
        config.save_config(user_config)
    return launchbox_db
