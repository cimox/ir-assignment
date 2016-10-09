import requests
import json
import arrow

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
                    "match": {
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
        'results': results,
        'start': start,
        'size': size
    }
    return render_template('search.html', data=data)


@app.route('/date/', methods=['POST', 'GET'],
           defaults={'interval': 'month', 'date_from': '2016', 'date_to': '2090', 'size': 10})
@app.route('/date/<string:interval>/<string:date_from>/', methods=['POST', 'GET'],
           defaults={'date_to': '2090', 'size': 10})
@app.route('/date/<string:interval>/<string:date_from>/<string:date_to>/<int:size>/', methods=['POST', 'GET'])
def search_date(interval, date_from, date_to, size):
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
        "aggs": {
            "articles_over_time": {
                "date_histogram": {
                    "field": "timestamp",
                    "interval": interval
                }
            }
        }
    }
    r = requests.post('{}/{}/_search'.format(app.config['ES_URL'], app.config['INDEX_NAME']),
                      data=json.dumps(body))

    buckets = []
    for bucket in r.json()['aggregations']['articles_over_time']['buckets']:
        buckets.append({
            arrow.get(bucket.get('key_as_string')).format('YYYY-MM-DD'): bucket.get('doc_count')
        })
    data = {
        'articles': r.json()['hits']['hits'],
        'buckets': buckets
    }

    return data


@app.route('/')
def homepage(name='Matus Cimerman'):
    data = {
        'name': name,
        'cookies': request.cookies,
        'buckets': search_date('month', '2016', '2017', 10)['buckets']
    }
    return render_template('index.html', data=data)


if __name__ == '__main__':
    app.run(port=8080)
