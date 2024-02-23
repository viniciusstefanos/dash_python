from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
import json
import pandas as pd
from dotenv import load_dotenv
import os

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

excel_output = '../data/sp24/raw/Anúncios-API.xlsx'
date_preset_window = 'maximum'

# Obtém as credenciais do ambiente
FB_APP_ID = os.getenv('FB_APP_ID')
FB_APP_SECRET = os.getenv('FB_APP_SECRET')
FB_ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN')
AD_ACCOUNT_ID = os.getenv('AD_ACCOUNT_ID')


# Linhas de impressão para depuração
print("Credentials OK!")



# Inicializa a API do Facebook Ads com as credenciais
FacebookAdsApi.init(FB_APP_ID, FB_APP_SECRET, FB_ACCESS_TOKEN)
print("Api inicializada")

# Cria o objeto da conta de anúncio
account = AdAccount(f'act_{AD_ACCOUNT_ID}')
print("Conta de Anúncios Definida")

# Nome da campanha que você quer filtrar
campaign_name_filter = "sp24"

def process_roas(roas_data):
    try:
        # Verifica se roas_data é uma lista e tem pelo menos um item
        if isinstance(roas_data, list) and len(roas_data) > 0:
            # Acessa o primeiro dicionário da lista e extrai o valor de 'value'
            roas_value = float(roas_data[0]['value'])
            roas_formatted = f"{roas_value:.2f}".replace('.', ',')
            return roas_formatted
        else:
            return "0,00"
    except (TypeError, ValueError, KeyError, IndexError):
        return "0,00"



def get_facebook_ads_insights(campaign_name_filter):
    try:
        """
        Esta função autentica na API do Facebook Ads, realiza chamadas de API para buscar dados,
        e salva os dados em um DataFrame.
        """

        # Campos que você deseja buscar
        fields = [
            'date_start',
            'date_stop',
            'spend',
            'impressions',
            'cpm',
            'reach',
            'frequency',
            'inline_link_clicks',
            'inline_link_click_ctr',
            'actions',
            'action_values',
            'conversion_values',
            'purchase_roas'
        ]


        # Parâmetros da busca
        params = {
            'date_preset': date_preset_window,  # Exemplo: buscar dados dos últimos 30 dias
            'filtering': [
                {'field': 'campaign.name', 'operator': 'CONTAIN', 'value': campaign_name_filter},
                {'field': 'campaign.name', 'operator': 'NOT_CONTAIN', 'value': 'meteorico'}
            ],
            'time_increment': 1,

                
            # Adicione mais parâmetros conforme necessário
        }

        # Busca insights em vez de anúncios
        insights = account.get_insights(fields=fields, params=params)
        print("Insights Coletados")
       
        # Converte os insights para um DataFrame do pandas
        insights_list = [insight.export_all_data() for insight in insights]
        df_insights = pd.DataFrame(insights_list)

        print("DataFrame definido")

        # Supondo que action_values seja uma coluna no df_insights que contém listas de dicionários como mostrado
        def process_purchase_values(action_values):
            if not isinstance(action_values, list):
                return 0.0
            return sum(float(action['value']) for action in action_values if action.get('action_type') == 'onsite_web_app_purchase')

        df_insights['Purchase Values'] = df_insights.apply(lambda row: process_purchase_values(row.get('action_values')), axis=1)

        # Ajuste na chamada da função
        df_insights['purchase_roas'] = df_insights['purchase_roas'].apply(process_roas)
       
        
        def process_actions(row):
            landing_page_views = 0
            purchases = 0
            initiate_checkouts = 0
            
            actions = row.get('actions', [])
            if isinstance(actions, list):
                for action in actions:
                    if action['action_type'] == 'landing_page_view':
                        landing_page_views += int(action['value'])
                    elif action['action_type'] == 'purchase':
                        purchases += int(action['value'])
                    elif action['action_type'] == 'initiate_checkout':
                        initiate_checkouts += int(action['value'])
            return landing_page_views, purchases, initiate_checkouts

        #Atualize este loop para processar a coluna 'actions'
        for index, row in df_insights.iterrows():
            l_views, purch, i_checkouts = process_actions(row)
            df_insights.at[index, 'Landing Page Views'] = l_views
            df_insights.at[index, 'Purchases'] = purch
            df_insights.at[index, 'Finalizações de compra iniciadas'] = i_checkouts

        
        
        # Em seguida, calcule o custo por compra e adicione como uma nova coluna
        df_insights['Cost per Purchase'] = df_insights.apply(lambda row: float(row['spend']) / row['Purchases'] if row['Purchases'] > 0 else 0, axis=1)


        # Remover as colunas 'actions' e 'conversion_values'
        df_insights.drop(columns=['actions'], inplace=True)
        df_insights.drop(columns=['action_values'], inplace=True)
        df_insights.drop(columns=['date_stop'], inplace=True)

        print("DataFrame atualizado")
     
        # Retorna o DataFrame
        return df_insights

    except Exception as e:
        print(f"Erro ao buscar insights: {e}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro


def renomear_colunas(df):
    mapeamento_colunas = {
        'date_start': 'Dia',
        'spend': 'Valor usado (BRL)',
        'impressions': 'Impressões',
        'cpm': 'CPM (custo por 1.000 impressões)',
        'reach': 'Alcance',
        'frequency': 'Frequência',
        'inline_link_clicks': 'Cliques no link',
        'inline_link_click_ctr':'CTR (taxa de cliques no link)',
        'Landing Page Views':'Visualizações da página de destino',
        'Purchases':'Compras',
        'Purchase Values':'Valor de conversão da compra',
        'purchase_roas':'Retorno sobre o investimento em publicidade (ROAS) das compras',
        'Cost per Purchase': 'Custo por compra',
        'initiate_checkout':'Finalizações de compra iniciadas',
        # Adicione mais mapeamentos conforme necessário
    }
    df.rename(columns=mapeamento_colunas, inplace=True)
    return df


if __name__ == '__main__':
    df_insights = get_facebook_ads_insights(campaign_name_filter)
    if not df_insights.empty:
        df_insights = renomear_colunas(df_insights)
        #print(df_insights)
        print("Sucesso")
        # Supondo que df_insights seja o seu DataFrame contendo os dados processados
        df_insights.to_excel(excel_output, index=False)

    else:
        print("Nenhum dado de insights foi retornado.")