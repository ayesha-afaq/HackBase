from HackathonBackend.app.database import cursor

cursor.execute('SELECT * FROM EVALUATIONS')
print(cursor.fetchall())
