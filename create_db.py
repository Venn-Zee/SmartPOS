import pyodbc

# CREATE DATABASE harus dijalankan di luar transaksi (autocommit=True)
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost;'
    'Trusted_Connection=yes;'
    'TrustServerCertificate=yes;'
)
conn.autocommit = True  # WAJIB untuk CREATE DATABASE

cursor = conn.cursor()
cursor.execute(
    "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'smartpos_db') "
    "CREATE DATABASE smartpos_db"
)
print('SUCCESS: Database smartpos_db berhasil dibuat (atau sudah ada)!')
conn.close()
