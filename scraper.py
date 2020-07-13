# -*- coding: utf-8 -*-
"""
Created on Sun Jun 26 11:16:10 2020
@author: Sharmin Shabnam
"""

import pandas as pd
from selenium import webdriver
import re

def goodreads_login(driver, username, password):
    """ Access Goodreads
    Entering log in credentials to access Goodreads Home Page
    
    Args:
    driver(object): WebDriver instance which performs user actions
    username(str): User email
    password(str): User password
    
    Returns:
    None 
    """
    driver.find_element_by_xpath("//*[@id='user_email']").send_keys(username)
    driver.find_element_by_xpath("//*[@id='user_password']").send_keys(password)
    driver.find_element_by_name("next").click()
    
    
def open_page(driver, pagelink):
    """Navigate to the webpage of choice in current tab
    
    Args:
    driver(object): WebDriver instance which performs user actions
    pagelink(str): Page url

    Returns:
    None 
    """
    driver.get(pagelink)
    
    
def open_next_page(driver):
    """Click next page link
    Find 'next page' button and clicking it untill no next page exists.
    
    Args:
    driver(object): WebDriver instance which performs user actions
    
    Returns:
    bool: if page exists
    """
    from selenium.common.exceptions import NoSuchElementException

    try:
        driver.implicitly_wait(3) 
        next = driver.find_element_by_xpath('//a[@rel="next"]')
        next.click()
        return True
    except NoSuchElementException:
        print("Last page reached")
        return False


def open_new_tab(driver, page_link, tab_index):
    """Opens a given link in a new tab.
    Open a new tab tab and open the given link in the new tab
    
    Args:
    driver(object): WebDriver instance which performs user actions
    page_link(str): Url to be opened in this tab
    tab_index(int): Index of new tab location
    
    Returns:
    None
    """
    driver.execute_script('''window.open("about:blank", "_blank");''')
    driver.switch_to.window(driver.window_handles[tab_index])
    driver.get(page_link)

def get_user_ids(driver):
    """Given a GoodReads.com page listing books, return book information.
    Finds all books on the webpage and collects names and hyperlinks for each book
    
    Args:
    driver(object): WebDriver instance which performs user actions
    
    Returns:
    Pandas DataFrmae(object): list of book names and hyperlinks
    """  
    
    freinds_id = []
    next_page_exists = True
    
    # Open each page and scrape user id
    while next_page_exists:         
        elems = driver.find_elements_by_class_name('userLink')
        uid = re.compile(r"(\d+)")
        for elem in elems:
            href = elem.get_attribute("href")
            match = uid.search(href)
            if match is not None:
                 freinds_id.append(match.group(1))
        next_page_exists = open_next_page(driver)
    
    return freinds_id    

def users_book_list(driver, column_names):
    """Extract all the information from the read shelf.
    Collects the names, authors name, rating, and hyperlinks of all books on 
    the read shelf
    
    Args:
    driver(object): WebDriver instance which performs user actions
    
    Returns:
    Pandas DataFrmae(object): Dataframe with book names and other information
    """
    
    tbody = driver.find_element_by_xpath("//*[@id='booksBody']")
    try:
        
        book_name = [td.text for td in tbody.find_elements_by_xpath("//*[contains(@id, 'review')]/td[4]/div/a")]
        book_author = [td.text for td in tbody.find_elements_by_xpath("//*[contains(@id, 'review')]/td[5]/div/a")]
        book_rating = [td.get_attribute("title") for td in tbody.find_elements_by_xpath("//*[contains(@id, 'review')]/td[14]/div/span")]
        book_link = [td.get_attribute("href") for td in tbody.find_elements_by_xpath("//*[contains(@id, 'review')]/td[4]/div/a")]
        user_book_dict = dict(zip(column_names[1:],
                                  [book_name,
                                   book_author,
                                   book_rating,
                                   book_link]))
        user_book_data = pd.DataFrame(user_book_dict)
    except Exception as e: 
        print('Information not found because error: ', e)
        pass
    return user_book_data

                
def remap_ratings(data, dict_ratings):
    """Remap rating column
    This function takes in a dataframe of user and books
    and dictionary of rating labels, and replace the 
    rating values (previously strings) into the integers.
    
    Args:
    data(object): dataframe of user and books
    dict_ratings(dictionary): dictionary of rating labels ex: {{'col1':{1:'A',2:'B'}}
    
    Returns:
    Pandas DataFrmae(object): dataframe of user and books with ratings remapped
    """
    
    for field,values in dict_ratings.items():
        print("Remapping column %s"%field)
        data.replace({field:values},inplace=True)
    print("Completed")

    return data



def extract_each_book_data(driver, href):
    """Visit each books in goodreads.com page in new tab and extract
    book details such as book genres and ratings
    
    Args:
    driver(object): WebDriver instance which performs user actions
    href(str): link to book page
    
    Returns:
    genre(str): list of genres associated with book
    additional_info(list): list of additional info of the book such as
    number of pages, original title, average rating, total ratings, total reviews
    """
    
    # Open new tab for a particular book hyperlink
    open_new_tab(driver, href, 1)
    
    # Extract book data
    try:
        average_rating = driver.find_element_by_xpath("//*[@id='bookMeta']/span[@itemprop = 'ratingValue']").text
        total_ratings = driver.find_element_by_xpath("//*[@id='bookMeta']/a[2]/meta[@itemprop = 'ratingCount']").get_attribute('content')
        total_reviews = driver.find_element_by_xpath("//*[@id='bookMeta']/a[3]/meta[@itemprop = 'reviewCount']").get_attribute('content')
        number_of_pages = driver.find_element_by_xpath("//*[@id='details']/div[1]/span[@itemprop = 'numberOfPages']").text        
        try:
            ori_title = driver.find_element_by_xpath("//*[@id='bookDataBox']/div[1]/div[@class = 'infoBoxRowItem']").text
        except Exception as e:
            print('Information not found because error: ', e)
            ori_title = None
            pass            
    except Exception as e: 
        print('Information not found because error: ', e)
        number_of_pages, ori_title, average_rating, total_ratings, total_reviews = None, None, None, None, None
        pass
    
    # Extract genre information
    elements = driver.find_elements_by_class_name('actionLinkLite.bookPageGenreLink')
    genres = []
    for item in elements:
        if 'users' not in item.text:
            genres.append(item.text)
    
    # Close the current tab and switch to first tab
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
    # Create list of book data
    additional_info = [number_of_pages,
                       ori_title,
                       average_rating,
                       total_ratings,
                       total_reviews]
    
    return genres, additional_info


def collate_books_from_id(driver, friends_id):
    """Collate book information from every user
    Create dataframe from list of books read by each user
    
    Args:
    driver(object): WebDriver instance which performs user actions
    friends_id(list): list of user id
    
    Returns:
    Pandas DataFrmae(object): dataframe of user and books 
    """
    
    # Create book data columns, dataframe and rating dictionary
    column_names = ['UserID',
                    'Title',
                    'Author',
                    'Rating',
                    'Link'] 
    user_book_list = pd.DataFrame(columns=column_names)
    dict_ratings = {'Rating':{''                :0,
                              'did not like it' :1,
                             'it was ok'        :2,
                             'liked it'         :3,
                             'really liked it'  :4,
                             'it was amazing'   :5}}
        
    for user_id in friends_id:
        new_link = "https://www.goodreads.com/review/list/{}?shelf=read".format(user_id)
        
        #Open new tab for each user ids shelf
        open_new_tab(driver, new_link, 1)
        next_page_exists = True 
        
        # Extract all the names of books in the read shelf
        while next_page_exists:  
            driver.implicitly_wait(3) 
            user_book_data = users_book_list(driver,
                                             column_names)
            user_book_data['UserID'] = user_id 
            user_book_list = user_book_list.append(user_book_data, ignore_index=True)
            next_page_exists = open_next_page(driver)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    
    user_book_list = remap_ratings(user_book_list,
                                   dict_ratings)
    return user_book_list


def collect_all_books_data(driver, user_book_list):
    """Collate book information from every user
    Create dataframe from list of books read by each user
    
    Args:
    driver(object): WebDriver instance which performs user actions
    friends_id(list): list of user id
    
    Returns:
    Pandas DataFrmae(object): dataframe of user and books 
    """
    
    # Create dataframe
    books_data = user_book_list[['Title',
                                 'Author',
                                 'Rating',
                                 'Link']]
    genres_list = []
    new_columns = ['Number_of_pages',
                   'Original_title',
                   'Average_rating',
                   'Total_ratings',
                   'Total_reviews']
    books_data = books_data.reindex(columns=books_data.columns.tolist() + new_columns)   
    
    # Loop through each books link to extract their data
    for index, row in books_data.iterrows():
        genres, additional_info = extract_each_book_data(driver,
                                                         row['Link'])
        books_data.loc[index,'Genre'] = ','.join(genres)
        books_data.loc[index, new_columns] = additional_info
        genres_list.extend(genres)   
    
    # Extracting the most common genres
    genre_data = pd.DataFrame(genres_list,
                              columns=['Genre'])
    return books_data, genre_data



def main():

    DRIVER_PATH = 'chromedriver.exe'

    # Goodreads login credentials
    USERNAME = 'youremail'
    PASSWORD = 'yourpassowrd'

    # Open Goodreads and log in with credentials
    driver = webdriver.Chrome(executable_path=DRIVER_PATH)
    open_page(driver,
               pagelink='https://www.goodreads.com/user/sign_in')
    goodreads_login(driver,
                    username=USERNAME,
                    password=PASSWORD)
    open_page(driver,
               pagelink='https://www.goodreads.com/friend')
    
    # Extract IDs
    friends_id = get_user_ids(driver)
    user_book_list = collate_books_from_id(driver,
                                           friends_id)
    books_data, genre_data = collect_all_books_data(driver,
                                                    user_book_list)
    
    # Writing to file
    books_data.to_csv('data/books_data.csv')
    genre_data.to_csv('data/genre_data.csv')

    driver.close()


if __name__ == '__main__':
    main()
    
