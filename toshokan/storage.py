import config
import json
import os
from PIL import Image
import requests
import uuid


def get_new_json_id():
    user_config = config.get_config()
    data_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Data')
    data_files = os.listdir(data_dir)
    # Short-circuit if no files are present, as you can't get the max of an empty list
    if len(data_files) == 0:
        return 1
    max_id = max([int(f.split('.')[0]) for f in data_files])
    return max_id + 1


def store_json(game_data):
    user_config = config.get_config()
    # Make the data directory if it does not exist
    data_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Data')
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    # Write the data to a json file
    datafile_path = os.path.join(data_dir, '%s.json' % game_data['ID'])
    with open(datafile_path, 'w', encoding='utf-8') as out_file:
        out_file.write(json.dumps(game_data, indent=4, sort_keys=True))


def load_json(id):
    user_config = config.get_config()
    data_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Data')
    # Load the data from a json file
    datafile_path = os.path.join(data_dir, '%s.json' % id)
    with open(datafile_path, 'r', encoding='utf-8') as in_file:
        game_data = json.load(in_file)
    return game_data


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


def store_background(id, file_path):
    user_config = config.get_config()
    bg_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Backgrounds')
    # Make the backgrounds directory if it does not exist
    if not os.path.exists(bg_dir):
        os.mkdir(bg_dir)
    bg_img_path = os.path.join(bg_dir, '%s.jpg' % id)
    os.rename(file_path, bg_img_path)


def store_cover(id, file_path):
    user_config = config.get_config()
    cover_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Covers')
    # Make the covers directory if it does not exist
    if not os.path.exists(cover_dir):
        os.mkdir(cover_dir)
    cover_img_path = os.path.join(cover_dir, '%s.jpg' % id)
    os.rename(file_path, cover_img_path)


def store_screenshot(id, file_path, number):
    user_config = config.get_config()
    ss_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Screenshots')
    # Make the screenshots directory if it does not exist
    if not os.path.exists(ss_dir):
        os.mkdir(ss_dir)
    # Expand into a game-specific folder
    game_ss_dir = os.path.join(ss_dir, str(id))
    if not os.path.exists(game_ss_dir):
        os.mkdir(game_ss_dir)
    ss_img_path = os.path.join(game_ss_dir, '%s.jpg' % number)
    os.rename(file_path, ss_img_path)


def clean_workzone():
    user_config = config.get_config()
    workzone_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Workzone')
    for wz_type in ['Background', 'Cover', 'Screenshot']:
        subdir = os.path.join(workzone_dir, wz_type)
        keepdir = os.path.join(subdir, 'Keep')
        if os.path.exists(subdir):
            for f in os.listdir(subdir):
                if str(f) not in ['desktop.ini', 'Keep']:
                    os.remove(os.path.join(subdir, f))
            if os.path.exists(keepdir):
                for f in os.listdir(keepdir):
                    if str(f) not in ['desktop.ini', 'Keep']:
                        os.remove(os.path.join(keepdir, f))


def clean_temp():
    user_config = config.get_config()
    temp_dir = os.path.join(user_config['Toshokan']['storage_path'], 'Temp')
    for f in os.listdir(temp_dir):
        if str(f) not in ['desktop.ini']:
            os.remove(os.path.join(temp_dir, f))
