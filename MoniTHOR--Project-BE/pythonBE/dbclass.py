import psycopg2

class PostgresDB:
    def __init__(self, dbname, user, password, host='localhost', port='5432'):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            print("Connection successful")
        except Exception as e:
            print(f"Error connecting to database: {e}")

    def get_data(self, query):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"Error getting data: {e}")
            return None

    def update_data(self, query, data):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, data)
            self.connection.commit()
            cursor.close()
            print("Update successful")
        except Exception as e:
            print(f"Error updating data: {e}")

    def close(self):
        if self.connection:
            self.connection.close()
            print("Connection closed")

# Example usage:
if __name__ == "__main__":
    db = PostgresDB(dbname="your_db", user="your_user", password="your_password")
    db.connect()
    data = db.get_data("SELECT * FROM your_table")
    print(data)
    db.update_data("UPDATE your_table SET column_name = %s WHERE condition_column = %s", ("new_value", "condition_value"))
    db.close()  
