import config
import ui

user_config = config.get_config()
config.save_config(user_config)

ui.add_new_game()
