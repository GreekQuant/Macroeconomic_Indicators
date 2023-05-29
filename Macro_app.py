import io
import copy
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from openbb_terminal.sdk import openbb

# openbb.economy.country_codes()
# openbb.economy.macro_countries()
# openbb.economy.macro_parameters()
# openbb.economy.available_indices()
# openbb.economy.events(countries=['Greece'])
# data,units,denomination = openbb.economy.macro(parameters = ['POP'], countries = ['United States', 'Greece', 'France', 'Italy', 'Spain', 'Germany'])
# data.tail(10)

@st.cache_data(show_spinner=False)
def CreateIndicatorsLandingDataFrame():
    parameters_df = pd.DataFrame.from_dict(openbb.economy.macro_parameters()).transpose()
    parameters_df = parameters_df.rename(columns={'name':'Indicator', 'period':'Frequency', 'description':'Description'}).copy()
    return parameters_df

@st.cache_data(show_spinner=False)
def formatMillion(x):
    return "{:.2f}M".format(x/1000000)

@st.cache_data(show_spinner=False)
def formatBillion(x):
    return "{:.2f}B".format(x/1000000000)

@st.cache_data(show_spinner=False)
def formatThousands(x):
    return "{:.2f}K".format(x/1000)

@st.cache_data(show_spinner=False)
def Fetch_Indicators_Data(*args):
    st.session_state.indicators_ = list(args)
    st.session_state.fetch_plot_indicators_btn = True
    st.session_state.time_series_gather=[]
    st.session_state.units_gather = []
    st.session_state.denomination_gather = []
    gather_only_those_with_data = []
    for i, elem in enumerate(st.session_state.indicators_):
        try:
            temp_series = openbb.economy.macro(parameters = [f'{elem}'], countries = ['Greece',], symbol='EUR')[0].droplevel(0, axis='columns')
            st.session_state.units_gather.append(openbb.economy.macro(parameters = [f'{elem}'], countries = ['Greece',])[1]['Greece'][f'{elem}'])
            st.session_state.denomination_gather.append(openbb.economy.macro(parameters = [f'{elem}'], countries = ['Greece',])[2])
            st.session_state.time_series_gather.append(temp_series)
            temp_series=None
            gather_only_those_with_data.append(elem)
        except (IndexError, KeyError) as error_:
            print(f"Data are not available for {elem} it will bee removed from the indicators_ list")
            continue
    st.session_state.indicators_ = copy.deepcopy(gather_only_those_with_data)


@st.cache_data(show_spinner=False)
def CreateGraphsAndMetrics(chosen_indicators:list, parameters_df):
    for i, elem in enumerate(chosen_indicators):
        try:
            col1, col2,= st.columns(2, gap='large')
            print(f"{i} : {st.session_state.time_series_gather[i].columns[0]} : {parameters_df.loc[elem,'Indicator']} [{st.session_state.units_gather[i]}, {st.session_state.denomination_gather[i]}]")
            df = st.session_state.time_series_gather[i].copy()
            fig = px.line(df, x=st.session_state.time_series_gather[i].index, y=st.session_state.time_series_gather[i].columns[0], title=f'{parameters_df.loc[elem,"Indicator"]} - {parameters_df.loc[elem,"Frequency"]} ({st.session_state.units_gather[i]})')
            fig.layout.update(showlegend=True, 
                                template="simple_white", 
                                title_x=0.35, 
                                plot_bgcolor='white',
                                width=800, 
                                height=650
                                )
            fig.update_traces(line=dict(color='#00796b'),)
            fig.update_xaxes(title='Date')
            fig.update_yaxes(title=f'{elem} {st.session_state.denomination_gather[i]}')
            with col1:
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                coll1, coll2 = st.columns(2, gap='medium')
                with coll1:
                    st.markdown("##")
                    st.markdown("##")
                    st.markdown("##")
                    st.session_state.time_series_gather[i].index.name='Date'
                    fmt = {f'{elem}':'{:.2f}', "Date": lambda t: t.strftime("%d-%m-%Y")}
                    styler = st.session_state.time_series_gather[i].reset_index().round(2).style.format(fmt)
                    st.dataframe(styler)
                    if st.session_state.denomination_gather[i]=='':
                        # print(st.session_state.time_series_gather[i].iloc[-1])
                        coll2.metric(f'Last Value', str(np.round(st.session_state.time_series_gather[i].iloc[-1].values[0],2)), f"{str(np.round(st.session_state.time_series_gather[i].pct_change().iloc[-1].values[0]*100,2))}% - {parameters_df.loc[elem,'Frequency']}")
                    elif st.session_state.denomination_gather[i] == ' [in Millions]':
                        # print(st.session_state.denomination_gather[i])
                        coll2.metric(f'Last Value', str(st.session_state.time_series_gather[i][elem].apply(formatMillion).iloc[-1]), f"{str(np.round(st.session_state.time_series_gather[i].pct_change().iloc[-1].values[0]*100,2))}% - {parameters_df.loc[elem,'Frequency']}")
                    elif st.session_state.denomination_gather[i] == ' [in Thousands]':
                        # print(st.session_state.denomination_gather[i])
                        coll2.metric(f'Last Value', str(st.session_state.time_series_gather[i][elem].apply(formatThousands).iloc[-1]), f"{str(np.round(st.session_state.time_series_gather[i].pct_change().iloc[-1].values[0]*100,2))}% - {parameters_df.loc[elem,'Frequency']}")
                    elif st.session_state.denomination_gather[i] == ' [in Billions]':
                        # print(st.session_state.denomination_gather[i])
                        coll2.metric(f'Last Value', str(st.session_state.time_series_gather[i][elem].apply(formatBillion).iloc[-1]), f"{str(np.round(st.session_state.time_series_gather[i].pct_change().iloc[-1].values[0]*100,2))}% - {parameters_df.loc[elem,'Frequency']}")
            # print(st.session_state.time_series_gather[i])
            st.divider()
        except IndexError:
            pass


    st.session_state.time_series_gather_for_dl = copy.deepcopy(st.session_state.time_series_gather)
    for i, elem in enumerate(chosen_indicators):
        
        st.session_state.time_series_gather_for_dl[i][f'{elem}_diff'] = st.session_state.time_series_gather_for_dl[i][f'{elem}'].diff()
        st.session_state.time_series_gather_for_dl[i][f'{elem}_pct_change'] = st.session_state.time_series_gather_for_dl[i][f'{elem}'].pct_change()

@st.cache_data(experimental_allow_widgets=True)
def TriggerDownloadButton(chosen_indicators):
    st.markdown("##")

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer) as writer:
        for i, elem in enumerate(chosen_indicators):
            st.session_state.time_series_gather_for_dl[i].to_excel(writer, sheet_name=f"{elem}")
        writer.save()    

    st.download_button(
        label="Download Excel File",
        data=buffer,
        file_name='Macroeconomic_Data_Greece.xlsx',
        mime="application/vnd.ms-excel",
    )


if "fetch_plot_indicators_btn" not in st.session_state:
    st.session_state.fetch_plot_indicators_btn = False

if "indicators_" not in st.session_state:
    st.session_state.indicators_ = None
    
if "units_gather" not in st.session_state:
    st.session_state.units_gather = None
    
if "denomination_gather" not in st.session_state:
    st.session_state.denomination_gather = None
    
if "time_series_gather" not in st.session_state:
    st.session_state.time_series_gather = None
    
if "time_series_gather_for_dl" not in st.session_state:
    st.session_state.time_series_gather_for_dl = None


st.set_page_config(page_title="Financial Risk Measurement Team",
                   page_icon = "favicon.png",
                   layout="wide",)

st.image("deloitte.svg")
st.title("Macroeconomic Data for Greece")

with open("style.css") as css:
    st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)
    
st.subheader("Available Indicators (Source: https://www.econdb.com/ and https://ec.europa.eu/eurostat)")
st.markdown("#")
the_parameters_ = CreateIndicatorsLandingDataFrame()
st.dataframe(the_parameters_, use_container_width=True)

st.markdown("#")
indicators = list(the_parameters_.index.unique()).append('All')
indicators_to_plot_ = st.multiselect("Select the indicatos to plot", list(the_parameters_.index.unique()), help='Please select the indicators you want to plot - you can select as many as you want or "All" to plot all the indicators')

st.markdown("#")
fetch_indicator_data = st.button("Source and Plot Data", on_click=Fetch_Indicators_Data, args=list(indicators_to_plot_))

if fetch_indicator_data or st.session_state.fetch_plot_indicators_btn:
    with st.spinner('Data and graphs loading...'):
        CreateGraphsAndMetrics(st.session_state.indicators_, the_parameters_)
    TriggerDownloadButton(st.session_state.indicators_)
    
