import config
import launchbox

user_config = config.get_config()
config.save_config(user_config)

launchbox.xml_to_sqlite()
test = launchbox.find_game_by_name("Pokemon FireRed")
for t in test:
    print(t)
