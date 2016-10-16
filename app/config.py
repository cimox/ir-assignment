class Config(object):
    DEBUG = False
    TESTING = False
    ES_URL = 'http://localhost:9200/'
    INDEX_NAME = 'vinf_fin'
    INDEX_TYPE = 'articles'


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
