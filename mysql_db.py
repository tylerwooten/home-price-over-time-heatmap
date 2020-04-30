
import sqlalchemy as db
import pymysql
import pandas as pd
from secret import Secret
 

class RealEstateDB():
    def open_connection( self ):
        self.engine = db.create_engine( Secret().db_address, pool_recycle=3600 )
        self.metadata = db.MetaData()
        self.connection = self.engine.connect()
        self.table_name = Secret().table_name
        self.table = db.Table( self.table_name, self.metadata, autoload=True, autoload_with=self.engine )

    def close_connection( self ):
        self.connection.close()

    def print_results( self, count=3 ):
        df = pd.DataFrame( self.results )
        df.columns = self.columns
        print( df.head( count ) )

    def read_row( self, column_id ):
        query = db.select( [ self.table ] ).where( self.table.columns.id == int(column_id) )
        results = self.connection.execute( query )
        self.columns = results.keys()
        df = pd.DataFrame( results )
        df.columns = self.columns
        return( df )

    def update_row( self, column_id, attributes ):
        self.add_new_attributes_to_table( attributes )

        query = db.update( self.table ).values( attributes )
        query = query.where( self.table.columns.id == column_id )
        results = self.connection.execute( query )
        print('\n~~~~~~~~~~~~~~~~~~~~~~~~~~~', 'Wrote ID to DB:', str(column_id), '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n')

    def update_all( self, attributes ):
        query = self.db.update( self.table ).values( attributes )
        results = self.connection.execute( query )
        print( 'updated all rows with ' + str( attributes ) )

    def add_new_attributes_to_table( self, attributes ):
        for column_name, value in attributes.items():
            if column_name not in self.columns:
                try:
                    self.connection.execute( 'ALTER TABLE {} ADD COLUMN {} {}'.format( self.table_name, str( column_name ), 'text' ) )
                    print( 'add column {} to {}'.format( column_name, self.table_name ) )
                except:
                    print( 'could not add column: ', column_name )
        self.close_connection() # reopen the connection so that the row can now be updated
        self.open_connection()
        




