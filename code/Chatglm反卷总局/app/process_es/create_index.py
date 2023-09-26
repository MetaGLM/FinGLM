from elasticsearch import Elasticsearch, helpers
import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

def create_index():

    es = Elasticsearch([config['es']['es_host']],
                       http_auth=(config['es']['es_user'], config['es']['es_passwd']))

    # 创建ES
    es_setting = {
        "settings": {
            "index": {
                "refresh_interval": "30s",
                "number_of_shards": "1",
                "number_of_replicas": "0"
            }
        },
        "mappings": {
            "properties": {
                "code": {
                    "type": "keyword",
                    "ignore_above": 100
                },
                "companys": {
                    "type": "keyword",
                    "ignore_above": 100
                },
                "embedding": {
                    "type": "dense_vector",
                    "dims": 768
                },
                "file_path": {
                    "type": "keyword",
                    "ignore_above": 100
                },
                "last_title": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 100
                        }
                    },
                    "analyzer": "ik_max_word"
                },
                "texts": {
                    "type": "text",
                    "analyzer": "ik_max_word"
                },
                "titles": {
                    "type": "keyword",
                    "ignore_above": 100
                },
                "titles_cut": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 100
                        }
                    },
                    "analyzer": "ik_max_word"
                },
                "year": {
                    "type": "keyword",
                    "ignore_above": 100
                },
                "keyword": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 100
                        }
                    },
                    "analyzer": "ik_max_word"
                }
            }
        }
    }

    es.indices.create(index=config["es"]["es_normal_index"], body=es_setting)
    es.indices.create(index=config["es"]["es_sentence_index"], body=es_setting)
