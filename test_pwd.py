import pyodbc

passwords = [
    "YourStrong!Passw0rd",
    "YourStr0ngP@ssw0rd",
    "YourSt0ckP@ssw0rd",
    "Pa55w0rd_str0ng",
    "St0ckP@ssw0rd_2026",
    "Docker@SQL2026",
    "SqlServer2026!Pwd",
]

for pwd in passwords:
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=localhost,1433;UID=sa;PWD={pwd}",
            timeout=3
        )
        print(f"SUCCESS with port 1433: {pwd}")
        conn.close()
        break
    except pyodbc.InterfaceError as e:
        if "28000" in str(e):
            continue
        print(f"Other error: {e}")
    except Exception as e:
        print(f"Error: {e}")
