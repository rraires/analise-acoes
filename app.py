import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import investpy as inv

st.set_page_config(page_title='Análise Quant Ações', layout = 'wide', initial_sidebar_state = 'auto') # Configurar Pagina
stocks_list = inv.get_stocks_list(country='Brazil') #Pegar a lista das Ações Brasileiras
stocks_df = pd.DataFrame(stocks_list) #Transforma a lista em DataFrame
stocks_df.columns = ['Ticker'] #Adiciona o nome da coluna
stocks_df = stocks_df.sort_values(by='Ticker').reset_index(drop=True) #Ordena por ordem alfabetica e reseta o index

'''
# Análise de quedas

Análise do comportamento no dia seguinte à grandes quedas
'''

ticker = st.sidebar.selectbox('Escolha a Ação (Clique no campo e digite as iniciais do Ticker)', stocks_df)
perc_queda = st.sidebar.number_input('Entre com a % de queda (Ex.: 10 para listar os dias em que a Ação caiu mais do que 10%',5)
pressed_calc = st.sidebar.button('Listar')


if pressed_calc:
  'Dias onde', ticker, ' teve uma queda de mais de', -perc_queda, '%'
  papel = yf.download(ticker + '.SA') # Baixar dados históricos do ticker
  papel = papel.reset_index() # Resetar o index, que antes estava como Date, e agora Index
  papel['Retorno'] = papel['Adj Close'].pct_change() # Calcular a variação % entre um dia e outro do fechamento e criar a coluna Retorno
  papel = papel[:-1] # Retirar a ultima linha (dia atual) caso ele tenha queda maior que o escolhido, para nao dar erro no dia seguinte q não existe

  perc = -(perc_queda/100) # Dividir o valor de perc por 100 para a busca

  indice = papel[papel["Retorno"] < perc].index # Procurar pelas linhas onde o Retorno for menor que perc, e gerar a lista com os indices

  dia_queda = papel.iloc[indice] # Criar a tabela com os dias de queda escolhido
  dia_seguinte = papel.iloc[indice+1] # Criar a tablea com os dias seguintes

  dados_df = pd.DataFrame() # Criar o dataframe dos dados a serem apresentados
  dados_df['Data Queda'] = dia_queda['Date'].values # Coluna das Datas de Queda
  dados_df['Data Queda'] = dados_df['Data Queda'].dt.strftime('%d-%m-%Y') # Formatar as coluna de datas commo string. Para apresentar no Streamlit
  dados_df['% Queda'] = dia_queda['Retorno'].values.round(2) # Coluna com a % de queda
  dados_df['% Abert. Seguinte'] = (((dia_seguinte['Open'].values - dia_queda['Close'].values) / dia_queda['Close'].values)).round(2) # Coluna com a % da Abertura do dia seguinte
  dados_df['% Fech. Seguinte'] = dia_seguinte['Retorno'].values.round(2) # Coluna com a % do Fechamento do dia seguinte
  dados_df['% Var. no dia'] = (((dia_seguinte['Close'] - dia_seguinte['Open']) / dia_seguinte['Open'])).values.round(2) # Coluna com a % Variação do dia seguinte

  def _color_red_or_green(val): # Função para o mapa de cores da tabela
    color = 'red' if val < 0 else 'green'
    return 'color: %s' % color
    #return 'background-color: %s' % color

  
  #dados_df = dados_df.style.format({"% Queda": "{:.2%}", "% Abert. Seguinte": "{:.2%}", "% Fech. Seguinte": "{:.2%}", "% Var. no dia": "{:.2%}"})
  dados_df = dados_df.style.applymap(_color_red_or_green, subset=['% Queda', '% Abert. Seguinte', '% Fech. Seguinte', '% Var. no dia']).format(
      {"% Queda": "{:.2%}", "% Abert. Seguinte": "{:.2%}", "% Fech. Seguinte": "{:.2%}", "% Var. no dia": "{:.2%}"}) # Formatar o dataframe com as cores do mapa acima e com a formatação de %
  
  st.table(dados_df)

  #st.table(dados_df.style.format({"% Queda": "{:.2%}", "% Abert. Seguinte": "{:.2%}", "% Fech. Seguinte": "{:.2%}", "% Var. no dia": "{:.2%}"}))
  #st.write(dados_df.style.format({"% Queda": "{:.2%}", "% Abert. Seguinte": "{:.2%}", "% Fech. Seguinte": "{:.2%}", "% Var. no dia": "{:.2%}"}))
