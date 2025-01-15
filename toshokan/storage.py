import config
import json
import os
from PIL import Image
import requests
import uuid


def store_json(data):
    user_config = config.get_config()
    # Make the data directory if it does not exist
    data_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Data')
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    # Write the data to a json file
    datafile_path = os.path.join(data_dir, '%s.json' % data['ID'])
    with open(datafile_path, 'w', encoding='utf-8') as out_file:
        out_file.write(json.dumps(data, indent=4, sort_keys=True))


def load_json(id):
    user_config = config.get_config()
    data_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Data')
    # Load the data from a json file
    datafile_path = os.path.join(data_dir, '%s.json' % id)
    with open(datafile_path, 'r', encoding='utf-8') as in_file:
        data = json.load(in_file)
    return data


def download_image(url):
    user_config = config.get_config()
    temp_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Temp')
    # Make the temp directory if it does not exist
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    file_type = url.split('.')[-1]
    temp_file_name = '%s.temp.%s' % (str(uuid.uuid4()), file_type.lower())
    temp_file_path = os.path.join(temp_dir, temp_file_name)
    file_name = '%s.jpg' % (str(uuid.uuid4()), )
    file_path = os.path.join(temp_dir, file_name)
    r = requests.get(url)
    with open(temp_file_path, 'wb') as out_file:
        out_file.write(r.content)
    with Image.open(temp_file_path).convert('RGB') as img:
        img.thumbnail((1000, 1000), Image.LANCZOS)
        img.save(file_path, quality=90)
    return file_path


def store_cover(id, temp_file):
    user_config = config.get_config()
    cover_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Covers')
    # Make the covers directory if it does not exist
    if not os.path.exists(cover_dir):
        os.mkdir(cover_dir)
    cover_img_path = os.path.join(cover_dir, '%s.jpg' % id)
    os.rename(temp_file, cover_img_path)


def store_screenshot(id, temp_file, number):
    user_config = config.get_config()
    ss_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Screenshots')
    # Make the screenshots directory if it does not exist
    if not os.path.exists(ss_dir):
        os.mkdir(ss_dir)
    # Expand into a game-specific folder
    game_ss_dir = os.path.join(ss_dir, id)
    if not os.path.exists(game_ss_dir):
        os.mkdir(game_ss_dir)
    ss_img_path = os.path.join(game_ss_dir, '%s.jpg' % number)
    os.rename(temp_file, ss_img_path)
