import requests
import json
from flask import Flask, render_template, request, jsonify, url_for

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')


@app.route('/autocomplete/<string:query>/', methods=['POST'])
def autocomplete(query):
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
    return jsonify(data)


@app.route('/search/<string:query>/', methods=['POST', 'GET'], defaults={'start': 0, 'size': 10})
@app.route('/search/<string:query>/<int:start>/<int:size>/', methods=['POST', 'GET'])
def search(query, start, size):
    body = {
        "from": start, "size": size,
        "query": {
            "bool": {
                "must": {
                    "fuzzy": {
                        "title": query
                    }
                },
                "should": [
                    {
                        "range": {
                            "timestamp": {
                                "boost": 5,
                                "gte": "now-90d/d"
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
        'results': results,
        'start': start,
        'size': size
    }
    return render_template('search.html', data=data)


@app.route('/')
def homepage(name='Matus Cimerman'):
    data = {
        'name': name,
        'cookies': request.cookies,
    }
    return render_template('index.html', data=data)


if __name__ == '__main__':
    app.run(port=8080)
