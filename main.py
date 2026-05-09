from db import cursor

cursor.execute('SELECT * FROM EVALUATIONS')
print(cursor.fetchall())