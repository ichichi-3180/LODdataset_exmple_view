from .models.models import Sparqlendpoint, Prefix, Class, Triple
from flask import Flask,render_template, request
from .models.db import db_session
import re
import random
import urllib.parse
from sqlalchemy import distinct

#Flaskオブジェクトの生成
app = Flask(__name__)

def get_prefix_info_from_prefix_id(prefix_id):
    prefix_info_list =  db_session.query(Prefix).filter_by(id=prefix_id).all()
    if len(prefix_info_list) != 0:
        for prefix_info in prefix_info_list:
            name_space = prefix_info.name_space
            prefix = prefix_info.prefix
    else:
        name_space = prefix_id
        prefix = prefix_id
    return name_space, prefix, 

def get_class_name_from_id(class_id):
    class_info = db_session.query(Class).filter_by(id=class_id).first()
    class_prefix_id = class_info.prefix_id
    name = class_info.name
    prefix_info = get_prefix_info_from_prefix_id(class_prefix_id)
    prefix = prefix_info[1]
    class_name = prefix_info[0] + name
    if re.match('^http(s)?.*', prefix) != None: #取得したprefixが省略版でなかったら
        display_name = prefix + name
    else:
        display_name = prefix + ':' + name
    return display_name, class_name

def get_triple_list_from_db(endpoint_id, domain_data):
    triple_list = []
    triple_list_db = db_session.query(Triple).filter_by(endpoint_id=endpoint_id, domain_data=domain_data).all()
    for triple_db in triple_list_db:
        print(triple_db.id)
        triple_dict = {}
        # ドメイン
        triple_dict["domain"] = {"content":domain_data}

        # プロパティ
        prefix_info = get_prefix_info_from_prefix_id(triple_db.prefix_id)
        if re.match('^http(s)?.*', prefix_info[1]) != None:
            display_property = prefix_info[1] + triple_db.name
        else:
            display_property = prefix_info[1] + ':' + triple_db.name
        proprety_url = prefix_info[0] + triple_db.name
        triple_dict["property"] = {"display_name":display_property, "url":proprety_url}

        # レンジに関してチェック
        range_data = {}
        if len(triple_db.range_class) > 0: # レンジがクラスだったら  クラスかつ空白ノードの場合、クラスを優先
            range_data["content"] = triple_db.range_data
            class_info = get_class_name_from_id(triple_db.range_class)
            range_data["class"] = {"display_name":class_info[0], "url":class_info[1]}
        elif triple_db.range_datatype == 'bnode': # レンジがbnodeだったら
            range_data["content"] = sorted(get_triple_list_from_db(endpoint_id, triple_db.range_data), key=lambda x: x['probability'], reverse=True)
            range_data["class"] = ''
        else: # レンジがuri, literalの場合
            range_data["content"] = triple_db.range_data
            range_data["class"] = ''
        range_data["datatype"] = triple_db.range_datatype
        triple_dict["range"] = range_data
        # if triple_db.range_datatype == 'bnode': # レンジが空白ノードだった場合
        #     range_data["content"] = sorted(get_triple_list_from_db(endpoint_id, triple_db.range_data), key=lambda x: x['probability'], reverse=True)
        #     range_data["datatype"] = triple_db.range_datatype
        # elif triple_db.range_datatype != 'bnode' and triple_db.range_datatype != 'uri' and triple_db.range_datatype != 'literal':
        #     range_data["content"] = triple_db.range_data
        #     class_info = get_class_name_from_id(triple_db.range_datatype)
        #     range_data["datatype"] = {"display_name":class_info[0], "url":class_info[1]}
        # else:
        #     range_data["content"]= triple_db.range_data
        #     range_data["datatype"] = triple_db.range_datatype
        # range_data["class"] = triple_db.range_class
        # triple_dict["range"] = range_data
        triple_dict["probability"] = triple_db.probability

        triple_list.append(triple_dict)
    return triple_list

def get_prefix_dict_from_endopoint_id(endpoint_id):
    prefix_dict = {}
    prefix_info_list = db_session.query(Triple).filter_by(endpoint_id=endpoint_id)
    prefix_id_list = []
    for prefix_info in prefix_info_list:
        if not prefix_info.prefix_id in prefix_id_list:
            prefix_id_list.append(prefix_info.prefix_id)
    
    # print(prefix_id_list)
    for prefix_id in prefix_id_list:
        const = get_prefix_info_from_prefix_id(prefix_id)
        if const[0] != const[1]:
            prefix_dict[const[0]] = const[1]

    return prefix_dict

@app.route("/")
#「/index」へアクセスがあった場合に、「index.html」を返す
@app.route("/index")
def index():
    endpoint_info_list = Sparqlendpoint.query.all()
    return render_template("index.html", endpoint_info_list=endpoint_info_list)

@app.route("/endpoint_info", methods=["post"])
def detail():
    # 現在のendpoint_idを受け取り、endpointテーブルから現在のエンドポイント(データセット)の情報を取得
    endpoint_id = request.form["endpoint_id"]
    endpoint_info = db_session.query(Sparqlendpoint).filter_by(id=endpoint_id).one()

    # 現在選択中のエンドポイントで出現する名前空間→接頭辞のペアを全て取得する
    prefix_info = get_prefix_dict_from_endopoint_id(endpoint_id)
    print(prefix_info)

    # 各クラスを開始ノードとしたトリプルを取得
    class_list_db = db_session.query(Class).filter_by(endpoint_id=endpoint_info.id).all()
    class_triple_list = []
    for class_db in class_list_db:
        # Tripleテーブルから、現在選択中のendpoint_idかつdomain_datatype = class_db.idであるtripleのdomain_data_idを取得
        triple_list_db = db_session.query(Triple).filter_by(endpoint_id=endpoint_id, domain_datatype=class_db.id).all()
        domain_data_list = []
        for triple_db in triple_list_db:
            domain_data_list.append(triple_db.domain_data)
        domain_data_list = list(set(domain_data_list))
        if len(domain_data_list) > 0:
            random_data_element = random.randint(0, len(domain_data_list)-1)
            domain_data = domain_data_list[random_data_element]
            display_triple_list = get_triple_list_from_db(endpoint_id,domain_data)
            # display_triple_list = db_session.query(Triple).filter_by(endpoint_id=endpoint_id, domain_data=domain_data, domain_datatype=class_db.id).all()
        else:
            display_triple_list = []
        # print(domain_data)
        display_triple_list_sorted = sorted(display_triple_list, key=lambda x: x['probability'], reverse=True)
        class_info = get_class_name_from_id(class_db.id)
        class_triple_list.append([class_info[0], class_info[1], display_triple_list_sorted])
    

    return render_template("endpoint_detail.html", endpoint_info=endpoint_info, class_triple_list=class_triple_list, prefix_info=prefix_info)