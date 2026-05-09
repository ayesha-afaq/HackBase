import pyodbc
conn_str_ayesha=( "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=DESKTOP-QQUVANE\\SQLEXPRESS;"
    "DATABASE=Hackathon;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;")

conn = pyodbc.connect(conn_str_ayesha)

cursor = conn.cursor()

#testing
cursor.execute("SELECT * FROM Teams")
print("connected to db: ", cursor.fetchall())
# print(pyodbc.drivers())
