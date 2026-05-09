print('hi guys')

from db import cursor

cursor.execute("SELECT * FROM TAB1")
print("connected to db:", cursor.fetchall())