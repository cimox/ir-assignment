import requests
import json

from flask import Flask, render_template, request, jsonify, url_for
from urllib import unquote_plus

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')


def _search(query, start, size):
    body = {
        "from": start, "size": size,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "fields": ["title"],
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
                "title": {}
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
                    "title", "article"
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
