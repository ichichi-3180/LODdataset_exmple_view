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
# endpoint = 'http://localhost:3030/NDL_sample_1000_from_public'
# endpoint = 'http://localhost:3030/onsen_sample'
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
# endpoint = 'http://localhost:3030/AGROVOC_2021_12'
# endpoint = 'http://data.yafjp.org/sparql'

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

def get_class_id_from_url(url):
    class_prefix_id_prefix_name = get_prefix_id_prefix_name(url)
    class_prefix_id = class_prefix_id_prefix_name[0]
    class_prefix = class_prefix_id_prefix_name[1]
    class_name = class_prefix_id_prefix_name[2]
    class_infos = db_session.query(Class).filter_by(endpoint_id=endpoint_info[0], prefix_id=class_prefix_id, name=class_name).all()
    class_id = ''
    for class_info in class_infos:
        class_id = class_info.id
    return class_id


# エンドポイントテーブルにendpoint_url, endpoint_nameを入れる
con=sqlite3.connect('app/models/graduation_research.db')
cur=con.cursor()
sql='INSERT OR IGNORE INTO sparql_endpoint (local_url, name) VALUES (?, ?)'
endpoint_name = urllib.parse.urlparse(endpoint).path
data = [endpoint, endpoint_name[1:]]
cur.execute(sql, data)
con.commit()
con.close()


# 現在選択中のエンドポイントの情報を取得
con=sqlite3.connect('app/models/graduation_research.db')
cur=con.cursor()
cur.execute("SELECT * from sparql_endpoint WHERE local_url=?", (endpoint,))
endpoint_info = cur.fetchone() #(id, url, name)
con.close()

# 各クラスの情報を登録していく
sparql = SPARQLWrapper(endpoint=endpoint, returnFormat='json')

directory = urllib.parse.urlparse(endpoint).netloc + urllib.parse.urlparse(endpoint).path 
directory = directory.replace("/", "_")
input_path =  directory +'/' 
class_structure = json.load(open(input_path + 'class_structure.json'))

for each_class_name in class_structure.keys():
    # 情報を取得するためのパスを設定
    input_class_directory = urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).netloc + urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).path
    if urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).fragment:
        input_class_directory += '#' + urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).fragment
    input_class_directory = input_class_directory.replace("/", "_")

    # クラス情報をデータベースに登録
    # 現在選択中のクラス名(each_class_name)をPrefixテーブルのprefix_idと名前に分ける
    prefix_id_and_name = get_prefix_id_prefix_name(each_class_name)
    class_name_prefix_id = prefix_id_and_name[0]
    class_name = prefix_id_and_name[2]
    con=sqlite3.connect('app/models/graduation_research.db')
    cur=con.cursor()
    sql='INSERT OR IGNORE INTO class (endpoint_id, prefix_id, name ) VALUES (?, ?, ?)'
    data = [endpoint_info[0], class_name_prefix_id, class_name]
    cur.execute(sql, data)
    con.commit()
    con.close()


bnode_num = 0 # トリプルだけでbnodeを識別できるようにするための番号
for each_class_name in class_structure.keys():
    # 情報を取得するためのパスを設定
    input_class_directory = urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).netloc + urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).path
    if urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).fragment:
        input_class_directory += '#' + urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).fragment
    input_class_directory = input_class_directory.replace("/", "_")

    # クラスを開始ノードとした構造情報を取得する

    # Tripleテーブルにデータをinput
    # inputするためのデータを取得する
    resource_csv_list = glob.glob(input_path + input_class_directory + '/instance_list/*/instance_list.csv')
    
    output_triple_list = [] # dbに入れるためのトリプルリスト
    for resource_csv in resource_csv_list:

        csv_file =  open(resource_csv, "r", encoding="utf-8", errors="", newline="" )
        f = csv.reader(csv_file, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)

        triple_list = [] #取得したトリプルを格納する配列
        for row in f:
            triple_list.append(row)

        bnode_dict = {} #key→csv上のbnode番号(^b\d+), value→dbに入れる用のbnode番号(^B\d+)

        # レンジのbnodeをチェック
        for triple in triple_list:
            if triple[4] == 'bnode': #現在選択中のトリプルのレンジのデータ型が空白ノードだった場合
                if not triple[3] in bnode_dict.keys(): # 現在選択中のトリプルのレンジのデータ(空白ノード)をキーとする値が登録されていなかったら
                    bnode_num += 1 #dbに入れるようのbnode番号を更新
                    bnode_dict[triple[3]] = 'B'+str(bnode_num) 
        # ドメイン
        for triple in triple_list:
            if re.match('^b\d+', triple[1]) != None and triple[0] != 'bnode': # ドメインがbnodeかつクラスの場合
                if not triple[1] in bnode_dict.keys():
                    bnode_num += 1 #dbに入れるようのbnode番号を更新
                    bnode_dict[triple[1]] = 'B'+str(bnode_num) 
        
        for triple in triple_list:
            # ドメイン
            if triple[1] in bnode_dict: #現在選択中のトリプルのドメインをkeyとするvalueが存在する場合(すでに現在のトリプルのドメインをハッシュに登録していた場合)
                output_domain_data = bnode_dict[triple[1]]
                if triple[0] != 'bnode': # ドメインがクラスの場合
                    output_domain_datatype = get_class_id_from_url(each_class_name)
                else: # ドメインがbnodeの場合
                    output_domain_datatype = triple[0]
            elif re.match('^b\d+', triple[1]) != None and triple[0] == 'bnode': # ドメインがb~であり、ドメインのデータ型がbnodeな場合
                bnode_num += 1 #dbに入れるようのbnode番号を更新
                output_domain_data = 'B'+str(bnode_num) 
                output_domain_datatype = triple[0]
            elif re.match('^b\d+', triple[1]) != None and triple[0] != 'bnode': # ドメインがb~であり、ドメインのデータ型がクラスの場合
                output_domain_data = bnode_dict[triple[1]]
                output_domain_datatype = get_class_id_from_url(each_class_name)
            else: #現在選択中のトリプルのドメインがクラスの場合
                output_domain_data = triple[1]
                output_domain_datatype = get_class_id_from_url(each_class_name)
            
            # プロパティ
            prefix_id_prefix_name = get_prefix_id_prefix_name(triple[2])
            property_prefix_id = prefix_id_prefix_name[0]
            property_name = prefix_id_prefix_name[2]

             # レンジ
            if triple[3] in bnode_dict: #現在選択中のトリプルのレンジをkeyとするvalueが登録されていたら
                output_range_data = bnode_dict[triple[3]]
                output_range_datatype = triple[4]
            elif triple[4] == 'uri' or triple[4] == 'literal':
                output_range_data = triple[3]
                output_range_datatype = triple[4]
            else: # #現在選択中のトリプルのレンジのデータ型がクラスだった場合
                output_range_data = triple[3]
                output_range_datatype = get_class_id_from_url(triple[4])
            
            # レンジクラス
            if triple[5] != None:
                output_range_class = get_class_id_from_url(triple[5])
            else:
                output_range_class = ''

            output_triple_list.append([endpoint_info[0], output_domain_data, output_domain_datatype, property_prefix_id, property_name, output_range_data, output_range_datatype, output_range_class, triple[6]])

    # Tripleテーブルにデータをinput
    for output_triple in output_triple_list:
        con=sqlite3.connect('app/models/graduation_research.db')
        cur=con.cursor()
        sql='INSERT OR IGNORE INTO triple (endpoint_id, domain_data, domain_datatype, prefix_id, name, range_data, range_datatype, range_class, probability) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(sql, output_triple)
        con.commit()
        con.close()