from sec_edgar_downloader import Downloader
import re
import unicodedata
from bs4 import BeautifulSoup as bs
import requests
import os
import pandas as pd
import nltk
from transformers import pipeline
import streamlit as st

def listToString(s):
 
    # initialize an empty string
    str1 = ""
 
    # traverse in the string
    for ele in s:
        str1 += ele
 
    # return string
    return str1

def get_year(partial_path):
    # Split the partial path by '/'
    parts = partial_path.split('/')
    year = parts[3].split('-')[1]
    if year:
        year = int(year)
    else:
        return 1000
    if(year < 30 or year == 0):
        return year + 2000
    else:
        return year + 1900

# Function to read the content of a file and return it as a string
def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Main function to iterate over folders and read files
@st.cache_data
def read_files_in_folders(root_dir):
    data_arrays = []
    dict_old = {}
    dict_new = {}
    for company_folder in os.listdir(root_dir):
        company_folder_path = os.path.join(root_dir, company_folder)
        if os.path.isdir(company_folder_path):
            for filing_folder in os.listdir(company_folder_path):
                filing_folder_path = os.path.join(company_folder_path, filing_folder)
                if os.path.isdir(filing_folder_path):
                    year = get_year(filing_folder_path)
                    print(year)
                    file_path = os.path.join(filing_folder_path, "full-submission.txt")
                    if os.path.exists(file_path):
                        file_data = read_file(file_path)
                        data_arrays.append(file_data.split('\n'))  # Splitting data by lines and storing in arrays
                        if year < 2011:
                            dict_old[year] = file_data.split('\n')
                        else:
                            dict_new[year] = file_data.split('\n')

    return data_arrays,dict_old,dict_new

# Assuming your current working directory contains 'sec-edgar-filings'

# Now 'result' contains arrays with data from each 'full-submission.txt' file in each folder.
# You can access the data like result[0], result[1], etc.
def get_filings(string):
    dl = Downloader("Anonymous", "my.email@domain.com")
    dl.get("10-K", string, limit=29)
 
@st.cache_data
def get_itemized_10k(text, sections: list[str]=['business', 'risk', 'mda', '7a']):
    '''Extract ITEM from 10k filing text.

    Args:
        fname: str, the file name (ends with .txt)
        sections: list of sections to extract

    Returns:
        itemized_text: dict[str, str], where key is the section name and value is the text
    '''
    fname="hi"
    # def get_text(link):
    #     page = requests.get(link, headers={'User-Agent': 'Mozilla'})
    #     html = bs(page.content, "lxml")
    #     text = html.get_text()
    #     text = unicodedata.normalize("NFKD", text).encode('ascii', 'ignore').decode('utf8')
    #     text = text.split("\n")
    #     text = " ".join(text)
    #     return(text)
    # text = get_text(link)

    def extract_text(text, item_start, item_end):
        '''
        Args:
            text: 10K filing text
            item_start: compiled regex pattern
            item_end: compiled regex pattern
        '''
        item_start = item_start
        item_end = item_end
        starts = [i.start() for i in item_start.finditer(text)]
        ends = [i.start() for i in item_end.finditer(text)]

        # if no matches, return empty string
        if len(starts) == 0 or len(ends) == 0:
            return None

        # get possible start/end positions
        # we may end up with multiple start/end positions, and we'll choose the longest
        # item text.
        positions = list()
        for s in starts:
            control = 0
            for e in ends:
                if control == 0:
                    if s < e:
                        control = 1
                        positions.append([s,e])

        # get the longest item text
        item_length = 0
        item_position = list()
        for p in positions:
            if (p[1]-p[0]) > item_length:
                item_length = p[1]-p[0]
                item_position = p

        item_text = text[item_position[0]:item_position[1]]

        return item_text

    # extract text for each section
    results = {}

    for section in sections:

        # ITEM 1: Business
        # if there's no ITEM 1A then it ends at ITEM 2
        if section == 'business':
            try:
                item1_start = re.compile("i\s?tem[s]?\s*[1I]\s*[\.\;\:\-\_]*\s*\\b", re.IGNORECASE)
                item1_end = re.compile("item\s*1a\s*[\.\;\:\-\_]*\s*Risk|item\s*2\s*[\.\,\;\:\-\_]*\s*(Desc|Prop)", re.IGNORECASE)
                business_text = extract_text(text, item1_start, item1_end)
                if business_text:
                    results['business'] = business_text
                else:
                    results['business'] = None
            except Exception as e:
                results['business'] = None
                print(f'Error extracting ITEM 1: Business for {fname}')
            
        # ITEM 1A: Risk Factors
        # it ends at ITEM 2
        if section == 'risk':
            try:
                item1a_start = re.compile("(?<!,\s)item\s*1a[\.\;\:\-\_]*\s*Risk", re.IGNORECASE)
                item1a_end = re.compile("item\s*2\s*[\.\;\:\-\_]*\s*(Desc|Prop)|item\s*[1I]\s*[\.\;\:\-\_]*\s*\\b", re.IGNORECASE)
                risk_text = extract_text(text, item1a_start, item1a_end)
                if risk_text:
                    results['risk'] = risk_text
                else:
                    results['risk'] = None
            except Exception as e:
                results['risk'] = None
                print(f'Error extracting ITEM 1A: Risk Factors for {fname}')
                
        # ITEM 7: Management's Discussion and Analysis of Financial Condition and Results of Operations
        # it ends at ITEM 7A (if it exists) or ITEM 8
        if section == 'mda':
            try:
                item7_start = re.compile("item\s*7\s*[\.\;\:\-\_]*\s*\\bM", re.IGNORECASE)
                item7_end = re.compile("item\s*7a\s*[\.\;\:\-\_]*[\s\n]*Quanti|item\s*8\s*[\.\,\;\:\-\_]*\s*Finan", re.IGNORECASE)
                item7_text = extract_text(text, item7_start, item7_end)
                if item7_text:
                    results['mda'] = item7_text
                else:
                    results['mda'] = None
            except Exception as e:
                results['mda'] = None
                print(f'Error extracting ITEM 7: MD&A for {fname}')

        # ITEM 7A: Quantitative and Qualitative Disclosures About Market Risk
        # 
        if section == '7a':
            try:
                item7a_start = re.compile("item\s*7a\s*[\.\;\:\-\_]*[\s\n]*Quanti", re.IGNORECASE)
                item7a_end = re.compile("item\s*8\s*[\.\,\;\:\-\_]*\s*Finan", re.IGNORECASE)
                item7a_text = extract_text(text, item7a_start, item7a_end)
                if item7a_text:
                    results['7a'] = item7a_text
                else:
                    results['7a'] = None
            except Exception as e:
                results['7a'] = None
                print(f'Error extracting ITEM 7A: for {fname}')
    
    return results
 
@st.cache_data
def get_itemized_10k_old(text, sections: list[str]=['business', 'risk', 'mda', '7a']):
    '''Extract ITEM from 10k filing text.

    Args:
        fname: str, the file name (ends with .txt)
        sections: list of sections to extract

    Returns:
        itemized_text: dict[str, str], where key is the section name and value is the text
    '''
    fname="hi"
    # def get_text(link):
    #     page = requests.get(link, headers={'User-Agent': 'Mozilla'})
    #     html = bs(page.content, "lxml")
    #     text = html.get_text()
    #     text = unicodedata.normalize("NFKD", text).encode('ascii', 'ignore').decode('utf8')
    #     text = text.split("\n")
    #     text = " ".join(text)
    #     return(text)
    # text = get_text(link)

    def extract_text(text, item_start, item_end):
        '''
        Args:
            text: 10K filing text
            item_start: compiled regex pattern
            item_end: compiled regex pattern
        '''
        item_start = item_start
        item_end = item_end
        starts = [i.start() for i in item_start.finditer(text)]
        ends = [i.start() for i in item_end.finditer(text)]

        # if no matches, return empty string
        if len(starts) == 0 or len(ends) == 0:
            return None

        # get possible start/end positions
        # we may end up with multiple start/end positions, and we'll choose the longest
        # item text.
        positions = list()
        for s in starts:
            control = 0
            for e in ends:
                if control == 0:
                    if s < e:
                        control = 1
                        positions.append([s,e])

        # get the longest item text
        item_length = 0
        item_position = list()
        for p in positions:
            if (p[1]-p[0]) > item_length:
                item_length = p[1]-p[0]
                item_position = p

        item_text = text[item_position[0]:item_position[1]]

        return item_text

    # extract text for each section
    results = {}

    for section in sections:

        # ITEM 1: Business
        # if there's no ITEM 1A then it ends at ITEM 2
        if section == 'business':
            try:
                item1_start = re.compile("item&nbsp;1.\sbusiness", re.IGNORECASE)
                item1_end = re.compile("item&nbsp;1a.\srisk", re.IGNORECASE)
                business_text = extract_text(text, item1_start, item1_end)
                if business_text:
                    soup = bs(business_text, 'html.parser')
                    text = soup.get_text()
                    clean_text = re.sub(r'\s+', ' ', text)
                    clean_text = re.sub(r'[^\w\s.:]', '', clean_text)
                    results['business'] = clean_text
                else:
                    results['business'] = None
            except Exception as e:
                results['business'] = None
                print(f'Error extracting ITEM 1: Business for {fname}')
            
        # ITEM 1A: Risk Factors
        # it ends at ITEM 2
        if section == 'risk':
            try:
                item1a_start = re.compile("item&nbsp;1a.\srisk", re.IGNORECASE)
                item1a_end = re.compile("item&nbsp;2.\s", re.IGNORECASE)
                risk_text = extract_text(text, item1a_start, item1a_end)
                if(risk_text):
                    soup = bs(risk_text, 'html.parser')
                    text = soup.get_text()
                    clean_text = re.sub(r'\s+', ' ', text)
                    clean_text = re.sub(r'[^\w\s.:]', '', clean_text)
                    results['risk'] = clean_text
                else:
                    results['risk'] = None
            except Exception as e:
                results['risk'] = None
                print(f'Error extracting ITEM 1A: Risk Factors for {fname}')
                
        # ITEM 7: Management's Discussion and Analysis of Financial Condition and Results of Operations
        # it ends at ITEM 7A (if it exists) or ITEM 8
        if section == 'mda':
            try:
                item7_start = re.compile("item&nbsp;7.\sMana", re.IGNORECASE)
                item7_end = re.compile("item&nbsp;7a.\sQuanti", re.IGNORECASE)
                item7_text = extract_text(text, item7_start, item7_end)
                if item7_text:
                    soup = bs(item7_text, 'html.parser')
                    text = soup.get_text()
                    clean_text = re.sub(r'\s+', ' ', text)
                    clean_text = re.sub(r'[^\w\s.:]', '', clean_text)
                    results['mda'] = clean_text
                else:
                    results['mda'] = None
                
            except Exception as e:
                results['mda'] = None
                print(f'Error extracting ITEM 7: MD&A for {fname}')

        # ITEM 7A: Quantitative and Qualitative Disclosures About Market Risk
        # 
        if section == '7a':
            try:
                item7a_start = re.compile("item&nbsp;7a.\sQuanti", re.IGNORECASE)
                item7a_end = re.compile("item&nbsp;8.", re.IGNORECASE)
                item7a_text = extract_text(text, item7a_start, item7a_end)
                if item7a_text:
                    soup = bs(item7a_text, 'html.parser')
                    text = soup.get_text()
                    clean_text = re.sub(r'\s+', ' ', text)
                    clean_text = re.sub(r'[^\w\s.:]', '', clean_text)
                    results['7a'] = clean_text
                else:
                    results['7a'] = None
            except Exception as e:
                results['7a'] = None
                print(f'Error extracting ITEM 7A: for {fname}')
    
    return results

def extract_tables_from_text_file(text_file):
    with open(text_file, 'r') as file:
        text = file.read()

    # Find all sections containing tables
    table_sections = re.findall(r'<TABLE[^>]*>.*?<\/TABLE>', text, re.DOTALL)

    # Extract tables with their corresponding headings
    tables_with_headings = []
    for section in table_sections:
        # Extract the heading of the table
        heading = re.search(r'<B[^>]*>(.*?)<\/B>', section, re.DOTALL)
        heading_name = heading.group(1) if heading else None

        # Extract table rows
        table_rows = re.findall(r'<TR[^>]*>.*?<\/TR>', section, re.DOTALL)
        table_data = []
        for row in table_rows:
            # Remove HTML tags from each row and replace non-breaking space with regular space
            cells = [re.sub(r'<[^>]*>', '', cell).replace('&nbsp;', ' ').strip() for cell in re.findall(r'<TD[^>]*>(.*?)<\/TD>', row, re.DOTALL)]
            # Filter out empty rows
            if any(cell for cell in cells if cell.strip() != ''):
                table_data.append(cells)
        # Add table data with heading name to tables_with_headings list
        if table_data:
            tables_with_headings.append((heading_name, table_data))

    return tables_with_headings

def convert_tables_to_dataframes(tables_with_headings):
    dataframes = []
    for heading_name, table_data in tables_with_headings:
        # Find the maximum number of columns in the table
        max_cols = max(len(row) for row in table_data)
        # Pad rows with empty strings to match the length of the header
        padded_table_data = [row + [''] * (max_cols - len(row)) for row in table_data]
        # Convert to DataFrame
        df = pd.DataFrame(padded_table_data[1:], columns=padded_table_data[0])
        dataframes.append((heading_name, df))
    return dataframes



# def read_fileurl_in_folders(root_dir):
#     arrays_with_years = []
#     for company_folder in os.listdir(root_dir):
#         company_folder_path = os.path.join(root_dir, company_folder)
#         if os.path.isdir(company_folder_path):
#             for filing_folder in os.listdir(company_folder_path):
#                 filing_folder_path = os.path.join(company_folder_path, filing_folder)
#                 if os.path.isdir(filing_folder_path):
#                     file_path = os.path.join(filing_folder_path, "full-submission.txt")
#                     if os.path.exists(file_path):
#                         year = get_year(file_path)
#                         url_arrays.append(url)
#     return url_arrays

