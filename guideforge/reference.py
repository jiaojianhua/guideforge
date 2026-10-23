import requests

ENDPOINT = "https://query.wikidata.org/sparql"
UA = {"User-Agent": "guideforge/0.1 (open-source content tool)"}

SPARQL = """
SELECT ?itemLabel (MAX(?links) AS ?sitelinks) WHERE {
  ?item wdt:P31/wdt:P279* wd:Q570116 .
  ?item wdt:P131* wd:%s .
  ?item wikibase:sitelinks ?links .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "%s,en". }
}
GROUP BY ?item ?itemLabel
ORDER BY DESC(?sitelinks)
LIMIT %d
"""


def fetch_reference(city_qid, lang="en", limit=40):
    r = requests.get(
        ENDPOINT,
        params={"query": SPARQL % (city_qid, lang, limit)},
        headers={**UA, "Accept": "application/sparql-results+json"},
        timeout=(10, 25),
    )
    r.raise_for_status()
    rows = r.json().get("results", {}).get("bindings", [])
    return [row["itemLabel"]["value"] for row in rows if row.get("itemLabel")]
