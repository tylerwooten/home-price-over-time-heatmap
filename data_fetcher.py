from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from mysql_db import RealEstateDB
import pandas as pd
import time
from selenium.webdriver.common.by import By
from secret import Secret


class DataFetcher():

    def fetch_row_from_db( self, column_id ):
        ''' read in row from mySQL DB based on column id '''
        self.db = RealEstateDB()
        self.db.open_connection()
        self.home = self.db.read_row( column_id )
        #print( self.home.head(4) )

        if self.home.iloc[0]['NUMBER'] and self.home.iloc[ 0 ][ 'STREET' ]:
            self.street_num  = str( self.home.iloc[ 0 ][ 'NUMBER' ] )
            self.street_name = self.home.iloc[ 0 ][ 'STREET' ]
    
        return self.street_num, self.street_name

    def fetch_home_info_from_address( self, year='2020', street_num=None, street_name=None ):
        ''' plug in address and year into site and create a dataframe of the data that is returned as a dictionary '''
        time.sleep( 3 ) # sleep to not put too much pressure on site
        home = self.home

        url = Secret().url

        driver = webdriver.Chrome( executable_path='dependencies/chromedriver' )
        self.driver = driver
        driver.get(url)

        search_by_address_button = driver.find_elements_by_xpath('//*[@id="s_addr"]')[ 0 ]
        search_by_address_button.click()

        year_box        = driver.find_elements_by_xpath( '//*[@id="Real_addr"]/table/tbody/tr[4]/td[1]/select' )[ 0 ]
        street_no_box   = driver.find_elements_by_xpath( '//*[@id="Real_addr"]/table/tbody/tr[4]/td[2]/input' )[ 0 ]
        street_name_box = driver.find_elements_by_xpath( '//*[@id="Real_addr"]/table/tbody/tr[4]/td[3]/input' )[ 0 ]

        year_box.send_keys( year )
        street_no_box.send_keys( street_num )
        street_name_box.send_keys( street_name )
        street_name_box.send_keys( Keys.RETURN )

        time.sleep( 15 ) # sleep to not put too much pressure on site
        iframe = self.driver.find_element_by_tag_name( 'iframe' )
        self.driver.switch_to.frame( iframe ) # after the iframe loads, switch into it for selenium to search by element

        # CHECK IF WE GOT RESULTS
        try:
            if driver.find_element_by_class_name( 'Open' ): # if this element exists, the results were empty
                print( '\n~~~~~~~~~~~~~~~~~~~~~~~', 'No data on this year and address: ', year, ': ' ,street_num, ' ', street_name,'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n' )
                driver.quit()
                return False # this address had no results. skip it
        except:
            pass
        
        for table in driver.find_elements_by_class_name('bgcolor_1'):
            sub_headings = [ x.text.upper().replace(':','').replace('/','').replace('#','').replace('\n','_').replace(' ','_').encode('ascii', errors='ignore').decode() for x in table.find_elements_by_class_name('sub_header') ]
            data_points = [ x.text.upper() for x in table.find_elements_by_class_name( 'data' ) ]

            if len( data_points ) + len( sub_headings ) <= 1: # if there is one data or point subheading or less, ignore it
                continue

            elif len( data_points ) == len( sub_headings ): # if the lengths are the same, I should be able to map them 1 to 1 to df
                for i, sub in enumerate( sub_headings ):
                    home[ sub ] = data_points[ i ] # assign the subheading value to the data value
                    continue

            elif 'VALUATIONS' in sub_headings:
                home[ 'PREVIOUS_LAND_VALUATION_MARKET' ]           = data_points[ 7 ]
                home[ 'PREVIOUS_LAND_VALUATION_APPRAISED' ]        = data_points[ 8 ]
                home[ 'CURRENT_LAND_VALUATION_MARKET' ]            = data_points[ 10 ]
                home[ 'CURRENT_LAND_VALUATION_APPRAISED' ]         = data_points[ 11 ]
                home[ 'PREVIOUS_IMPROVEMENT_VALUATION_MARKET' ]    = data_points[ 13 ]
                home[ 'PREVIOUS_IMPROVEMENT_VALUATION_APPRAISED' ] = data_points[ 14 ]
                home[ 'CURRENT_IMPROVEMENT_VALUATION_MARKET' ]     = data_points[ 16 ]
                home[ 'CURRENT_IMPROVEMENT_VALUATION_APPRAISED' ]  = data_points[ 17 ]
                home[ 'PREVIOUS_TOTAL_VALUATION_MARKET' ]          = data_points[ 19 ]
                home[ 'PREVIOUS_TOTAL_VALUATION_APPRAISED' ]       = data_points[ 20 ]
                home[ 'CURRENT_TOTAL_VALUATION_MARKET' ]           = data_points[ 22 ]
                home[ 'CURRENT_TOTAL_VALUATION_APPRAISED' ]        = data_points[ 23 ]

            elif 'LAND' and 'MARKET_VALUE_LAND' in sub_headings:
                continue # we don't want to get this data for now
                #subs_for_df = sub_headings[2:14] # get the 12 not including "land" and "market value land"

            elif 'EXTRA_FEATURES' or 'OWNER_AND_PROPERTY_INFORMATION' or 'VALUE_STATUS_INFORMATION' or 'IMPR_SQ_FT' or 'EXEMPTIONS_AND_JURISDICTIONS' in sub_headings:
                continue # we don't want to get this data for now

            else:
                print( 'SUB: ' + str( len( sub_headings ) ) +  str( sub_headings ) )
                print( 'DATA: ' + str( len( data_points ) ) +  str( data_points ) )
                print( '\n' )

        try:
            building_data = driver.find_element_by_class_name('bgcolor_3')
            rows = building_data.find_elements( By.TAG_NAME, 'tr' ) # get all of the rows in the table
            table_data = []
            for row in rows:
                table_data = row.find_elements( By.TAG_NAME, 'td' ) 
                for data in table_data:
                    table_data.append(data.text)

            headers = [ val for idx,val in enumerate( table_data ) if idx % 2 == 0 ]
            values  = [ val for idx,val in enumerate( table_data ) if idx % 2 == 1 ]

            for idx, header in enumerate(header):
                formatted_header = header.replace(' ', '_').replace(':','').replace('/','').replace('#','').replace('\n','_').upper() # change string to ascii camel case format
                home[ formatter_header ] = values[ idx ]
        except:
            print( 'Unable to get additional building data.' )
            pass

        home_dict = home.to_dict( 'records' )[ 0 ]

        return home_dict

def process_many_from_db( start_id=3, end_id=10 ):
    for column_id in range( start_id, end_id ):
        new_home = DataFetcher()
        street_num, street_name = new_home.fetch_row_from_db( column_id )
        home_dict = new_home.fetch_home_info_from_address( '2020', street_num, street_name )
        if home_dict:
            new_home.db.update_row( column_id, home_dict )
        new_home.driver.quit()

process_many_from_db(3,10)
