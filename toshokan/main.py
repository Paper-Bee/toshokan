import config
import howlongtobeat
import ui

user_config = config.get_config()
config.save_config(user_config)

# ui.add_new_game()
ui.select_from_list(howlongtobeat.search_for_game('Bee Simulator'))
