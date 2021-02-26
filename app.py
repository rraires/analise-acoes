import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import investpy as inv

st.beta_set_page_config(page_title='Análise Quant Ações', page_icon = favicon, layout = 'wide', initial_sidebar_state = 'auto')
stocks_list = inv.get_stocks_list(country='Brazil') #Pegar a lista das Ações Brasileiras
stocks_df = pd.DataFrame(stocks_list) #Transforma a lista em DataFrame
stocks_df.columns = ['Ticker'] #Adiciona o nome da coluna
stocks_df = stocks_df.sort_values(by='Ticker').reset_index(drop=True) #Ordena por ordem alfabetica e reseta o index

'''
# Análise de quedas

Análise do comportamento no dia seguinte à grandes quedas
'''

option = st.sidebar.selectbox('Escolha a Ação (Clique no campo e digite as iniciais do Ticker)', stocks_df)
perc_queda = st.sidebar.number_input('Entre com a % de queda (Ex.: 10 para listar os dias em que a Ação caiu mais do que 10%',5)
pressed_calc = st.sidebar.button('Listar')


if pressed_calc:
  'Dias onde', option, ' teve uma queda de mais de', -perc_queda, '%'
  papel = yf.download(option + '.SA')
  papel = papel.reset_index()
  papel['Retorno'] = papel['Adj Close'].pct_change()
  papel = papel[:-1]

  perc = -(perc_queda/100)

  indice = papel[papel["Retorno"] < perc].index

  dia_queda = papel.iloc[indice]
  dia_queda['Retorno'] = (dia_queda['Retorno'])
  dia_seguinte = papel.iloc[indice+1]
  dia_seguinte['Retorno'] = (dia_seguinte['Retorno'])

  dados_df = pd.DataFrame()
  dados_df['Data Queda'] = dia_queda['Date'].values
  dados_df['Data Queda'] = dados_df['Data Queda'].dt.strftime('%d-%m-%Y')
  dados_df['% Queda'] = dia_queda['Retorno'].values.round(2)
  #dados_df['Dia Seguinte'] = dia_seguinte['Date'].values
  dados_df['% Abert. Seguinte'] = (((dia_seguinte['Open'].values - dia_queda['Close'].values) / dia_queda['Close'].values)).round(2)
  dados_df['% Fech. Seguinte'] = dia_seguinte['Retorno'].values.round(2)
  dados_df['% Var. no dia'] = (((dia_seguinte['Close'] - dia_seguinte['Open']) / dia_seguinte['Open'])).values.round(2)

  def _color_red_or_green(val):
    color = 'red' if val < 0 else 'green'
    return 'color: %s' % color
    #return 'background-color: %s' % color

  
  #dados_df = dados_df.style.format({"% Queda": "{:.2%}", "% Abert. Seguinte": "{:.2%}", "% Fech. Seguinte": "{:.2%}", "% Var. no dia": "{:.2%}"})
  dados_df = dados_df.style.applymap(_color_red_or_green, subset=['% Queda', '% Abert. Seguinte', '% Fech. Seguinte', '% Var. no dia']).format(
      {"% Queda": "{:.2%}", "% Abert. Seguinte": "{:.2%}", "% Fech. Seguinte": "{:.2%}", "% Var. no dia": "{:.2%}"})
  
  st.table(dados_df)

  #st.table(dados_df.style.format({"% Queda": "{:.2%}", "% Abert. Seguinte": "{:.2%}", "% Fech. Seguinte": "{:.2%}", "% Var. no dia": "{:.2%}"}))
  #st.write(dados_df.style.format({"% Queda": "{:.2%}", "% Abert. Seguinte": "{:.2%}", "% Fech. Seguinte": "{:.2%}", "% Var. no dia": "{:.2%}"}))
