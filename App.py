import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from utils import get_filings,get_itemized_10k,get_itemized_10k_old,read_file,read_files_in_folders,listToString,extract_tables_from_text_file,convert_tables_to_dataframes
import pandas as pd
from transformers import pipeline
import nltk
from litellm import completion
import os
import cohere
from cohere import ClassifyExample
import json
import time
import matplotlib.pyplot as plt

co = cohere.Client("Q7IK6W3dGquUbFx90A7VAqoL88nZgZObkVdRUXEl")
########## Setting the page configuration ###############
st.set_page_config(
    page_title="10-K Filings Analyzer",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

########### Some additional Code ##################

examples = [
    ClassifyExample(text="Stocks are rallying, profits are up!", label = "Bullish"),
    ClassifyExample(text="The economy is showing signs of recovery.", label = "Bullish"),
    ClassifyExample(text="Investors are optimistic about future growth.", label = "Bullish"),
    ClassifyExample(text="Market volatility is causing concern among traders.", label="Bearish"),
    ClassifyExample(text="Uncertainty in global markets is driving risk aversion.", label="Bearish"),
    ClassifyExample(text="The company's earnings report disappointed analysts.", label="Bearish"),
    ClassifyExample(text="Tech stocks are underperforming compared to last quarter.", label="Bearish"),
    ClassifyExample(text="Consumer spending is at an all-time high.", label = "Bullish"),
    ClassifyExample(text="There's a bullish sentiment surrounding renewable energy stocks.", label = "Bullish"),
    ClassifyExample(text="Inflationary pressures are putting downward pressure on the market.", label="Bearish"),
    ClassifyExample(text="Investors are flocking to safe-haven assets amid geopolitical tensions.", label="Bearish"),
    ClassifyExample(text="The Federal Reserve's decision to raise interest rates is worrying investors.", label="Bearish"),
    ClassifyExample(text="Positive earnings surprises are driving the market higher.", label = "Bullish"),
    ClassifyExample(text="Analysts predict alabel =  bullish trend for the next quarter.", label = "Bullish"),
    ClassifyExample(text="Trade tensions between major economies are impacting investor confidence.", label="Bearish")
]




nltk.download('punkt')
summarizer = pipeline('summarization', model='t5-base')
#classifier_model_name = 'nickmuchi/distilroberta-finetuned-financial-text-classification'
classifier_emotions = ['Bullish','Bearish']
# classifier = pipeline('text-classification', model=classifier_model_name)

# classifier = pipeline("zero-shot-classification",
#                       model="facebook/bart-large-mnli")
nltk.download('punkt')
summarizer = pipeline('summarization', model='t5-base')
classifier_model_name = 'nickmuchi/distilroberta-finetuned-financial-text-classification'
classifier_emotions = ['bullish','bearish']
classifier = pipeline('text-classification', model=classifier_model_name)

def find_emotional_sentences(text, emotions, threshold):
    sentences_by_emotion = {}
    for e in emotions:
        sentences_by_emotion[e] = []
    sentences = nltk.sent_tokenize(text)
    print(f'Document has {len(text)} characters and {len(sentences)} sentences.')
    for s in sentences:
        if len(s) <= 512:  # Check if the sentence length is less than or equal to 512(this was added as the model could take tensor of max size 512)
            prediction = classifier(s)
            if prediction[0]['label'] != 'neutral' and prediction[0]['score'] > threshold:
                sentences_by_emotion[prediction[0]['label']].append(s)
    for e in emotions:
        print(f'{e}: {len(sentences_by_emotion[e])} sentences')
    
    return sentences_by_emotion

def summarize_sentences(sentences_by_emotion,year,section, min_length, max_length):
    st.session_state[year][section] = {}
    for k in sentences_by_emotion.keys():
        if (len(sentences_by_emotion[k])!=0):
            text = ' '.join(sentences_by_emotion[k])
            summary = summarizer(text, min_length=min_length, max_length=max_length)
            print(f"{k.upper()}: {summary[0]['summary_text']}\n")
            
            st.session_state[year][section][k] = summary[0]['summary_text']
            #st.write(f" {summary[0]['summary_text']}")
            
    if (len(sentences_by_emotion['bearish'])== 0 or len(sentences_by_emotion['bullish'])==0):
        bullish_ratio = 0
    else:
        bullish_ratio = len(sentences_by_emotion['bullish'])/len(sentences_by_emotion['bearish'])
    st.session_state[year][section]["bullish_ratio"] = bullish_ratio



########## Sidebar ##############
with st.sidebar:
    st.title('🏂 10-K Filings Analyzer')
    
    #year_list = list(df_reshaped.year.unique())[::-1]
    ticker_list = ['AAPL','MSFT','TSLA']
    year_list = ['1995','1996','1997','1998','1999','2000','2001','2002','2003','2004','2005','2006',
                 '2007','2008','2009','2010','2011','2012','2013','2014','2015','2016','2017',
                 '2018','2019','2020','2021','2022','2023']
    selected_ticker = st.selectbox('Select a ticker', ticker_list)
    start_year = st.selectbox('Start Year', year_list)
    end_year = st.selectbox('End Year',year_list)
    start_year = int(start_year)
    end_year = int(end_year)
    #get_filings(selected_ticker)
    
    
#######################
# Dashboard Main Panel
col = st.columns((4.5, 1.5, 2), gap='medium')
result_new = {"2011":None,
              "2012":None,
              "2013":None,
              "2014":None,
              "2015":None,
              "2016":None,
              "2017":None,
              "2018":None,
              "2019":None,
              "2020":None,
              "2021":None,
              "2022":None,
              "2023":None
              }
              
with col[0]:
    
    root_dir = f"sec-edgar-filings/{selected_ticker}"
    #result = read_files_in_folders(root_dir)
    result,result_old,result_new = read_files_in_folders(root_dir)
    #dict=get_itemized_10k(listToString(result[15]),['business'])
    #st.write(dict)
    st.session_state['old'] = result_old
    st.session_state['new'] = result_new
    st.markdown("### Analysis being done, Kindly wait")

for year in range(start_year,end_year+1):

    if year >=2011:       
        filing = result_new[year]
        year = str(year)
        dict = get_itemized_10k((filing),['business','risk','mda','7a'])
        if dict['business'] is None:
            dict['business'] = get_itemized_10k_old(listToString(filing),['business'])['business']
        if dict['risk'] is None:
            dict['risk'] = get_itemized_10k_old(listToString(filing),['risk'])['risk']
        if dict['mda'] is None:
            dict['mda'] = get_itemized_10k_old(listToString(filing),['mda'])['mda']
        if dict['7a'] is None:
            dict['7a'] = get_itemized_10k_old(listToString(filing),['7a'])['7a']
        if year not in st.session_state:
            st.session_state[year] = {}
    else:
        if(year == 1998):
            continue
        if(year in result_old):
            filing = result_old[year]
        else:
            continue
        year = str(year)
        dict = get_itemized_10k_old(listToString(filing),['business','risk','mda','7a'])
        if dict['business'] is None:
            dict['business'] = get_itemized_10k(listToString(filing),['business'])['business']
        if dict['risk'] is None:
            dict['risk'] = get_itemized_10k(listToString(filing),['risk'])['risk']
        if dict['mda'] is None:
            dict['mda'] = get_itemized_10k(listToString(filing),['mda'])['mda']
        if dict['7a'] is None:
            dict['7a'] = get_itemized_10k(listToString(filing),['7a'])['7a']

        if year not in st.session_state:
            st.session_state[year] = {}
    
    
    
    if(dict['business'] is not None):
        sentences_by_emotion = find_emotional_sentences(dict['business'],classifier_emotions,0.7)
        summarize_sentences(sentences_by_emotion,year,'business',min_length=30,max_length=60)
    
    if(dict['risk'] is not None):
        sentences_by_emotion = find_emotional_sentences(dict['risk'],classifier_emotions,0.7)
        summarize_sentences(sentences_by_emotion,year,'risk',min_length=30,max_length=60)
    
    if(dict['mda'] is not None):
        sentences_by_emotion = find_emotional_sentences(dict['mda'],classifier_emotions,0.7)
        summarize_sentences(sentences_by_emotion,year,'mda',min_length=30,max_length=60)
    
    if(dict['7a'] is not None):
        sentences_by_emotion = find_emotional_sentences(dict['7a'],classifier_emotions,0.7)
        summarize_sentences(sentences_by_emotion,year,'7a',min_length=30,max_length=60)
    st.markdown(f"{year} ✅")

year_ratios = []
years=[]
st.markdown('#### Results')
for year in range(start_year,end_year):
    years.append(year)
    year = str(year)
    if year in st.session_state:
        if 'business' in st.session_state[year]:
            if 'bullish_ratio' in st.session_state[year]['business']:
                business_ratio = st.session_state[year]['business']['bullish_ratio']
        else:
            business_ratio = 0
        if 'risk' in st.session_state[year]:
            if 'bullish_ratio' in st.session_state[year]['risk']:
                risk_ratio = st.session_state[year]['risk']['bullish_ratio']
        else:
            risk_ratio = 0
        if 'mda' in st.session_state[year]:
            if 'bullish_ratio' in st.session_state[year]['mda']:
                mda_ratio = st.session_state[year]['mda']['bullish_ratio']
        else:
            mda_ratio = 0
        if '7a' in st.session_state[year]:
            if 'bullish_ratio' in st.session_state[year]['7a']:
                _7a_ratio = st.session_state[year]['7a']['bullish_ratio']
        else:
            _7a_ratio = 0


        year_ratio = (business_ratio+risk_ratio+mda_ratio+_7a_ratio)/4
        year_ratios.append(year_ratio)
    else:
        year_ratio = 0
        year_ratios.append(year_ratio)
    
if len(year_ratios) != 0:
    average_bullish_index = sum(year_ratios)/len(year_ratios)
else:
    average_bullish_index = 0
st.write(f"### Bullish Index: {average_bullish_index}")

x = years
y = year_ratios
df = pd.DataFrame({'x': x, 'y':y})
st.line_chart(df,x='x',y='y')

    # tables_with_headings = extract_tables_from_text_file('sec-edgar-filings/AAPL/10-K/0001193125-11-282113/full-submission.txt')
    # dataframes = convert_tables_to_dataframes(tables_with_headings)
    # desired_heading_name = '2011'
    # desired_df = None
    # for heading_name, df in dataframes:
    #     if heading_name == desired_heading_name:
    #         desired_df = df
    #         break    
    # #summarizer = pipeline('summarization', model='t5-base')
    # st.write(df)

