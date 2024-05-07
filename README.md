# 10K-Analyser
 
This is an SEC 10-K form analyzer which extracts useful data from the 10-K filings of a company(last 29 years) and gives insights into the data. It is implemented as a streamlit application for ease of use.

The Project Demo Video can be found `[here]``(https://www.loom.com/share/f6485d1f0d224d89af0e9b02dcebb264?sid=ef11b2ef-d979-44c8-bb4b-5c6bfd2bdd9f)`

# How to Install

In this project, huggingface models are used for classification and summarization since the free version of all the LLM APIs are limited to 1000 calls/month which were used up during testing. Due to this reason, this app could not be deployed on streamlit(since we get only 1 GB on the free Streamlit Community Cloud).
To run this app locally, follow the following steps:

Step 1 : Clone this repository\n
Step 2(Recommended) : Create a new virtual environment in conda using `conda create --name myenv python=3.9` and activate the environment using `conda activate myenv`\
Step 3 : Navigate inside the respository and type `pip install -r requirements.txt`\
Step 4 : Just run `streamlit run App.py` to launch the streamlit application locally.\
Step 5 : Now select that start year and the end year and the ticker of the company that you want to analyze. 
        (Note : Currently in this repository, only the filings of AAPL are present. If you want any company other than that, uncomment the `get_filings` line from the App.py file.\

# Methodology Used

1. We extract four sections from the filings namely Item 1 : Business, Item 1a:Risk Factors, Item 7: MDNA and Item 7a.
2. We extract the sections from the filings using two functions get_itemized_10k(for the new filings after 2011) and get_itemized_10k_old (for old filings i.e. before 2011) since the format of the filings changed around this time. These functions are available in the utils.py file and have used regular expressions to extract the text.In some filings where the regular expression does not correspond the one used in earlier filings, we skip the section.
3. For each section, the sentences are classified into Bullish or Bearish using `nickmuchi/distilroberta-finetuned-financial-text-classification` model available on huggingface. The summarization of bullish and bearish sentences is done using `t5-base` model available on huggingface.
4. The bullish ratio (i.e. no. of bullish sentences/ no. of bearish sentences) is calculated for section and the average bullish ratio for all the sections is considered as the bullish ratio for that year.
5. The bullish index is calculated as the average of the bullish ratios for each year and a graph is plotted on the main page(bullish ratio vs year).
6. In the respective page of every year in consideration, the summaries of each section are listed along with bullish ratio for each section.

# Why is Bullish Ratio used for the insight?
This is since we can analyze the performance of the company (between any two values of years) by the slope of the graph i.e. if the slope is positive, it means that the bullish ratio is rising and hence the company is doing well financially and if the slope is negative, we can infer that there are some financial markers which are not favourable.
