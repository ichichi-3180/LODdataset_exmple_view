from app.models.models import Prefix
from app.models.db import db_session
import json
import sqlite3

prefix_dict = json.load(open('./prefix.json'))

for name_space in prefix_dict.keys():
    con=sqlite3.connect('app/models/graduation_research.db')
    cur=con.cursor()
    sql='INSERT OR IGNORE INTO prefix (name_space, prefix) VALUES (?, ?)'
    data=[name_space, prefix_dict[name_space]]
    cur.execute(sql, data)
    con.commit()
    con.close()