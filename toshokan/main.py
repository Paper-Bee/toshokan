import config
import steam

user_config = config.get_config()
config.save_config(user_config)

for x in steam.search_for_game("Bee Simulator"):
    print(x)
