import os
import mysql
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
    def __init__(self):
        pass

    def connect(self):
        try:
            self.connection = mariadb.connect(
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD'),
                host=os.environ.get('DB_HOST'),
                port=int(os.environ.get('DB_PORT')),
                database=os.environ.get('DB_NAME'),
            )
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
        else: return self.connection.cursor()

    def create_tables(self):
        # FIX....
        query_user = 'CREATE TABLE user(id INT NOT NULL PRIMARY KEY)'
        query_place = """CREATE TABLE place(
                            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                            address VARCHAR(200) NOT NULL,
                            description TEXT,
                            latitude Decimal(8, 6) UNSIGNED,
                            longitude Decimal(9, 6) UNSIGNED,
                            photopath VARCHAR(200),
                            user_id INT NOT NULL,
                            date_cr DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE)"""
        try:
            cursor = self.connect()
            cursor.execute(query_user)
            cursor.execute(query_place)
            cursor.connection.commit()
        except  mariadb.Error as e:
            print(f'Error creating tables: {e}')
        finally:
            cursor.connection.close()

    def list(self, user_id, count=5):
        data_list = list()
        if count == -1:
            # FIX automatic fields
            query = """SELECT address, description, latitude, longitude, photopath
                        FROM place WHERE(user_id = ?) ORDER BY date_cr"""
            cursor = self.connect()
            cursor.execute(query, (user_id, ))
        else:
            query = """SELECT address, description, latitude, longitude, photopath
                        FROM place WHERE(user_id = ?) ORDER BY date_cr DESC LIMIT ?"""
            cursor = self.connect()
            cursor.execute(query, (user_id, count))
        for row in cursor:
            data_list.append(dict(zip(Place.fields, row)))
        cursor.connection.close()
        return self._toplaces(data_list)

    def add_user(self, cursor, user_id):
        cursor.execute('SELECT 1 FROM user WHERE (id = ?)', (user_id, ))
        data = cursor.fetchall()
        if not data:
            cursor.execute('INSERT INTO user VALUES(?)', (user_id, ))
            cursor.connection.commit()

    def add(self, user_id, place):
        # FIX... user data must be a function argument
        data = place.data
        data['user_id'] = user_id
        q = ['?'] * len(data.values())
        query = f'INSERT INTO place ({", ".join([str(v) for v in data.keys()])}) VALUES ({",".join(q)})'
        try:
            print(query)
            cursor = self.connect()
            self.add_user(cursor, user_id)
            cursor.execute(query, tuple(data.values()))
            cursor.connection.commit()
        except mariadb.Error as e:
            if place.photopath: delete_photo(place.photopath)
            print(f'Error add: {e}')
            sys.exit(1)
        finally:
            cursor.connection.close()

    def reset(self, user_id):
        query = 'DELETE FROM user WHERE(id = ?)'
        try:
            cursor = self.connect()
            cursor.execute(query, (int(user_id), ))
            cursor.connection.commit()
            delete_photos(user_id)
        except mariadb.Error as e:
            print(f'Error delete: {e}')
        finally:
            cursor.connection.close()
