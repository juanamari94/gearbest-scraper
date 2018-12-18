"""
Author: Juan Amari
File that manages lower-level actions in the Gearbest MySQL database.
"""
from mysql import connector

from database_classes.gearbest_mysql_data import *


class GearbestMySQLManager:
    """
    Class that implements Context Manager in order to properly handle connections, cursors, commits and rollbacks.
    """

    def __init__(self, database=None):
        """
        Initialization method.
        :param database: A database name in case it already exists.
        """
        self.database = database

    def __enter__(self):
        """
        Enter method for the context manager. It creates the database if it doesn't exist.
        """
        if self.database:
            self.cnx = connector.connect(user=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST, database=DB_NAME)
        else:
            self.cnx = connector.connect(user=MYSQL_USER, password=MYSQL_PASSWORD, host=MYSQL_HOST)
        self.cur = self.cnx.cursor(dictionary=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit method for the context manager. It closes connections and cursors.
        """
        self.cur.close()
        self.cnx.close()

    def create_tables(self):
        """
        Creates all gearbest database tables if they don't exist.
        """
        for table_name in TABLES:
            table_description = TABLES[table_name]
            self.cur.execute(table_description)

    def create_table(self, table_query):
        self.cur.execute(table_query)

    def create_and_set_database(self):
        """
        Creates the database if it doesn't exist and sets the instance's cursor to use this database.
        """
        self.cur.execute("CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET 'utf8'" % DB_NAME)
        self.cur.execute("USE %s" % DB_NAME)

    def execute_manipulation_query(self, query, params=None):
        """
        Executes a manipulation query that usually doesn't return anything.
        :param query: The query itself.
        :param params: The parameters for the query.
        """
        self.cur.execute(query, params)
        self.cnx.commit()

    def execute_selection_query(self, query, params=None):
        """
        Executes a selection query and returns the cursor with the reuslts.
        :param query: The query itself.
        :param params: The parameters for the query.
        :return: The cursor containing the results.
        """
        self.cur.execute(query, params)
        return self.cur
