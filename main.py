import datetime as dt

import pandas as pd
import plotly.graph_objs as go
import requests
import streamlit as st

st.set_page_config(page_title='Covid Basel', page_icon='🦠', layout='wide')


@st.cache(ttl=3600,show_spinner=False)
def get_data():
    req = requests.get(
        'https://data.bs.ch/api/records/1.0/search/?dataset=100073&q=&rows=800&sort=timestamp&facet=timestamp')
    js = req.json()['records']
    dico = [i['fields'] for i in js]
    data = pd.DataFrame(dico)
    data = data.set_index('date', drop=False)
    data = data[['week', 'current_quarantined', 'ndiff_conf', "ncumul_conf",'current_isolated', 'ndiff_released', 'ndiff_deceased',
                 'current_icu', 'current_hosp']]
    data.rename({'ndiff_conf': 'cases',"ncumul_conf":'total_cases', 'ndiff_released': 'released', 'ndiff_deceased': 'deceased'}, axis=1,
                inplace=True)
    data.sort_index(inplace=True)
    return data


# sidebar
if st.sidebar.button('clear cache'):
    st.caching.clear_cache()
st.sidebar.header('Time smoothing')
n_average = st.sidebar.slider("on how many days would you like to smooth your average data", min_value=1, max_value=21, step=1, value=7)
n_incidence = st.sidebar.slider("On how many days would you like to smooth your incidence data ", min_value=1, max_value=21, step=1, value=14)
pop = 201469

df_base = get_data()


@st.cache(ttl=3600, show_spinner=False)
def calc_df(data, n_average=7, n_incidence=14):
    df2 = data.copy()
    df2['average_n'] = df2['cases'].rolling(n_average).mean()
    df2['incidence_n'] = df2['cases'].rolling(n_incidence).sum() / pop * 100000
    return df2


df = calc_df(df_base, n_average=n_average,n_incidence=n_incidence)

today = df.index.max()
yesterday = (dt.datetime.strptime(today, "%Y-%m-%d") - dt.timedelta(days=1)).strftime("%Y-%m-%d")
last_update = dt.datetime.strptime(df.index.max(), '%Y-%m-%d').strftime('%d %b %Y')
st.markdown(f'''
# Covid19 cases in basel stadt 

This dashboard show the evolution of covid in the canton of basel stadt

last data updated on the **{last_update}**

## indicators 
''')
fig_ind_abs = go.Figure(go.Indicator(
    mode="number+delta",
    value=df.loc[today]["cases"],
    delta={'position': "top", 'reference': df.loc[yesterday]['cases']}))
fig_ind_abs.update_layout(title="today's cases")

fig_ind_avg = go.Figure(go.Indicator(
    mode="number+delta",
    value=df.loc[today]['average_n'],
    delta={'position': "top", 'reference': df.loc[yesterday]['average_n']}))
fig_ind_avg.update_layout(title=f'{n_average} days avg')

fig_ind_inc = go.Figure(go.Indicator(
    mode="number+delta",
    value=df.loc[today]['incidence_n'],
    delta={'position': "top", 'reference': df.loc[yesterday]['incidence_n']}))
fig_ind_inc.update_layout(title=f'{n_incidence} days incidence')

fig_ind_cumul = go.Figure(go.Indicator(
    mode="number",
    value=df.loc[today]['total_cases']))
fig_ind_cumul.update_layout(title='Total cases')

fig_ind_cumul_pop = go.Figure(go.Indicator(
    mode="number",
    value=df.loc[today]['total_cases']/pop*100000))
fig_ind_cumul_pop.update_layout(title="Total cases per 100'000 inhabitants")

col1, col2, col3 = st.beta_columns(3)
col1.plotly_chart(fig_ind_abs, use_container_width=True)
col2.plotly_chart(fig_ind_avg, use_container_width=True)
col3.plotly_chart(fig_ind_inc, use_container_width=True)

st.markdown('### Since the beginning of the pandemics')
col1, col2 = st.beta_columns(2)
col1.plotly_chart(fig_ind_cumul,use_container_width=True)
col2.plotly_chart(fig_ind_cumul_pop,use_container_width=True)

st.header('Evolution')

view = st.radio('Do you want to see average cases or incidence', ['Average', 'Incidence','Cumulative'])


if view == 'Average':
    fig_cases = go.Figure()
    fig_cases.add_trace(go.Scatter(x=df.index, y=df.cases,
                                   mode='lines+markers',
                                   name='Cases',
                                   opacity=0.2,
                                   marker={'size': 3.5}))
    fig_cases.add_trace(
        go.Scatter(x=df.sort_index().index, y=df['average_n'],
                   mode='lines+markers',
                   name=f'{n_average} days average',
                   line={
                       'width': 2},
                   marker={'size': 3.5}))
    fig_cases.update_layout(title='Covid19 cases in BS ',
                            xaxis_title='Date',
                            yaxis_title='# cases', plot_bgcolor='rgba(0,0,0,0)', yaxis_gridcolor='rgba(0,0,0,0.05)')
    fig_cases.update_layout(hovermode="x unified")

    st.plotly_chart(fig_cases, use_container_width=True)

elif view == 'Incidence':
    fig_inc = go.Figure()
    fig_inc.add_trace(go.Scatter(x=df.sort_index().index, y=df['incidence_n'],
                                 mode='lines+markers',
                                 name=f'{n_incidence} days incidence (per 100000)',
                                 line={
                                     'width': 2},
                                 marker={'size': 3.5}))
    fig_inc.update_layout(title=f'Covid19 {n_incidence} days incidence in BS ',
                          xaxis_title='Date',
                          yaxis_title='# cases', plot_bgcolor='rgba(0,0,0,0)', yaxis_gridcolor='rgba(0,0,0,0.05)')
    fig_inc.update_layout(hovermode="x unified")
    st.plotly_chart(fig_inc, use_container_width=True)

elif view == 'Cumulative':
    fig_cumul =go.Figure()
    fig_cumul.add_trace(go.Scatter(x=df.index, y=df['total_cases'],
                                 mode='lines+markers',
                                 name='Cumulative Cases',
                                 marker={'size': 3.5}))
    fig_cumul.update_layout(title=f'Covid19 cumulative cases in BS ',
                          xaxis_title='Date',
                          yaxis_title='# cases', plot_bgcolor='rgba(0,0,0,0)', yaxis_gridcolor='rgba(0,0,0,0.05)')
    fig_cumul.update_layout(hovermode="x unified")
    st.plotly_chart(fig_cumul, use_container_width=True)
if st.checkbox("view Data", value=False):
    st.write(df.sort_index(ascending=False))
