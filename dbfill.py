import sqlite3
import json

conn = sqlite3.connect('var/wordle.db')
c = conn.cursor()


f = open('share/valid.json')
data = json.load(f)

for val in data:
    c.execute("INSERT INTO valid (word) VALUES(?)" , (val,)) 
f.close()   


s = open('share/correct.json')
data = json.load(s)

for val in data:
    c.execute("INSERT INTO correct (word) VALUES(?)" , (val,))

s.close()   

conn.commit()