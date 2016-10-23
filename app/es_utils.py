import requests
import arrow
import json

from flask import Flask, render_template, request, jsonify, url_for
from urllib import unquote_plus

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')


def _autocomplete(query):
    body = {
        "size": 5,
        "fields": [
            "title",
            "timestamp",
            "categories"
        ],
        "query": {
            "match": {
                "title": query
            }
        },
        "sort": [
            {"_score": {"order": "desc"}},
            {"timestamp": {
                "order": "desc",
                "mode": "max"
            }
            }
        ]
    }
    r = requests.post('{}/{}/_search'.format(app.config['ES_URL'], app.config['INDEX_NAME']),
                      data=json.dumps(body))
    data = {
        'autocomplete': [hit['fields']['title'][0] for hit in r.json()['hits']['hits']]
    }
    app.logger.debug('Autocomplete request: {} -> response: {}'.format(query, data))
    return data


def _search(query, start, size):
    body = {
        "from": start, "size": size,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "fields": ["title", "article", "author"],
                        "query": query,
                        "fuzziness": "AUTO"
                    }
                },
                "should": [
                    {
                        "range": {
                            "timestamp": {
                                "boost": 5,
                                "gte": "now-90d/d"
                            }
                        },
                        "range": {
                            "timestamp": {
                                "boost": 2,
                                "gte": "now-12m/d"
                            }
                        },
                        "range": {
                            "timestamp": {
                                "boost": 1,
                                "gte": "now-24m/d"
                            }
                        }
                    }
                ]
            }
        },
        "sort": [
            {"_score": {"order": "desc"}},
            {"timestamp": {
                "order": "desc",
                "mode": "max"
            }
            }
        ],
        "highlight": {
            "fields": {
                "title": {},
                "article": {},
                "author": {}
            }
        }
    }
    r = requests.post('{}/{}/_search'.format(app.config['ES_URL'], app.config['INDEX_NAME']),
                      data=json.dumps(body))
    results = []
    for hit in r.json()['hits']['hits']:
        results.append({
            'fields': hit['_source'],
            'highlight': hit['highlight'],
            'short_description': u'{}...'.format(hit['_source'].get('article', [])[:180])
        }
        )

    data = {
        'query': query,
        'query_time': r.json()['took'],
        'hits_total': r.json()['hits']['total'],
        'results': results if len(results) > 1 else results[0],
        'start': start,
        'size': size
    }
    app.logger.debug("Search query: {} -> result {}".format(query, json.dumps(data, indent=4, sort_keys=True)))

    return data


def _article(query):
    body = {
        "size": 1,
        "query": {
            "match": {
                "url": unquote_plus(query)
            }
        }
    }
    r = requests.post('{}/{}/_search'.format(app.config['ES_URL'], app.config['INDEX_NAME']),
                      data=json.dumps(body))
    results = []
    for hit in r.json()['hits']['hits']:
        results.append({
            'fields': hit['_source']
        }
        )

    data = {
        'query': query,
        'query_time': r.json()['took'],
        'hits_total': r.json()['hits']['total'],
        'results': results if len(results) > 1 else results[0],
    }

    return data


def _more_like_this(query, size=6):
    print query
    body = {
        "size": size,
        "query": {
            "more_like_this": {
                "fields": [
                    "article"
                ],
                "like_text": query,
                "min_term_freq": 1,
                "max_query_terms": 12
            }
        }
    }
    r = requests.post('{}/{}/_search'.format(app.config['ES_URL'], app.config['INDEX_NAME']),
                      data=json.dumps(body))
    results = []
    for hit in r.json()['hits']['hits']:
        results.append({
            'title': hit['_source']['title'],
            'url': hit['_source']['url'],
            'image_link': hit['_source']['image_link']
        }
        )
    data = {
        'query': query,
        'query_time': r.json()['took'],
        'hits_total': r.json()['hits']['total'],
        'results': results if len(results) > 1 else results[0]
    }

    return data


def _search_date(interval, date_from, date_to, size):
    body = {
        "size": size,
        "query": {
            "range": {
                "timestamp": {
                    "from": date_from,
                    "to": date_to
                }
            }
        },
        "aggregations": {
            "articles_over_time": {
                "date_histogram": {
                    "field": "timestamp",
                    "interval": interval
                }
            }
        },
        "sort": [
            {
                "timestamp": {
                    "order": "asc"
                }
            }
        ]
    }
    r = requests.post('{}/{}/_search'.format(app.config['ES_URL'], app.config['INDEX_NAME']),
                      data=json.dumps(body))

    buckets = []
    for bucket in r.json()['aggregations']['articles_over_time']['buckets']:
        buckets.append({
            arrow.get(bucket.get('key_as_string')).format('YYYY-MM-DD'): bucket.get('doc_count')
        })
    results = []
    for hit in r.json()['hits']['hits']:
        results.append({
            'fields': hit['_source'],
            'short_description': u'{}...'.format(hit['_source'].get('article', [])[:180])
        }
        )
    return {
        'results': results if len(results) > 1 else results[0],
        'buckets': buckets,
        'query': date_from,
        'query_time': r.json()['took']
    }


def _stats():
    # article stats, authors cardinality and categories cardinality
    body = {
        "size": 0,
        "query": {"match_all": {}},
        "aggs": {
            "articles_stats": {
                "stats": {
                    "script": "_source.article.toString().length()"
                }
            },
            "authors_count": {
                "cardinality": {
                    "field": "author"
                }
            },
            "categories_count": {
                "cardinality": {
                    "field": "categories"
                }
            }
        }
    }
    r = requests.post('{}/{}/_search'.format(app.config['ES_URL'], app.config['INDEX_NAME']),
                      data=json.dumps(body))

    return {
        'results': r.json()['aggregations'],
        'query_time': r.json()['took']
    }


def _articles_ln_histogram():
    body = {
        "size": 0,
        "aggs": {
            "articles_ln_histogram": {
                "histogram": {
                    "script": "_source.article.toString().length()",
                    "interval": 250
                }
            }
        }
    }
    r = requests.post('{}/{}/_search'.format(app.config['ES_URL'], app.config['INDEX_NAME']),
                      data=json.dumps(body))

    return {
        'results': r.json()['aggregations']['articles_ln_histogram'],
        'query_time': r.json()['took']
    }