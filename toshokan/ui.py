def select_from_list(options):
    for i in range(0, len(options)):
        print('%s. %s' % (i, options[i]['Row']))
    print()
    user_input = input("Select an option: ").strip()
    if not user_input.isnumeric():
        return None
    else:
        return options[int(user_input)]


def choose_cover(options):
    pass


def choose_screenshots(options):
    pass


def choose_tags(suggestions):
    pass


def choose_platforms(suggestions):
    pass


def add_new_game():
    user_input = input("Please input a game name or Steam URL: ").strip()
