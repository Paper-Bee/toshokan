import config
import launchbox

user_config = config.get_config()
config.save_config(user_config)

launchbox.xml_to_sqlite()
