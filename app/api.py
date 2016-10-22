import requests
import json
import arrow

from requests import ConnectionError
from flask import Flask, render_template, request, jsonify, url_for
from es_utils import _search, _article, _more_like_this, _autocomplete, _search_date, _stats, _articles_ln_histogram
from urllib import quote_plus

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')


@app.route('/autocomplete/<string:query>/', methods=['POST'])
def autocomplete(query):
    data = _autocomplete(query)
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
def dates(interval, date_from, date_to, size):
    data = _search_date(interval, date_from, date_to, size)
    return render_template('dates.html', data=data)


@app.route('/article/', methods=['POST'])
def article():
    article_url = quote_plus(request.form.get('query'))
    article = _article(article_url)
    similar = more_like_this(request.form.get('title'))
    return render_template('article.html', data=article, similar=similar)


@app.route('/like/<string:query>/', methods=['GET'])
def more_like_this(query):
    return _more_like_this(query)


@app.route('/articles_over_time/', methods=['GET'])
def articles_over_time():
    try:
        buckets = _search_date('month', '2015', '2017', 20)['buckets']
    except ConnectionError:
        buckets = [{'Error': 'Elastic is down'}]

    dates = []
    values = []
    for bucket in buckets:
        for date, value in bucket.items():
            dates.append(date)
            values.append(value)
    data = {
        'articles_over_time': {
            'dates': dates,
            'values': values
        }
    }
    return jsonify(data)


@app.route('/articles_ln_histogram/', methods=['GET'])
def articles_ln_hisogram():
    try:
        buckets = _articles_ln_histogram()['results']['buckets']
    except ConnectionError:
        buckets = [{'Error': 'Elastic is down'}]

    # lengths = []
    # counts = []
    # for bucket in buckets:
    #     lengths.append(bucket['key'])
    #     counts.append(bucket['doc_count'])
    # data = {
    #     'articles_ln_histogram': {
    #         'lengths': lengths,
    #         'counts': counts
    #     }
    # }
    data_array = []
    for b in buckets:
        if b['doc_count'] > 15 and b['key'] > 0:
            data_array.append((b['key'], b['doc_count']))
    data = {
        'articles_ln_histogram': data_array
    }
    return jsonify(data)


@app.route('/')
def homepage(name='Matus Cimerman'):
    data = {
        'name': name,
        'cookies': request.cookies,
        'desc_stats': _stats()
    }
    return render_template('index.html', data=data)


if __name__ == '__main__':
    app.run(port=8080)
