from duckduckgo_search import DDGS


def search_for_game(name):
    resp = DDGS().text('%s site:howlongtobeat.com' % name, max_results=40)

    search_results = []
    for i in range(0, len(resp)):
        g = {}
        g['ID'] = resp[i]['href'].split('/game/')[-1]
        g['Row'] = resp[i]['title'] + ' [%s]' % g['ID']
        # Skip playthrough submission pages
        if '/submit/' in resp[i]['href']:
            continue
        # Skip non-main game pages (aka anything where the last portion
        # of the URL does not contain the HowLongToBeat ID)
        if not g['ID'].isnumeric():
            continue
        search_results.append(g)
    return search_results[:21]
