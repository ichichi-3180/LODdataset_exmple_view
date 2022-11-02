from SPARQLWrapper import SPARQLWrapper
from sqlalchemy.sql.expression import false, true
from app.models.models import Sparqlendpoint, Prefix, Class,Triple
from app.models.db import db_session
import json
import re
import urllib.parse
import os
from graphviz import Source
import copy
import collections
import pprint
import csv
import math
# from sqlalchemy.dialects.sqlite import insert
import glob
import sqlite3


# endpoint = 'http://localhost:3030/NDL'
# endpoint = 'http://localhost:3030/sample_isil'
# endpoint = 'http://localhost:3030/onsen_sample'
# endpoint = 'http://localhost:3030/NDL_sample_1000_from_public'
# endpoint = 'http://localhost:3030/onsen' # inbound->Personクラス instance->HotSpringクラス
# endpoint = 'http://localhost:3030/botanical' # inbound->Placeクラス instance->Plantクラス
# endpoint = 'http://localhost:3030/vtuber' # inbound->Personクラス instance->VideoObjectクラス
# endpoint = 'http://localhost:3030/omiyage'
# endpoint='https://id.ndl.go.jp/auth/ndla/sparql'
endpoint = 'http://localhost:3030/textbook'
# endpoint = 'http://localhost:3030/isil'
# endpoint = 'http://localhost:3030/vlueprint'
# endpoint = 'http://localhost:3030/media-arts-db'
# endpoint = 'https://sparql.metadata.moe/madb/query'
# endpoint = 'https://sparql.city.kyoto.lg.jp/sparql/'
# endpoint = 'https://lib-lod.tsunagun.org/sparql/isil-lod-jp/query'
# endpoint = 'http://localhost:3030/LOV'

sparql = SPARQLWrapper(endpoint=endpoint, returnFormat='json')

# クラス間関係の画像を生成し、static/img内に配置

# 出力先のフォルダを指定
con=sqlite3.connect('app/models/graduation_research.db')
cur=con.cursor()
cur.execute("SELECT * from sparql_endpoint WHERE local_url=?", (endpoint,))
endpoint_info = cur.fetchone() #(id, url, name)
if not os.path.exists('app/static/img/' + str(endpoint_info[0]) + '/'):
    os.makedirs('app/static/img/' + str(endpoint_info[0]) + '/')


# クラス間関係を取得[]
def get_class():
    class_list = []
    query = """
        select distinct ?class where{
            ?s a ?class .
        }
    """
    print(query)
    sparql.setQuery(query)
    results = sparql.query().convert()
    # print(results["results"]["bindings"][0]["class"]["value"])
    for result in results["results"]["bindings"]:
        # print(result["class"]["value"])
        class_list.append(result["class"]["value"])
    return class_list

def get_class_relation(class1, class2):
    property_list = []
    query = """
        select distinct ?p where{{
            ?o a <{class2}> .
            ?s ?p ?o .
            {{
                select distinct ?s where{{
                    ?s a <{class1}> .
                }}
            }}
        }}
    """
    query = query.format(class1 = class1, class2 = class2)
    print(query)
    sparql.setQuery(query)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
        property_list.append(result["p"]["value"])
    return property_list


class_list = get_class()


class_relation_list = []
for class1 in class_list:
    for class2 in class_list:
        property_list = get_class_relation(class1, class2)
        for property in property_list:
            class_relation_list.append([class1, property, class2])

with open('app/static/img/' + str(endpoint_info[0]) + '/' + 'class_relation.csv', 'w') as f:
    writer = csv.writer(f, lineterminator='\n')
    writer.writerows(class_relation_list)

# 取得したクラス間関係から、表示用の文字列に変更
def judge_prefix_or_name_space(prefix): # 入力したものがprefixならばTrueを、name_spaceならばFalseを返す
    if re.match('^http(s)?://.*', prefix) != None:
        return False
    else:
        return True

def get_prefix_id_prefix_name(uri):
    if len(urllib.parse.urlparse(uri).fragment) == 0:
        name_space = urllib.parse.urlparse(uri).scheme + '://' + urllib.parse.urlparse(uri).netloc + urllib.parse.urlparse(uri).path
        right_slash_pos = name_space.rfind('/')
        name = name_space[right_slash_pos+1:]
        name_space = name_space[:right_slash_pos+1]
    else:
        name_space = urllib.parse.urlparse(uri).scheme + '://' + urllib.parse.urlparse(uri).netloc + urllib.parse.urlparse(uri).path + '#'
        name = urllib.parse.urlparse(uri).fragment

    # print(prefix)
    # print(name)
    print(uri)
    prefix_infos = db_session.query(Prefix).filter_by(name_space=name_space).all()
    if len(prefix_infos) != 0: # namespace(名前空間の省略していないバージョン)に対応するpreifx(接頭辞), prefix_idが存在すれば
        for prefix_info in prefix_infos:
            prefix_id = prefix_info.id
            prefix = prefix_info.prefix
            # print(prefix_id)
    else: # namespaceに対応しているデータがない場合、新しく追加し、取得し直す
        p = Prefix(name_space, name_space)
        db_session.add(p)
        db_session.commit()
        db_session.close()
        prefix_id_prefix_name_list = get_prefix_id_prefix_name(uri)
        prefix_id = prefix_id_prefix_name_list[0]
        prefix = prefix_id_prefix_name_list[1]
    return prefix_id,  prefix, name

# 登録したクラス情報に基づいて、クラス間関係のdotファイル, png, svgを作成
done_prefix_check_class_relation_list = []
for class_relation in class_relation_list:
    done_prefix_check_class_relation = []
    for i in range(3):
        class_prefix_id_prefix_name = get_prefix_id_prefix_name(class_relation[i])
        if judge_prefix_or_name_space(class_prefix_id_prefix_name[1]):
            done_prefix_check_class_relation.append(class_prefix_id_prefix_name[1] + ':' + class_prefix_id_prefix_name[2])
        else:
            done_prefix_check_class_relation.append(class_prefix_id_prefix_name[1] + class_prefix_id_prefix_name[2])
    done_prefix_check_class_relation_list.append(done_prefix_check_class_relation)

structure_dot = """digraph{
    graph [rankdir = LR];
"""
for done_prefix_check_class_relation in done_prefix_check_class_relation_list:
    print(done_prefix_check_class_relation)
    structure_dot += '\"' + done_prefix_check_class_relation[0] + '\"->\"' + done_prefix_check_class_relation[2] + '\"[label=\"' + done_prefix_check_class_relation[1] + '\"]\n'
structure_dot += '}'

s = Source(structure_dot)
s.render('app/static/img/' + str(endpoint_info[0]) + '/structure', format='png')
s.render('app/static/img/' + str(endpoint_info[0]) + '/structure', format='svg')