import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import os
from datetime import datetime


# Definição das cores do tema
# Cores harmoniosas para os gráficos
color_1 = '#66C5CC'  # Azul-Verde Água
color_2 = '#F6CF71'  # Amarelo Claro
color_3 = '#F89C74'  # Coral
color_4 = '#DCB0F2'  # Lavanda
color_5 = '#87C55F'  # Verde Oliva
color_6 = '#9EB9F3'  # Azul Claro

fonte = "../data/sp24/raw/Anúncios-API.xlsx"

# Função para carregar os dados
@st.cache_data
def load_data():
    # O caminho para o arquivo Excel deve ser correto e relativo ao local onde o script é executado
    data = pd.read_excel(fonte)
    # Convertendo a coluna 'Dia' para datetime para facilitar a filtragem
    data['Dia'] = pd.to_datetime(data['Dia'])
   # Calcula as métricas de desempenho
    data['CTR'] = data['Cliques no link'] / data['Impressões']
    data['Connect Rate'] = data['Visualizações da página de destino'] / data['Cliques no link']
    data['Taxa de Conversão da Página'] = data['Finalizações de compra iniciadas'] / data['Visualizações da página de destino']
    data['Taxa de Conversão de Checkout'] = data['Compras'] / data['Finalizações de compra iniciadas']
    return data

# Definir o layout da página para 'wide'
st.set_page_config(layout="wide")

# Funções para calcular os KPIs
data = load_data()

# Título do Dashboard
st.title("Dashboard - ENCONTRO NACIONAL 2024")



# Obter as datas mínima e máxima do DataFrame
min_date, max_date = data['Dia'].min(), data['Dia'].max()

# Filtros de data limitados ao intervalo disponível
start_date = st.sidebar.date_input("Data de início", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("Data de término", value=max_date, min_value=min_date, max_value=max_date)

# Convertendo objetos date para datetime
start_datetime = pd.to_datetime(start_date)
end_datetime = pd.to_datetime(end_date)

# Filtrando os dadosgit
filtered_data = data[(data['Dia'] >= start_datetime) & (data['Dia'] <= end_datetime)]


#ÚLTIMA MODIFICAÇÃO EM:
# Substitua 'df_path' pelo caminho até o seu arquivo de dados
df_path = fonte

# Obter a última data de modificação do arquivo
last_mod_time = os.path.getmtime(df_path)

# Convertendo timestamp para formato legível
last_mod_date = datetime.fromtimestamp(last_mod_time).strftime('%Y-%m-%d %H:%M:%S')

# Exibindo na sidebar do Streamlit
st.sidebar.markdown(
    f"<span style='font-size: 12px; opacity: 0.7;'>Data da última atualização: {last_mod_date}</span>",
 
    unsafe_allow_html=True
)




# Função para formatar os valores monetários e de quantidade
def format_currency(value, currency=True):
    if currency:  # Se o valor for monetário
        if value >= 1000:
            return f"{value/1000:.1f}k"
        else:
            return f"${value:.0f}"
    else:  # Se o valor for uma quantidade (sem "R$")
        if value >= 1000:
            return f"{value/1000:.1f}k"
        else:
            return f"{value:.0f}"

# Função para criar gráficos de KPIs diários com rótulos de dados formatados
def create_kpi_charts(data):
    fig = px.line(data, x='Dia', y=['Compras', 'Custo por compra', 'Valor usado (BRL)'],
                  title='Investimento e CAC ao longo dos dias',color_discrete_map={
                      'Compras': color_1,
                      'Custo por compra': color_2,
                      'Valor usado (BRL)': color_3
                    
                  })
    
    # Adiciona rótulos de texto formatados para cada ponto no gráfico
    for col, color in zip(['Compras', 'Custo por compra', 'Valor usado (BRL)'], [color_1, color_2, color_3
]):
        fig.add_trace(go.Scatter(
            x=data['Dia'],
            y=data[col],
            mode='markers+text',
            text=[format_currency(val, col != 'Compras') for val in data[col]],
            textposition='top center',
            textfont=dict(color=color),
            showlegend=False,
            marker=dict(color=color),
            line=dict(color=color),
        ))
    
    # Atualiza a formatação dos eixos e da legenda
    fig.update_layout(
        yaxis_tickformat=',.0f',  # Sem vírgulas para os valores e sem casas decimais
        xaxis_tickformat='%d %b %Y',  # Formata a data como 'Dia Mês Ano'
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="right",
            x=1
        )
    )
    
    return fig



# Função para criar gráfico de funil
def create_funnel_chart(data):
    stages = ['Impressões', 'Cliques no link', 'Visualizações da página de destino', 'Finalizações de compra iniciadas', 'Compras']
    values = [data[col].sum() for col in stages]

    funnel_data = pd.DataFrame({'Estágio': stages, 'Quantidade': values})
    fig = px.funnel(funnel_data, x='Quantidade', y='Estágio', title='Funil de Marketing')
    
    # Aplica uma única cor do tema a todas as barras do funil
    fig.update_traces(marker=dict(color=color_1))

    fig.update_traces(textfont=dict(size=16))

    fig.update_layout(xaxis_range=[-8000, 8000])

    # Altera o formato dos números no eixo x para evitar a notação científica
    fig.update_layout(xaxis_tickformat='.')  # Use vírgula como separador de milhar

    fig.update_layout(height=700)
    return fig


# Função para criar gráfico de CTR
def create_performance_ctr_chart(filtered_data):
    if 'Dia' in filtered_data.columns:
        metrics_data = filtered_data[['Dia', 'CTR']].melt('Dia', var_name='Métricas', value_name='Valor')
        fig = px.line(metrics_data, x='Dia', y='Valor', color='Métricas', title='CTR ao Longo do Tempo', color_discrete_map={
                          'CTR': color_1
                      })
         # Atualiza o layout para mover a legenda para baixo
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=250)
        return fig
    else:
        raise KeyError("Coluna 'Dia' não encontrada no DataFrame.")


# Função para criar gráfico de linhas das métricas de desempenho
def create_performance_metrics_chart(data):
    metrics_data = data[['Dia', 'Connect Rate', 'Taxa de Conversão da Página', 'Taxa de Conversão de Checkout']].melt('Dia', var_name='Métricas', value_name='Valor')
    fig = px.line(metrics_data, x='Dia', y='Valor', color='Métricas', title='Métricas de Desempenho ao Longo do Tempo', color_discrete_map={
                      'Connect Rate': color_1,
                      'Taxa de Conversão da Página': color_2,
                      'Taxa de Conversão de Checkout': color_3
                  })
     # Atualiza o layout para mover a legenda para baixo
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
        height=400)
    return fig




# Calcula as métricas
soma_valor_gasto = filtered_data['Valor usado (BRL)'].sum()
soma_compras = int(filtered_data['Compras'].sum())
media_cac = (soma_valor_gasto / soma_compras) if soma_compras > 0 else 0
soma_faturamento = filtered_data['Valor de conversão da compra'].sum()
roas = (soma_faturamento / soma_valor_gasto) if soma_valor_gasto > 0 else 0

# Formatação para moeda
def format_to_currency(value):
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Criação da fileira de métricas
metric_row = st.columns(5)

with metric_row[0]:
    st.metric(label="Valor Valor usado (BRL)", value=format_to_currency(soma_valor_gasto))

with metric_row[1]:
    st.metric(label="Compras", value=f"{soma_compras}")

with metric_row[2]:
    st.metric(label="CAC", value=format_to_currency(media_cac))

with metric_row[3]:
    st.metric(label="Valor de conversão da compra", value=format_to_currency(soma_faturamento))

with metric_row[4]:
    st.metric(label="ROAS", value=f"{roas:.2f}")



# Incluir aqui o gráfico de KPIs diários
st.plotly_chart(create_kpi_charts(filtered_data), use_container_width=True)



# Criação dos gráficos
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(create_funnel_chart(filtered_data), use_container_width=True)

with col2:
    st.plotly_chart(create_performance_ctr_chart(filtered_data), use_container_width=True)
    st.plotly_chart(create_performance_metrics_chart(filtered_data), use_container_width=True)