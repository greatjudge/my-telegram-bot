import os
import mysql.connector as connector
from mysql.connector import errorcode
import sys

from abc import ABC, abstractmethod
from place import Place
from functions import *


JSON_DB_PATH = 'database.json'


class AbstractBase(ABC):
    def _toplaces(self, data_list):
        # order must be address, description, latitude, longitude, photopath
        return tuple(map(Place, data_list))

    @abstractmethod
    def list(self, user_id, count):
        pass

    @abstractmethod
    def add(self, user_id, place):
        pass

    @abstractmethod
    def reset(self, user_id):
        pass


# Connect to MariaDB Platform
class MysqlBase(AbstractBase):
    TABLES = {'user': 'CREATE TABLE user(id INT NOT NULL PRIMARY KEY)',
              'place': """CREATE TABLE place(
                  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                  address VARCHAR(200) NOT NULL,
                  description TEXT,
                  latitude Decimal(8, 6) UNSIGNED,
                  longitude Decimal(9, 6) UNSIGNED,
                  photopath VARCHAR(200),
                  user_id INT NOT NULL,
                  date_cr DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE)"""}

    def __init__(self):
        pass

    def connect(self):
        try:
            connection = connector.connect(
                user=os.environ.get('NEW_DB_USER'),
                password=os.environ.get('NEW_DB_PASSWORD'),
                host=os.environ.get('NEW_DB_HOST'),
                port=int(os.environ.get('NEW_DB_PORT')),
                database=os.environ.get('NEW_DB_NAME'),
            )
        except connector.Error as e:
            print(f"Error connecting to Mysql Platform: {e}")
            sys.exit(1)
        else: return connection

    def create_tables(self):
        connection = self.connect()
        cursor = connection.cursor()
        for table_name in self.TABLES:
            table_description = self.TABLES[table_name]
            try:
                print("Creating table {}: ".format(table_name), end='')
                cursor.execute(table_description)
            except connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("already exists.")
                else:
                    print(err.msg)
            else:
                print("OK")
        cursor.close()
        connection.close()

    def list(self, user_id, count=5):
        connection = self.connect()
        cursor = connection.cursor()
        data_list = list()
        if count == -1:
            # FIX automatic fields
            query = """SELECT address, description, latitude, longitude, photopath
                        FROM place WHERE(user_id = %s) ORDER BY date_cr"""
            cursor.execute(query, (user_id, ))
        else:
            query = """SELECT address, description, latitude, longitude, photopath
                        FROM place WHERE(user_id = %s) ORDER BY date_cr DESC LIMIT %s"""
            cursor.execute(query, (user_id, count))
        for row in cursor:
            data_list.append(dict(zip(Place.fields, row)))
        cursor.close()
        connection.close()
        return self._toplaces(data_list)

    def add_user(self, cursor, connection, user_id):
        cursor.execute('SELECT 1 FROM user WHERE (id = %s)', (user_id, ))
        data = cursor.fetchall()
        if not data:
            cursor.execute('INSERT INTO user VALUES(%s)', (user_id, ))
            connection.commit()

    def add(self, user_id, place):
        # FIX... user data must be a function argument
        data = place.data
        data['user_id'] = user_id
        q = ['%s'] * len(data.values())
        query = f'INSERT INTO place ({", ".join([str(v) for v in data.keys()])}) VALUES ({",".join(q)})'
        try:
            connection = self.connect()
            cursor = connection.cursor()
            self.add_user(cursor, connection, user_id)
            cursor.execute(query, tuple(data.values()))
            connection.commit()
            connection.close()
        except connector.Error as e:
            if place.photopath: delete_photo(place.photopath)
            print(f'Error add: {e}')
            print(query)
            sys.exit(1)

    def reset(self, user_id):
        query = 'DELETE FROM user WHERE(id = %s)'
        try:
            connection = self.connect()
            cursor = connection.cursor()
            cursor.execute(query, (int(user_id), ))
            connection.commit()
            connection.close()
            delete_photos(user_id)
        except connector.Error as e:
            print(f'Error delete: {e}')
