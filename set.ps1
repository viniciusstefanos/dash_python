# Ativa o ambiente virtual do Python
.venv\Scripts\Activate.ps1

# Muda para o diretório 'src'
cd src

# Executa o script para extrair dados do Facebook Ads
python facebook_ads.py

# Executa o aplicativo Streamlit
streamlit run app.py
