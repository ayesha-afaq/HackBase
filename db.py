import pyodbc
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=DESKTOP-QQUVANE\\SQLEXPRESS;"
    "DATABASE=AYESHA;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM TAB1")
print("connected to db: ", cursor.fetchall())
# print(pyodbc.drivers())
