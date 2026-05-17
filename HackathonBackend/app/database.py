import pyodbc


# conn_str_ayesha=( "DRIVER={ODBC Driver 18 for SQL Server};"
#     "SERVER=DESKTOP-QQUVANE\\SQLEXPRESS;"
#     "DATABASE=Hackathon;"
#     "Trusted_Connection=yes;"
#     "TrustServerCertificate=yes;")

#     conn_str_ayesha=( "DRIVER={ODBC Driver 18 for SQL Server};"
#     "SERVER=MAHAMMASROOR29\SQLEXPRESS;"
#     "DATABASE=Hackathon;"
#     "Trusted_Connection=yes;"
#     "TrustServerCertificate=yes;")

# def get_connection():

#     conn = pyodbc.connect(conn_str_ayesha)
#     return conn


print (pyodbc.drivers())

