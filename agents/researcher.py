from tools.github_fetcher import github_fetch

def search(user):
    queries = [
        f"{user} full project",
        f"{user} source code"
    ]

    results = []

    for q in queries:
        try:
            r = github_fetch(q)
            if r:
                results.extend(r)
        except:
            pass

    return list(set(results))