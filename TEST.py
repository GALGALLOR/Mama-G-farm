import MySQLdb

# Establish connections to local and online databases
local_conn = MySQLdb.connect(host='localhost', user='', passwd='', db='MAMA_G')
online_conn = MySQLdb.connect(host='mamaG.mysql.pythonanywhere-services.com', user='mamaG', passwd='GALGALLO10_', db='mamaG$default')

# Retrieve table names from the local database
cursor = local_conn.cursor()
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()
print(tables)
# Iterate over table names
for table in tables:
    table_name = table[0]
    
    # Create table in the online database
    cursor.execute(f"CREATE TABLE {table_name} (id INT AUTO_INCREMENT PRIMARY KEY)")
    online_conn.commit()
    
    # Retrieve field names from the local database for the current table
    cursor.execute(f"DESCRIBE {table_name}")
    fields = cursor.fetchall()
    print(fields)
    # Iterate over field names
    for field in fields:
        field_name = field[0]
        
        # Create field in the online database
        ###cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {field_name} VARCHAR(255)")
        ###online_conn.commit()

# Close connections
cursor.close()
local_conn.close()
online_conn.close()
