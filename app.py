import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import investpy as inv
import time
import matplotlib.pyplot as plt
import seaborn as sns
import cufflinks as cf
import datetime
from datetime import date

# Função de Análise de Carteira
def Carteira():
  st.title('Análise do Beta da Carteira')

  '**Ações**'
  papeis = st.multiselect('Selecione as Ações da Carteira', stocks_df)
  qtde_papeis = len(papeis)
 
  '**Quantidade**'
  lotes = st.text_input('Digite a quantidade de cada ativo, separando com "," (vírgula) e na mesma sequência (Ex.: 200,500,300 ...)')
  
  if st.button('Calcular'):
    lotes = lotes.split(',')
    qtde_lotes = len(lotes)
    if qtde_papeis == qtde_lotes:
      portfolio = pd.DataFrame()
      portfolio['Ação'] = papeis
      portfolio['Qtde'] = lotes
    else:
      st.write('Quantidade diferente de Papéis e de Lotes. Verifique a lista')

    # Ler os Tickers da lista e adicionar o '.SA' para usar com o YahooFinance e baixar o histórico

    tickers = papeis
    count = 0
    for item in tickers:
        item = item + '.SA'
        tickers[count] = item
        count += 1

    carteira = yf.download(tickers, start="2020-02-06", end="2021-02-12")["Adj Close"]
    bovespa = yf.download('^BVSP', start="2020-02-06", end="2021-02-12")["Adj Close"]
    carteira['BOVESPA'] = bovespa

    # Pegar a ultima cotação dos ativos
    count = 0
    portfolio['Fechamento'] = ''
    barra_progresso = st.progress(0)
    total_progress = len(portfolio['Ação'])
    for i in portfolio['Ação']:
      portfolio['Fechamento'][count] = inv.get_stock_information(i, country='brazil')['Prev. Close'][0]
      count += 1
      barra_progresso.progress(count/total_progress)

    #Calculo Covariancia e Variancia
    log_returns = np.log(carteira/carteira.shift(1))
    cov = log_returns.cov()*250             #covariância dos dados
    var_m = log_returns["BOVESPA"].var()*250  #variância do mercado
    portfolio['Qtde'] = pd.to_numeric(portfolio['Qtde'])
    portfolio['Valor'] = portfolio['Qtde'] * portfolio['Fechamento']
    portfolio['%'] = (portfolio['Valor'] / portfolio['Valor'].sum()) 
    cov = cov.drop(cov.tail(1).index)
    cov = cov.reset_index(drop=False)
    portfolio['Beta'] = cov['BOVESPA'] / var_m #Calculo do Beta
    portfolio['Beta Pond'] = portfolio['%']  * portfolio['Beta']
    portfolio['Fechamento'] = pd.to_numeric(portfolio['Fechamento'])
    portfolio['Valor'] = pd.to_numeric(portfolio['Valor'])
    portfolio['%'] = pd.to_numeric(portfolio['%'])
    portfolio['Beta Pond'] = pd.to_numeric(portfolio['Beta Pond'])
    beta_portfolio = portfolio['Beta Pond'].sum().round(2)

    portfolio = portfolio.style.format({"Fechamento": "R${:20,.2f}", "Valor": "R${:20,.2f}", "%": "{:.0%}", "Beta": "{:.2}", "Beta Pond": "{:.2}"})

    '**Portfolio**'
    st.table(portfolio)
    ''
    '**Beta da Carteira:**', beta_portfolio


# Função de Calculo de Correlação

def Correlacao():
  st.title('Correlação entre Ativos')

  stocks_list = inv.get_stocks_list(country='Brazil') #Pegar a lista das Ações Brasileiras
  indices = ['Indice Bovespa', 'Indice Dolar', 'Indice SP500', 'Indice Dow Jones', 'Indice NASDAQ']
  stocks_list.extend(indices)
  stocks_list.sort()

  selecao = st.multiselect('Selecione os Ativos. O 1º Ativo será a referência de comparação com os demais. Para Indices, apenas digitar "Indice..."', stocks_list)

  tickers = selecao[:]

  if st.button('Calcular'):
    with st.spinner('Baixando Histórico e Calculando...'):
      count = 0
      for item in tickers:
          if 'Indice' not in item: 
            item = item + '.SA'
          tickers[count] = item
          count += 1

      if 'Indice Bovespa' in tickers:
        tickers.remove('Indice Bovespa')
        tickers.append('^BVSP')
      if 'Indice Dolar' in tickers:
        tickers.remove('Indice Dolar')
        tickers.append('USDBRL=X')
      if 'Indice SP500' in tickers:
        tickers.remove('Indice SP500')
        tickers.append('^GSPC')
      if 'Indice Dow Jones' in tickers:
        tickers.remove('Indice Dow Jones')
        tickers.append('^DJI')
      if 'Indice NASDAQ' in tickers:
        tickers.remove('Indice NASDAQ')
        tickers.append('^IXIC')
      
      carteira = yf.download(tickers, start="2010-01-01")["Close"]
      carteira = carteira.dropna()

      retornos = carteira.pct_change()[1:]

      retornos.rename(columns = {'^BVSP': 'Indice Bovespa', 'USDBRL=X': 'Indice Dolar', '^GSPC': 'Indice SP500', '^DJI': 'Indice Dow Jones', '^IXIC': 'Indice NASDAQ'}, inplace = True)
      count = 0
      for item in retornos.columns:
        if 'Indice' not in item: 
          string_a = retornos.columns[count]
          string_b = string_a[:-3]
          retornos.columns = retornos.columns.str.replace(string_a, string_b)
        count += 1

      #count = 1
      #for i in range(len(tickers)-1):
      #  correlacao_tempo = retornos[selecao[count]].rolling(252).corr(retornos[selecao[0]])*100
      #  correlacao_tempo = correlacao_tempo.dropna()
      #  'Correlação entre ', selecao[0], ' e', selecao[count]
      #  st.line_chart(correlacao_tempo)
      #  count += 1

      count = 1
      for i in range(len(tickers)-1):
        correlacao_ativo = pd.DataFrame(retornos[selecao[count]].rolling(252).corr(retornos[selecao[0]])*100)
        correlacao_ativo.columns = [selecao[count]]
        if count == 1: correlacao_composicao = correlacao_ativo
        if count != 1: correlacao_composicao = pd.merge(correlacao_composicao, correlacao_ativo, how= 'inner', on = 'Date')
        count += 1
      correlacao_composicao = correlacao_composicao.dropna()
      #'Correlação entre **', selecao[0], '**e os demais ativos:'
      #st.line_chart(correlacao_composicao)
      fig = correlacao_composicao.iplot(asFigure=True, xTitle='Data', yTitle='Correlação', title='Correlação entre ' + selecao[0] + ' e os Ativos listados')
      st.plotly_chart(fig)

      'HeatMap da correlação entre os ativos nos últimos **12 meses**:'
      #plt.subplots(figsize=(18,10))
      sns.heatmap(retornos.tail(255).corr(), annot=True); # HeatMap da correlação entre os Ativos do periodo de 1 ano
      st.pyplot()

      #correlacao = retornos[ticker2].rolling(252).corr(retornos[ticker1])*100
      #correlacao = correlacao.dropna()
      #'Correlação entre', ticker1_sel, 'e ', ticker2_sel, 'ao longo do tempo'
      #st.line_chart(correlacao)
      #correlacao_ultimo_ano = correlacao.tail(1)[0].round(2)
      #'Correlação nos últimos 12 meses:', correlacao_ultimo_ano, '%'
    st.success('Pronto!')

# Função de Analise de Quedas e dia seguinte

def Quedas():
  st.title('Análise de quedas e comportamento no dia seguinte')
  
  ticker = st.selectbox('Escolha a Ação (Clique no campo e digite as iniciais do Ticker)', stocks_df)
  perc_queda = st.number_input('Entre com a % de queda (Ex.: 10 para listar os dias em que a Ação caiu mais do que 10%', min_value = 5, value = 10)
  pressed_calc = st.button('Listar')


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
    
    dados_df = dados_df.style.applymap(_color_red_or_green, subset=['% Queda', '% Abert. Seguinte', '% Fech. Seguinte', '% Var. no dia']).format(
        {"% Queda": "{:.2%}", "% Abert. Seguinte": "{:.2%}", "% Fech. Seguinte": "{:.2%}", "% Var. no dia": "{:.2%}"}) # Formatar o dataframe com as cores do mapa acima e com a formatação de %
    
    st.table(dados_df)

# Função de Analise da Distância do preço com as Médias

def Distancia_Medias():
  # Dados para análise
  st.title('Análise de Distância das Médias')
  ticker = st.selectbox('Escolha a Ação (Clique no campo e digite as iniciais do Ticker)', stocks_df)
  SMA= st.number_input('Selecione a média móvel desejada', min_value = 8, max_value = 200, value = 20)
  threshold= st.number_input('Selecione o Threshold', min_value = 1.0, max_value = 10.0, value = 3.0)
  periodo = st.slider('Selecione o período desejado em anos', min_value = 1, max_value = 20, value = 10)

  if st.button('Calcular'):

    data_atual_instancia = date.today()
    data_atual = date.today().strftime('%d/%m/%Y')
    data_delta = datetime.timedelta(weeks=periodo * 52)
    data_inicio = (data_atual_instancia - data_delta).strftime('%d/%m/%Y') # Pegar a data inicio
  
    papel_inv = inv.get_stock_historical_data(ticker, country='brazil',  from_date=data_inicio, to_date=data_atual)

    data = pd.DataFrame(papel_inv['Close'])
    data.rename(columns={'Close': 'price'}, inplace=True)
    data['returns'] = np.log(data['price'] / data['price'].shift(1))
    data['SMA'] = data['price'].rolling(SMA).mean()
    data['distance'] = data['price'] - data['SMA']
    df = data['distance'].dropna()

    fig = df.iplot(asFigure=True, xTitle='Data', yTitle='Preço', dimensions=(900, 600), title=ticker + ' - Distância em relação a SMA ' + str(SMA) + '- Threshold: ' + str(threshold), hline=[-threshold,0,threshold])
    st.plotly_chart(fig)


# Função de Analise de Retornos Mensais
def Retornos_mensais():
  st.title('Análise de Retornos Mensais')
  data_inicial = '01/01/1990'
  data_final = date.today().strftime('%d/%m/%Y')

  st.write('Escolha o País')
  pais = st.radio('', ('Brasil', 'Estados Unidos'))

  st.write('Escolha entre Ações ou Indices')
  opcao = st.radio('', ('Ações', 'Indices'))

  if pais == 'Brasil' and opcao == 'Ações':
    lista = inv.get_stocks_list(country='brazil')
  if pais == 'Brasil' and opcao == 'Indices':  
    lista = inv.get_indices_list(country='brazil')
  if pais == 'Estados Unidos' and opcao == 'Ações':
    lista = inv.get_stocks_list(country='united states')
  if pais == 'Estados Unidos' and opcao == 'Indices':
    lista = inv.get_indices_list(country='united states')

  ticker = st.selectbox('Selecione a Ação ou Indice desejado', lista)

  if st.button('Calcular'):

    #Dados do Investing
    if pais == 'Brasil' and opcao == 'Ações':
      papel = inv.get_stock_historical_data(ticker, country='brazil', from_date=data_inicial, to_date=data_final, interval='Monthly')['Close'].pct_change(1)
    if pais == 'Brasil' and opcao == 'Indices':
      papel = inv.get_index_historical_data(ticker, country='brazil', from_date=data_inicial, to_date=data_final, interval='Monthly')['Close'].pct_change(1)
    if pais == 'Estados Unidos' and opcao == 'Ações':
      papel = inv.get_stock_historical_data(ticker, country='united states', from_date=data_inicial, to_date=data_final, interval='Monthly')['Close'].pct_change(1)
    if pais == 'Estados Unidos' and opcao == 'Indices':
      papel = inv.get_index_historical_data(ticker, country='united states', from_date=data_inicial, to_date=data_final, interval='Monthly')['Close'].pct_change(1)

    #Separar e agrupar os anos e meses
    retorno_mensal = papel.groupby([papel.index.year.rename('Year'), papel.index.month.rename('Month')]).mean()
    #Criar e formatar a tabela pivot table
    tabela_retornos = pd.DataFrame(retorno_mensal)
    tabela_retornos = pd.pivot_table(tabela_retornos, values='Close', index='Year', columns='Month')
    tabela_retornos.columns = ['Jan', 'Fev', 'Mar','Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    #Função para colorir a tabela
    def _color_red_or_green(val): # Função para o mapa de cores da tabela
      color = 'red' if val < 0 else 'green'
      #return 'color: %s' % color
      return 'background-color: %s' % color
    #Aplicar a formatação
    tabela_retornos = tabela_retornos.style.applymap(_color_red_or_green).format("{:.2%}")
    st.table(tabela_retornos)


######### Inicio do Código ##########

st.set_option('deprecation.showPyplotGlobalUse', False) # Desabilitar os Warnigs sobre o Pyplot
st.set_page_config(page_title='Análise Quant Ações', layout = 'wide', initial_sidebar_state = 'auto') # Configurar Pagina

st.sidebar.image('EQ.png', caption='', width=200, use_column_width=False)
st.sidebar.header('App para análise de Ações')
st.sidebar.subheader('Escolha a opção para análise:')

opcao = st.sidebar.radio("", ('Correlação entre Ativos', 'Análise do Beta da Carteira', 'Análise de Quedas / Dia Seguinte', 'Análise de Distância das Médias', 'Análise de Retornos Mensais'))


stocks_list = inv.get_stocks_list(country='Brazil') #Pegar a lista das Ações Brasileiras
stocks_df = pd.DataFrame(stocks_list) #Transforma a lista em DataFrame
stocks_df.columns = ['Ticker'] #Adiciona o nome da coluna
indices = [{'Ticker': 'Indice Bovespa'}, {'Ticker': 'Indice Dolar'},{'Ticker': 'Indice SP500'}, {'Ticker': 'Indice Dow Jones'}, {'Ticker': 'Indice NASDAQ'}]
stocks_df = stocks_df.append(indices, ignore_index=True)
stocks_df = stocks_df.sort_values(by='Ticker').reset_index(drop=True) #Ordena por ordem alfabetica e reseta o index

if opcao == 'Análise do Beta da Carteira':
  Carteira()

if opcao == 'Análise de Quedas / Dia Seguinte':
  Quedas()
  
if opcao == 'Correlação entre Ativos':  
  Correlacao()

if opcao == 'Análise de Distância das Médias':  
  Distancia_Medias()

if opcao == 'Análise de Retornos Mensais': 
  Retornos_mensais()


st.sidebar.text('Criado por Roberto Martins')
st.sidebar.text('rraires.dev@gmail.com')
