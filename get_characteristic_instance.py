from SPARQLWrapper import SPARQLWrapper
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

# endpoint = 'http://localhost:3030/NDL'
# endpoint = 'http://localhost:3030/onsen' # inbound->Personクラス instance->HotSpringクラス
# endpoint = 'http://localhost:3030/botanical' # inbound->Placeクラス instance->Plantクラス
# endpoint = 'http://localhost:3030/vtuber' # inbound->Personクラス instance->VideoObjectクラス
# endpoint = 'http://localhost:3030/omiyage'
# endpoint = 'http://localhost:3030/textbook'
# endpoint = 'http://localhost:3030/isil'
# endpoint = 'http://localhost:3030/vlueprint'
# endpoint = 'http://localhost:3030/media-arts-db'
# endpoint = 'https://sparql.metadata.moe/madb/query'
endpoint = 'https://sparql.city.kyoto.lg.jp/sparql/'
# endpoint = 'https://lib-lod.tsunagun.org/sparql/isil-lod-jp/query'
# endpoint = 'http://data.yafjp.org/sparql'
# endpoint = 'https://lod.dataeye.jp/sparql'
# endpoint = 'http://localhost:3030/LOV'
# endpoint = 'http://mdlab.slis.tsukuba.ac.jp/lodc2018/drama/query'

sparql = SPARQLWrapper(endpoint=endpoint, returnFormat='json')

directory = urllib.parse.urlparse(endpoint).netloc + urllib.parse.urlparse(endpoint).path 
directory = directory.replace("/", "_")
output_path =  directory +'/' 
if not os.path.exists(output_path):
    os.makedirs(output_path)

def get_class_list():
    class_list = []
    query = """                                                                                                                                                                      
        select distinct ?class where{
            ?s a ?class .
        } 
    """
    sparql.setQuery(query)
    results = sparql.query().convert()
    
    for result in results["results"]["bindings"]:
        class_list.append(result["class"]["value"])
    return class_list

def get_n_count(path):
    query = """
        select (count(?n) AS ?num) where{{
            {path}
        }}
    """
    query = query.format(path=path)
    sparql.setQuery(query)
    results = sparql.query().convert()
    return results["results"]["bindings"][0]["num"]["value"]

def get_distinct_n_count(path):
    query = """
        select (count(distinct ?n) AS ?num) where{{
            {path}
        }}
    """
    query = query.format(path=path)
    sparql.setQuery(query)
    results = sparql.query().convert()
    return results["results"]["bindings"][0]["num"]["value"]

def get_distinct_n_class_count(range_class,path):
    query = """
        select (count(distinct ?n) AS ?num) where{{
            {path}
            ?n a <{range_class}>.
        }}
    """
    query = query.format(path=path, range_class=range_class)
    sparql.setQuery(query)
    results = sparql.query().convert()
    return results["results"]["bindings"][0]["num"]["value"]

def get_n_class(path):
    query = """
        select distinct ?class where{{
            {path}
            ?n a ?class .
        }}
    """
    query = query.format(path=path)
    sparql.setQuery(query)
    results = sparql.query().convert()
    if len(results["results"]["bindings"]) == 1:
        return results["results"]["bindings"][0]["class"]["value"]
    elif len(results["results"]["bindings"]) == 0:
        return "no_class"
    else:
        # print(results["results"]["bindings"])
        return "many_class"

def get_n_class_list(path):
    query = """
        select distinct ?class where{{
            {path}
            ?n a ?class .
        }}
    """
    query = query.format(path=path)
    sparql.setQuery(query)
    results = sparql.query().convert()
    class_list = []
    for result in results["results"]["bindings"]:
        class_list.append(result["class"]["value"])
    return class_list

def get_n_datatype(path):
    query = """
        select distinct ?n where{{
            {path}
        }}
    """
    query = query.format(path=path)
    sparql.setQuery(query)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
        return result["n"]["type"]

# for文内で重複をrange_pathの更新を行う関数
def input_range_path(range_path, p):
    range_path = range_path.format(p=p)
    return range_path

def get_n_range_count(now_choice_node_path, next_property):
    query = """
        select ?n (count(distinct ?n1) AS ?count) where{{
            {path}
            ?n <{next_property}> ?n1 .
        }}GROUP BY ?n
    """
    query = query.format(path = now_choice_node_path, next_property=next_property)
    sparql.setQuery(query)
    results = sparql.query().convert()
    range_num_count = []
    for result in results["results"]["bindings"]:
        # c = get_n_count(now_choice_node_path)
        # print(c)
        range_num_count.append(result["count"]["value"])
    
    return collections.Counter(range_num_count)

def get_n_range_class_count(now_choice_node_path, next_property, range_class):
    query = """
        select ?n (count(distinct ?n1) AS ?count) where{{
            {path}
            ?n <{next_property}> ?n1 .
            ?n1 a <{range_class}>.
        }}GROUP BY ?n
    """
    query = query.format(path = now_choice_node_path, next_property=next_property, range_class=range_class)
    sparql.setQuery(query)
    # print(query)
    results = sparql.query().convert()
    range_num_count = []
    for result in results["results"]["bindings"]:
        # c = get_n_count(now_choice_node_path)
        # print(c)
        range_num_count.append(result["count"]["value"])
    
    return collections.Counter(range_num_count)

def get_n_not_exists_range_count(now_choice_node_path, next_property):
    query = """
        select ?n where{{
            {path}
            filter not exists{{?n <{next_property}> ?n1 }}
        }}GROUP BY ?n
    """
    query = query.format(path = now_choice_node_path, next_property=next_property)
    sparql.setQuery(query)
    results = sparql.query().convert()
    count = 0
    for result in results["results"]["bindings"]:
        count += 1
    return count

def get_n_not_exists_range_class_count(now_choice_node_path, next_property, range_class):
    query = """
        select ?n where{{
            {path}
            filter not exists{{?n <{next_property}> [a <{range_class}>] }}
        }}GROUP BY ?n
    """
    query = query.format(path = now_choice_node_path, next_property=next_property,range_class=range_class)
    sparql.setQuery(query)
    results = sparql.query().convert()
    count = 0
    for result in results["results"]["bindings"]:
        count += 1
    return count

def get_n_class_count(range_class, path):
    query = """
        select (count(?n) AS ?num) where{{
            {path}
            ?n a <{range_class}> .
        }}
    """
    query = query.format(path=path, range_class=range_class)
    sparql.setQuery(query)
    results = sparql.query().convert()
    return results["results"]["bindings"][0]["num"]["value"]

def get_outbound_property(begin_node_class, path):
    # print(check_class_list)
    begin_node_path = 'a <' + begin_node_class + '>'
    if len(path) == 0: # 1周目
        # print(begin_node_path)
        comma_or_semicolon = '.'
        filter = "filter(?s = ?n)"
        in_path = path
        now_choice_node_path = '?n '+begin_node_path + '.'
        # now_choice_node_path = '?n a <' + begin_node_class + '>.' 
        next_in_path = '<{p}> ?n .'
        # range_path = """
        #     ?s {begin_node_path} ;
        #     {path}"""
        range_path = """
            ?s {begin_node_path} ;
            {path}"""
        range_path=range_path.format(begin_node_path=begin_node_path, path=next_in_path)
    else: # 2周目以降
        comma_or_semicolon = ';'
        filter = ''
        left_count = path.count('[')
        in_path = path + '?n' + left_count*']' + '.' 

        # 現在選択中のノードに対するパス    
        now_choice_node_path = """
            ?s {begin_node_path} ;
            {path}"""
        now_choice_node_path = now_choice_node_path.format(begin_node_path=begin_node_path, path=in_path)

        # 現在選択中のノードを主語とした時の目的語ノードに対するパス
        next_in_path = path + '[' + '<{p}>' + '?n' + (left_count+1)*']' + '.' 
        range_path = """
            ?s {begin_node_path} ;
            {path}"""
        range_path = range_path.format(begin_node_path=begin_node_path, path=next_in_path)

        path += '['

    property_list = []
    query = """
        select distinct ?p where{{
            ?s {begin_node_path} {comma_or_semicolon}
            {path}
            ?n ?p ?o .
            {filter}
        }}
    """
    query = query.format(begin_node_path=begin_node_path, comma_or_semicolon=comma_or_semicolon, path=in_path, filter=filter)
    # print(query)
    sparql.setQuery(query)
    results = sparql.query().convert()
    domain_num = get_n_count(now_choice_node_path)
    domain_kind_num = get_distinct_n_count(now_choice_node_path)
    domain_datatype = get_n_datatype(now_choice_node_path)
    # print(now_choice_node_path)
    for result in results["results"]["bindings"]:
        range = input_range_path(range_path, result["p"]["value"])
        # print(range)
        range_class_list = get_n_class_list(range)
        if len(range_class_list) > 0: # レンジがクラスの場合　レンジが複数クラスの場合もあるため、range_numも変わってくる
            # [ドメイン(クラス名orbnode名), ]
            for range_class in range_class_list:
                dic = {}
                dic["name"] = result["p"]["value"]
                dic["domain_num"] = int(domain_num)
                range_num = get_n_class_count(range_class, range)
                dic["range_num"] = int(range_num)
                # dic["domain_kind_num"] = int(domain_kind_num)
                range_kind_num = get_distinct_n_class_count(range_class, range)
                # dic["range_kind_num"] = int(range_kind_num)
                # dic["domain_datatype"] = domain_datatype
                dic["range_class"] = range_class
                dic["range_datatype"] = get_n_datatype(range)
                range_num_count = get_n_range_class_count(now_choice_node_path, result["p"]["value"],range_class)
                sum = 0
                for k in range_num_count.keys():
                    sum += int(range_num_count[k])
                range_num_count['0'] = get_n_not_exists_range_class_count(now_choice_node_path, result["p"]["value"], range_class)
                dic["range_num_count"] = range_num_count
                # next_path = path + ' <'+result["p"]["value"]+'> ' 
                # dic["next_p"] = get_outbound_property(begin_node_class, next_path)
                dic["next_p"] = []
                property_list.append(dic)

        else: # レンジがクラスでない場合
            range_num = get_n_count(range)
            range_kind_num = get_distinct_n_count(range)
            dic = {}
            dic["name"] = result["p"]["value"]
            dic["domain_num"] = int(domain_num)
            dic["range_num"] = int(range_num)
            # dic["domain_kind_num"] = int(domain_kind_num)
            # dic["range_kind_num"] = int(range_kind_num)
            # dic["domain_datatype"] = domain_datatype
            dic["range_class"] = ''
            dic["range_datatype"] = get_n_datatype(range)
            range_num_count = get_n_range_count(now_choice_node_path, result["p"]["value"])
            sum = 0
            for k in range_num_count.keys():
                sum += int(range_num_count[k])
            range_num_count['0'] = get_n_not_exists_range_count(now_choice_node_path, result["p"]["value"])
            dic["range_num_count"] = range_num_count
            if get_n_datatype(range) == 'bnode':
                next_path = path + ' <'+result["p"]["value"]+'> ' 
                dic["next_p"] = get_outbound_property(begin_node_class, next_path)
            else:
                dic["next_p"] = []
            property_list.append(dic)


    return property_list

def dict_to_characteristic_dot(domain,structure_dict):
    global uri_num, literal_num, bnode_num, node_list
    dot_list = []
    for structure in structure_dict:
        # print(structure)
        range_count = structure["range_num_count"].most_common()
        # range_num_countの中で最も頻度が高い目的語の数をリストで取得(複数ある場合も考慮したいため)
        most_common_range_num_count_list = [k for k, v in structure["range_num_count"].items() if v == range_count[0][1]]
        most_common_range_num_count_list = list(map(int, most_common_range_num_count_list))  # 文字列であったrange_num_countをint型に変換
        most_common_object_num = min(most_common_range_num_count_list) # 複数あった場合に最も数が小さい場合を採用(探索結果を取得しやすくするため)
        # print(structure["name"] + ':' + str(most_common_range_num_count_list))
        # most_common_object_num = int(range_count[0][0])
        # print(most_common_object_num)
        for i in range(int(most_common_object_num)):

            # レンジの確認
            if len(structure["range_class"]) > 0 : #レンジがクラスだったら
                range_node = '\"' + structure["range_class"] + '\"'
            else: #レンジがクラスでないばあお
                if structure["range_datatype"] == 'literal':
                    literal_num += 1
                    range_node = 'LITERAL' + str(literal_num)
                    node_list.append(range_node + '[shape=\"box\"]')
                elif structure["range_datatype"] == 'uri':
                    uri_num += 1
                    range_node = 'URI' + str(uri_num)
                    node_list.append(range_node + '[shape=\"ellipse\"]')
                elif structure["range_datatype"] == 'bnode':
                    bnode_num += 1
                    range_node = 'BNODE' + str(bnode_num)
                    node_list.append(range_node + '[shape=\"doublecircle\"]' )
                    if len(structure["next_p"]) > 0:
                        for dot in dict_to_characteristic_dot(range_node, structure["next_p"]):
                            dot_list.append(dot)
                else:
                    print(structure)
            # exist_probab = float(structure["range_num_count"][str(most_common_object_num)]) / float(structure["domain_num"])
            exist_probab =(float(structure["domain_num"]) -  float(structure["range_num_count"][str(0)])) / float(structure["domain_num"])
            dot_list.append('\"' + domain + '\"->' + range_node + '[label=\"' + structure["name"] + '\nexistprobab:' + str(exist_probab) +  '\"]')

    return dot_list

def dict_to_characteristic_structure_list(domain, structure_dict):
    global bnode_num
    structure_list = []
    for structure in structure_dict:
        most_common_range_num = max(structure["range_num_count"], key=structure["range_num_count"].get)
        if int(most_common_range_num) == 0: # 最も出現頻度の高い構造が目的語が0個の場合
            if structure["range_datatype"] == 'bnode': # レンジがbnodeの場合
                bnode_num += 1
                range_node = 'b' + str(bnode_num)
                if len(structure["range_class"]) > 0: # レンジがクラスの場合
                    range_class = structure["range_class"]
                else: # レンジがクラスでない場合
                    range_class = None
                if len(structure["next_p"]) > 0:
                    for list in dict_to_characteristic_structure_list(range_node, structure["next_p"]):
                        structure_list.append(list)
            else: # レンジがbnodeでない場合(literal or uri)
                range_node = structure["range_datatype"]
                if len(structure["range_class"]) > 0: # レンジがクラスの場合
                    range_class = structure["range_class"]
                else: # レンジがクラスでない場合
                    range_class = None
            # listの形式→[ドメインクラス/bnode番号, プロパティ名, レンジデータタイプ(uri/literal/b\d+), レンジクラス(クラス名前/None), 出現確率]
            structure_list.append([domain, structure["name"], range_node, range_class, 0])

        else: # 最も出現頻度の高い構造が目的語が1つ以上の場合
            for i in range(int(most_common_range_num)):
                if structure["range_datatype"] == 'bnode': # レンジがbnodeの場合
                    bnode_num += 1
                    range_node = 'b' + str(bnode_num)
                    if len(structure["range_class"]) > 0: # レンジがクラスの場合
                        range_class = structure["range_class"]
                    else: # レンジがクラスでない場合
                        range_class = None
                    if len(structure["next_p"]) > 0:
                        for list in dict_to_characteristic_structure_list(range_node, structure["next_p"]):
                            structure_list.append(list)
                else: # レンジがbnodeでない場合(literal or uri)
                    range_node = structure["range_datatype"]
                    if len(structure["range_class"]) > 0: # レンジがクラスの場合
                        range_class = structure["range_class"]
                    else: # レンジがクラスでない場合
                        range_class = None
                
                # プロパティの出現確率(最も出現頻度が高い目的語の数とは別)を「最も出現頻度が高い目的語の数をレンジとして持つドメインの数」/「ドメインの数」として求める
                # exist_probab = float(structure["range_num_count"][str(most_common_range_num)]) / float(structure["domain_num"])
                exist_probab =(float(structure["domain_num"]) -  float(structure["range_num_count"][str(0)])) / float(structure["domain_num"])
                # if exist_probab > 0.99:
                
                
                # listの形式→[ドメインクラス/bnode番号, プロパティ名, レンジクラス/データタイプ(URI/リテラル), 出現確率]
                structure_list.append([domain, structure["name"], range_node, range_class, exist_probab])
    
    return structure_list

def dict_to_query_path(domain, structure_dict):
    global num
    if re.match('^\?o\d*', domain) != None: #domainがクラスでない場合(空白ノードの場合)
        domain_node = domain
        begin_node_query = ''
        query_domain = domain
    else: #domainがクラス名の場合
        domain_node = '?n'
        begin_node_query = '?n a <' + domain + '>.'
        query_domain = domain_node
    # print(structure_dict)
    triple_list = [] # 形式→[ドメインノード,プロパティ, レンジノード, レンジの個数]
    subquery_list = []
    while len(structure_dict) != 0:
        num += 1
        x = structure_dict.pop(0)
        # print(x)
        range_count = x["range_num_count"].most_common()
        # range_num_countの中で最も頻度が高い目的語の数をリストで取得(複数ある場合も考慮したいため)
        most_common_range_num_count_list = [k for k, v in x["range_num_count"].items() if v == range_count[0][1]]
        most_common_range_num_count_list = list(map(int, most_common_range_num_count_list))  # 文字列であったrange_num_countをint型に変換
        most_common_range_num = min(most_common_range_num_count_list) # 複数あった場合に最も数が小さい場合を採用(探索結果を取得しやすくするため)
        if int(most_common_range_num) > 0:
            # exist_probab = float(x["range_num_count"][str(most_common_range_num)]) / float(x["domain_num"])
            triple_list.append([domain_node, x["name"], '?o'+str(num), most_common_range_num])
            if len(x["next_p"]) > 0 and x["range_datatype"] == 'bnode': #レンジがbnodeかつ次のプロパティが存在する場合
                subquery_list.append(dict_to_query_path('?o'+str(num),x["next_p"]))


    # print(list)
    mainquery = ''
    firstLoop = True
    conditions = ''
    for p in triple_list:
        mainquery += p[0] + ' <' + p[1] + '> ' + p[2] + '.\n'
        if firstLoop:
            conditions += '(count(distinct '+p[2]+')='+str(p[3])+')'
            firstLoop = False
        else:
            conditions += ' && (count(distinct '+p[2]+')='+str(p[3])+')'

    query = """
        select distinct {query_domain} where{{
            {begin_node_query}
            {mainquery}
            {subquery}
        }}GROUP BY {query_domain}
        HAVING (
            {conditions}
        )
    """
    subquery=''
    for sq in subquery_list:
        subquery += '{' + sq + '}\n'
    query = query.format(query_domain=query_domain, begin_node_query=begin_node_query, mainquery=mainquery, subquery=subquery, conditions=conditions)
    # print(query)
    begin_node_query = ''
    return query

def get_query_info(node, structure_list):
    global node_num ,objects, path_list
    while len(structure_list) != 0:
        node_num += 1
        x = structure_list.pop(0)
        range_count = x["range_num_count"].most_common()
        # range_num_countの中で最も頻度が高い目的語の数をリストで取得(複数ある場合も考慮したいため)
        most_common_range_num_count_list = [k for k, v in x["range_num_count"].items() if v == range_count[0][1]]
        most_common_range_num_count_list = list(map(int, most_common_range_num_count_list))  # 文字列であったrange_num_countをint型に変換
        most_common_range_num = min(most_common_range_num_count_list) # 複数あった場合に最も数が小さい場合を採用(探索結果を取得しやすくするため)
        # most_common_range_num = max(x["range_num_count"], key=x["range_num_count"].get)
        # if int(most_common_range_num) != 0:
            # main_query += (node + ' <' + x['name'] + '> ?o' + str(node_num) + '.\n')
        object = 'o'+str(node_num)
        objects += ' ?' + object

        # レンジのデータタイプ設定
        if len(x["range_class"]) > 0: # レンジがクラスの場合
            range_class = x["range_class"]
        else: # レンジがクラス以外(URI, リテラル, 空白ノード)
            range_class = None
        
        range_datatype = x["range_datatype"]
        

        # exist_probab = float(x["range_num_count"][str(most_common_range_num)]) / float(x["domain_num"])
        exist_probab =(float(x["domain_num"]) -  float(x["range_num_count"][str(0)])) / float(x["domain_num"])
        if int(most_common_range_num) != 0:
            path_list.append([node, x["name"], object, range_datatype, range_class, exist_probab, most_common_range_num])
        else:
            path_list.append([node, x["name"], object, range_datatype, range_class, 0, most_common_range_num])
        if len(x["next_p"]) > 0:
            get_query_info('o'+str(node_num), x["next_p"])
    return 0

def get_characteristic_instance(begin_class, instance_node):
    # print(instance_node)
    # path_listはデータをsparqlで取得するための情報を入れている
    # path_listの形式[domain_node, property, range_node,range_datatype, range_class, 出現頻度, 目的語の数]
    global path_list
    main_query = ''
    for path in path_list:
        if int(path[6]) != 0:
            # print(path)
            main_query += '?' + path[0] + ' <' + path[1] + '> ?' + path[2] + '.\n'
        # print(path)
    query = """
        select distinct {objects} where{{
            {main_query}
            filter (?n = <{instance_node}>)
        }}
    """
    query = query.format(objects=objects, main_query=main_query, instance_node=instance_node)
    print(query)
    sparql.setQuery(query)
    results = sparql.query().convert()
    # print(query)
    instance_list = [] #[主語, 述語, 目的語, データ型(uri, literal, bnode),クラス(クラス名/None), 存在確率]
    # print(results)
    if results["results"]["bindings"]: # 作成したクエリの結果としてデータが取得できたら
        # print('a')
        for result in results["results"]["bindings"]:
            for path in path_list:
                if path[0] == 'n': # ドメインがクラスの時
                    domain_node = instance_node
                    domain_datatype = begin_class
                else:
                    domain_node = result[path[0]]["value"]
                    domain_datatype = 'bnode'
                # print(result)
                # print(path)
                if path[2] in result:
                    if not [domain_datatype, domain_node, path[1], result[path[2]]["value"],  path[3], path[4], path[5]] in instance_list:
                        instance_list.append([domain_datatype, domain_node, path[1], result[path[2]]["value"],  path[3], path[4], path[5]])
                else:
                    if not [domain_datatype, domain_node, path[1], '',  path[3], path[4], path[5]] in instance_list:
                        instance_list.append([domain_datatype, domain_node, path[1], '',  path[3], path[4],path[5]])
    else: # 作成したクエリの結果として、データが取得できなかったら
        # print("a")
        for path in path_list:
            if path == 'n':
                domain_node = instance_node
                domain_datatype = begin_class
            else:
                domain_node = path[0]
                domain_datatype = 'bnode'
            if not [domain_datatype, domain_datatype, path[1], path[2], path[3], path[4], path[5]]:
                instance_list.append([domain_datatype, domain_datatype, path[1], path[2], path[3], path[4], path[5]])
        # print(instance_list)
    #     print("a")
    return instance_list, query

def get_data_get_query(instance_get_query):
    global path_list
    main_query = ''
    for path in path_list:
        if int(path[6]) != 0:
            main_query += '?' + path[0] + ' <' + path[1] + '> ?' + path[2] + '.\n'
    data_get_query = """
        select distinct ?n {objects} where{{
            {main_query}
            {{
                {instance_get_query}
            }}
        }}
    """ 
    data_get_query = data_get_query.format(objects=objects, main_query=main_query,instance_get_query=instance_get_query)
    return data_get_query

def check_bnode_class(class_name):
    query = """
        select distinct ?n where{{
            ?n a <{class_name}>.
        }}
    """
    query = query.format(class_name=class_name)
    sparql.setQuery(query)
    results = sparql.query().convert()
    if results["results"]["bindings"][0]["n"]["type"] == 'bnode': # 引数として渡したクラスが空白ノードならば
        return True
    else: # 引数として渡したクラスが空白ノードでないならば
        return False

# データセット内のクラス名を取得
class_name_list = get_class_list()
# print(class_name_list[0])

# データセット内のクラスそれぞれにおいて、近傍の構造(プロパティ、目的語(空白ノードがある場合はその先も探索))を取得
class_structure = {}
for class_name in class_name_list:
    begin_node_path = 'a <' + class_name + '>'
    print(class_name)
    structure_info = get_outbound_property(class_name, '')
    class_structure[class_name] = structure_info

with open(output_path + 'class_structure.json', 'w') as f:
    print(json.dumps(class_structure, ensure_ascii=False), file=f)

# データセット内のクラスそれぞれにおいて、近傍の構造を可視化
for each_class_name in class_structure.keys():
    # print(each_class_name)
    output_class_directory = urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).netloc + urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).path
    if urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).fragment:
        output_class_directory += '#' + urllib.parse.urlparse(urllib.parse.unquote(each_class_name)).fragment
    output_class_directory = output_class_directory.replace("/", "_")

    # クラスごとに作成したdict形式の構造をdot形式に直して可視化する
    uri_num = 0
    literal_num = 0
    bnode_num = 0
    class_num = 0
    node_list = []
    chracteristic_structure_dot_list = dict_to_characteristic_dot(each_class_name, class_structure[each_class_name])
    
    characteristic_structure_dot_file = """digraph{
        graph [rankdir = LR];
    """
    for chracteristic_structure_dot in chracteristic_structure_dot_list:
        characteristic_structure_dot_file += chracteristic_structure_dot + '\n'
    for node in node_list:
        characteristic_structure_dot_file += node + '\n'
    characteristic_structure_dot_file += '}'
    s = Source(characteristic_structure_dot_file)
    s.render(output_path + output_class_directory + '/characteristic_structure', format='png')

    # 特徴的なリスト形式の構造(トリプル単位[ドメインクラス/bnode番号, プロパティ名, レンジデータタイプ(uri/literal/bnode), レンジクラス(クラス名前/None), 出現確率])を取得
    bnode_num = 0 #空白ノードをカウントするグローバル変数
    characteristic_structure_list = dict_to_characteristic_structure_list(each_class_name, class_structure[each_class_name])
    if not os.path.exists(output_path + output_class_directory + '/'):
        os.makedirs(output_path + output_class_directory + '/')
    with open(output_path + output_class_directory + '/characteristic_structure.csv', 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(characteristic_structure_list)
    
    # グローバル変数を宣言し、検索に必要な情報を取得(path_list)
    node_num = 0
    objects = ''
    path_list = []
    get_query_info('n', copy.deepcopy(class_structure[each_class_name]))
    # print(path_list)
    with open(output_path + output_class_directory + '/path_list.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(path_list)
    
    # 各クラスごとに特徴的な構造を満たす開始ノードを取得
    num = 0
    query_path = []
    instance_get_query = dict_to_query_path(each_class_name, copy.deepcopy(class_structure[each_class_name]))
    with open(output_path + output_class_directory + '/get_begin_node_list_query.rq', 'w') as f:
        print(instance_get_query, file=f)
    
    # 現在選択中のクラスのデータタイプが空白ノードであるかをチェック
    if check_bnode_class(each_class_name): # 空白ノードであった場合
        data_get_query = get_data_get_query(instance_get_query)
        with open(output_path + output_class_directory + '/data_get_query.rq', 'w') as f:
            print(data_get_query, file=f)
        sparql.setQuery(data_get_query)
        results = sparql.query().convert()
        instance_list = [] #[主語, 述語, 目的語, データ型, 存在確率]
        if results["results"]["bindings"]: #クエリの結果が存在したら
            for result in results["results"]["bindings"]:
                for path in path_list:
                    if path[0] == 'n': # ドメインがクラスの時
                        domain_datatype = each_class_name
                    else:
                        domain_datatype = 'bnode'
                    
                    if path[2] in result:
                        if not [domain_datatype, result[path[0]]["value"], path[1], result[path[2]]["value"],  path[3], path[4], path[5]] in instance_list:
                            instance_list.append([domain_datatype, result[path[0]]["value"], path[1], result[path[2]]["value"],  path[3], path[4], path[5]])
                    else:
                        if not [domain_datatype, path[0], path[1], '',  path[3], path[4], path[5]] in instance_list:
                            instance_list.append([domain_datatype, result[path[0]]["value"], path[1], '',  path[3], path[4], path[5]])
        else: 
            for path in path_list:
                if path[0] == 'n':
                    domain_datatype = each_class_name
                else:
                    domain_datatype = 'bnode'
                if not [domain_datatype, path[0], path[1], path[2], path[3], path[4], path[5]]:
                    instance_list.append([domain_datatype, path[0], path[1], path[2], path[3], path[4], path[5]])
        if not os.path.exists(output_path + output_class_directory + '/instance_list/instance/'):
            os.makedirs(output_path + output_class_directory + '/instance_list/instance/')
        with open(output_path + output_class_directory + '/instance_list/instance/instance_list.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(instance_list)

    else: # 空白ノードでない場合
        sparql.setQuery(instance_get_query)
        results = sparql.query().convert()
        begin_node_list = []
        for i in range(len(results["results"]["bindings"])):
            # print(urllib.parse.unquote(results["results"]["bindings"][i]["n"]["value"]))
            begin_node_list.append(results["results"]["bindings"][i]["n"]["value"])
        with open(output_path + output_class_directory + '/begin_node_list.json', 'w') as f:
            print(json.dumps(begin_node_list, ensure_ascii=False), file=f)


        # 開始ノードリストから特徴的な用例[ドメインデータタイプ, ドメインデータ, プロパティ, レンジデータ, レンジデータタイプ, プロパティ出現確率]
        for begin_node in begin_node_list:
            const = get_characteristic_instance(each_class_name, begin_node)
            characteristic_structure_instance = const[0]
            get_query = const[1]
            directory = urllib.parse.urlparse(urllib.parse.unquote(begin_node)).netloc + urllib.parse.urlparse(urllib.parse.unquote(begin_node)).path 
            directory = directory.replace("/", "_")
            if not os.path.exists(output_path + output_class_directory + '/instance_list/' + directory + '/'):
                os.makedirs(output_path + output_class_directory + '/instance_list/' + directory + '/')
            with open(output_path + output_class_directory + '/instance_list/' + directory + '/' + 'instance_list.csv', 'w') as f:
                writer = csv.writer(f)
                writer.writerows(characteristic_structure_instance)
            with open(output_path + output_class_directory + '/instance_list/' + directory + '/' + 'get_query.rq', 'w') as f:
                print(get_query, file=f)
    