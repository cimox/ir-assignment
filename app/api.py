import requests
import json
import arrow

from requests import ConnectionError
from flask import Flask, render_template, request, jsonify, url_for
from es_utils import _search, _article, _more_like_this
from urllib import quote_plus

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
    data = _search(query, start, size)
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


@app.route('/article/', methods=['POST'])
def article():
    article_url = quote_plus(request.form.get('query'))
    article = _article(article_url)
    similar = more_like_this(request.form.get('title'))
    return render_template('article.html', data=article, similar=similar)


@app.route('/like/<string:query>/', methods=['GET'])
def more_like_this(query):
    return _more_like_this(query)


@app.route('/')
def homepage(name='Matus Cimerman'):
    try:
        buckets = search_date('month', '2016', '2017', 10)['buckets']
    except ConnectionError:
        buckets = [{'Error': 'Elastic is down'}]
    data = {
        'name': name,
        'cookies': request.cookies,
        'buckets': buckets
    }
    return render_template('index.html', data=data)


if __name__ == '__main__':
    app.run(port=8080)
