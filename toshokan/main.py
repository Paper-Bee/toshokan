import config
import launchbox
import steam

user_config = config.get_config()
config.save_config(user_config)

lbdata = launchbox.get_full_game_info('173402')
print(launchbox.get_suggested_data(lbdata))

steamdata = steam.download_data('914750')
print(steam.get_suggested_data(steamdata))
