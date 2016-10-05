# -*- coding: utf-8 -*-
import json

INDEX_NAME = 'vinf'
INDEX_TYPE = 'articles'


class JsonWriterPipeline(object):

    def __init__(self):
        self.file = open('articles-new.json', 'wb')

    def process_item(self, item, spider):
        index = {
            'index': {
                '_index': INDEX_NAME,
                '_type': INDEX_TYPE,
                '_id': item['url']
            }
        }
        self.file.write(json.dumps(index) + '\n')
        self.file.write(json.dumps(item) + '\n')

        return item