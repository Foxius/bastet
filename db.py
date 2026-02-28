from database import create_connection, create_tables

conn = create_connection()
create_tables(conn)
conn.close()
