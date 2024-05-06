# Python file for the year 1999
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from utils import get_filings,get_itemized_10k,get_itemized_10k_old,read_file,read_files_in_folders,listToString,extract_tables_from_text_file,convert_tables_to_dataframes
import pandas as pd
from transformers import pipeline
import nltk
import streamlit.components.v1 as components

year = 1999
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
result_old = st.session_state['old']
components.html(listToString(result_old[year]),height=600,scrolling=True)


year = str(year)
dict = {}
if year in st.session_state:
    dict = st.session_state[year]
    st.markdown("### Business")
    if 'business' in st.session_state[year]:
        st.write(f"Bullish : {st.session_state[year]['business']['bullish']}\n")
        st.write(f"Bearish : {st.session_state[year]['business']['bearish']}\n")
        st.write(f"Bullish Ratio : {st.session_state[year]['business']['bullish_ratio']}\n")

    st.markdown("### Risk")
    if 'risk' in st.session_state[year]:
        st.write(f"Bullish : {st.session_state[year]['risk']['bullish']}\n")
        st.write(f"Bearish : {st.session_state[year]['risk']['bearish']}\n")
        st.write(f"Bullish Ratio : {st.session_state[year]['risk']['bullish_ratio']}\n")

    st.markdown("### MDNA")
    if 'mda' in st.session_state[year]:
        st.write(f"Bullish : {st.session_state[year]['mda']['bullish']}\n")
        st.write(f"Bearish : {st.session_state[year]['mda']['bearish']}\n")
        st.write(f"Bullish Ratio : {st.session_state[year]['mda']['bullish_ratio']}\n")

    st.markdown("### Business")
    if '7a' in st.session_state[year]:
        st.write(f"Bullish : {st.session_state[year]['7a']['bullish']}\n")
        st.write(f"Bearish : {st.session_state[year]['7a']['bearish']}\n")
        st.write(f"Bullish Ratio : {st.session_state[year]['7a']['bullish_ratio']}\n")
else:
    st.write(f"File Not Found for the year {year}")

