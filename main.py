import datetime as dt

import pandas as pd
import plotly.graph_objs as go
import requests
import streamlit as st


@st.cache(ttl=3600)
def get_data():
    req = requests.get(
        'https://data.bs.ch/api/records/1.0/search/?dataset=100073&q=&rows=800&sort=timestamp&facet=timestamp')
    js = req.json()['records']
    dico = [i['fields'] for i in js]
    data = pd.DataFrame(dico)
    data = data.set_index('date', drop=False)
    data = data[['week', 'current_quarantined', 'ndiff_conf', 'current_isolated', 'ndiff_released', 'ndiff_deceased',
                 'current_icu', 'current_hosp']]
    data.rename({'ndiff_conf': 'cases', 'ndiff_released': 'released', 'ndiff_deceased': 'deceased'}, axis=1,
                inplace=True)
    data.sort_index(inplace=True)
    data['average_7'] = data['cases'].rolling(7).mean()
    data['incidence_14'] = data['cases'].rolling(14).sum() / pop * 100000
    return data


# sidebar
if st.sidebar.button('clear cache'):
    st.caching.clear_cache()
st.sidebar.header('Time smoothing')
n = st.sidebar.slider("on how many days would you like to smooth your data", min_value=1, max_value=21, step=1, value=7)
pop = 201469

df_base = get_data()


@st.cache(ttl=3600)
def calc_df(data, n=14):
    df2 = data.copy()
    df2['average_n'] = df2['cases'].rolling(n).mean()
    df2['incidence_n'] = df2['cases'].rolling(n).sum() / pop * 100000
    return df2


df = calc_df(df_base, n=n)

today = df.index.max()
yesterday = (dt.datetime.strptime(today, "%Y-%m-%d") - dt.timedelta(days=1)).strftime("%Y-%m-%d")

last_update = dt.datetime.strptime(df.index.max(), '%Y-%m-%d').strftime('%d %b %Y')

st.markdown(f'''
# Covid19 cases in basel stadt 

This dashboard show the evolution of covid in the canton of basel stadt

last data updated on the {last_update}

## indicators 
Those indicators will not be affected by the filters
''')
fig_ind_abs = go.Figure(go.Indicator(
    mode="number+delta",
    value=df.loc[today]["cases"],
    delta={'position': "top", 'reference': df.loc[yesterday]['cases']}))
fig_ind_abs.update_layout(title="today's cases")

fig_ind_avg = go.Figure(go.Indicator(
    mode="number+delta",
    value=df.loc[today]['average_7'],
    delta={'position': "top", 'reference': df.loc[yesterday]['average_7']}))
fig_ind_avg.update_layout(title='7 days avg')

fig_ind_inc = go.Figure(go.Indicator(
    mode="number+delta",
    value=df.loc[today]['incidence_14'],
    delta={'position': "top", 'reference': df.loc[yesterday]['incidence_14']}))
fig_ind_inc.update_layout(title='14 days incidence')

col1, col2, col3 = st.beta_columns(3)
col1.plotly_chart(fig_ind_abs, use_container_width=True)
col2.plotly_chart(fig_ind_avg, use_container_width=True)
col3.plotly_chart(fig_ind_inc, use_container_width=True)

fig_cases = go.Figure()
fig_cases.add_trace(go.Scatter(x=df.index, y=df.cases,
                               mode='lines+markers',
                               name='Cases',
                               opacity=0.2,
                               marker={'size': 3.5}))
fig_cases.add_trace(
    go.Scatter(x=df.sort_index().index, y=df['average_n'],
               mode='lines+markers',
               name=f'{n} days average',
               line={
                   'width': 2},
               marker={'size': 3.5}))
fig_cases.update_layout(title='Covid19 cases in BS ',
                        xaxis_title='Date',
                        yaxis_title='# cases', plot_bgcolor='rgba(0,0,0,0)', yaxis_gridcolor='rgba(0,0,0,0.05)')
fig_cases.update_layout(hovermode="x unified")
st.header('Evolution')
st.plotly_chart(fig_cases, use_container_width=True)

fig_inc = go.Figure()
fig_inc.add_trace(go.Scatter(x=df.index, y=df.cases,
                             mode='lines+markers',
                             name='Cases',
                             opacity=0.2,
                             marker={'size':3.5}))
fig_inc.add_trace(go.Scatter(x=df.sort_index().index, y=df['incidence_n'],
                             mode='lines+markers',
                             name=f'{n} days incidence (per 100000)',
                             line={
                        'width':2},
                             marker={'size':3.5}))
fig_inc.update_layout(title=f'Covid19 {n} days incidence in BS ',
                      xaxis_title='Date',
                      yaxis_title='# cases', plot_bgcolor='rgba(0,0,0,0)', yaxis_gridcolor='rgba(0,0,0,0.05)')
fig_inc.update_layout(hovermode="x unified")
st.write(fig_inc)
