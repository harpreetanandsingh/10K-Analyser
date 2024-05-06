import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from utils import get_filings,get_itemized_10k,get_itemized_10k_old,read_file,read_files_in_folders,listToString,extract_tables_from_text_file,convert_tables_to_dataframes
import pandas as pd
from transformers import pipeline
import nltk

########## Setting the page configuration ###############
st.set_page_config(
    page_title="10-K Filings Analyzer",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

########### Some additional Code ##################
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
    selected_ticker = st.selectbox('Select a ticker', ticker_list)
    #get_filings(selected_ticker)
    
    
#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')
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
    st.markdown('#### Filings')
    root_dir = f"sec-edgar-filings/{selected_ticker}"
    #result = read_files_in_folders(root_dir)
    result,result_old,result_new = read_files_in_folders(root_dir)
    #dict=get_itemized_10k(listToString(result[15]),['business'])
    #st.write(dict)
    st.session_state['old'] = result_old
    st.session_state['new'] = result_new
st.markdown("### Analysis being done, Kindly wait")

for year in range(1995,2024):

    if year >=2011:       
        filing = result_new[year]
        year = str(year)
        dict = get_itemized_10k(listToString(filing),['business','risk','mda','7a'])
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
        if(result_old[year] is not None):
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
    
    
    st.markdown(f"{year} ✅")
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
    
year_ratios = []
with col[1]:
    st.markdown('#### Results')
    for year in range(1995,2024):
        year = str(year)
        if year in st.session_state:
            if 'business' in st.session_state[year]:
                if 'bullish_ratio' in st.session_state[year]['business']:
                    business_ratio = st.session_state[year]['business']['bullish_ratio']
            if 'risk' in st.session_state[year]:
                if 'bullish_ratio' in st.session_state[year]['risk']:
                    risk_ratio = st.session_state[year]['risk']['bullish_ratio']
            if 'mda' in st.session_state[year]:
                if 'bullish_ratio' in st.session_state[year]['mda']:
                    mda_ratio = st.session_state[year]['mda']['bullish_ratio']
            if '7a' in st.session_state[year]:
                if 'bullish_ratio' in st.session_state[year]['7a']:
                    _7a_ratio = st.session_state[year]['7a']['bullish_ratio']

            year_ratio = (business_ratio+risk_ratio+mda_ratio+_7a_ratio)/4
            year_ratios.append(year_ratio)
    
    print(year_ratios[2])
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

