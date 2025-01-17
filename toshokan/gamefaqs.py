from duckduckgo_search import DDGS


def search_for_game(name):
    resp = DDGS().text('%s site:gamefaqs.gamespot.com' % name, max_results=40)

    search_results = []
    for i in range(0, len(resp)):
        g = {}
        g['Row'] = resp[i]['title']
        g['URL'] = resp[i]['href']
        # Skip forums
        if '/boards/' in g['URL']:
            continue
        # Skip videos
        if '/videos/' in g['URL']:
            continue
        # Skip news
        if '.com/news' in g['URL']:
            continue
        # Skip non-main game pages (aka anything where the last portion
        # of the URL does not contain the GameFAQs ID)
        if not g['URL'].split('/')[-1].split('-')[0].isnumeric():
            continue
        search_results.append(g)
    return search_results[:21]
