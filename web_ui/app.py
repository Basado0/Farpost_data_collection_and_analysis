import streamlit as st
import pandas as pd
import plotly.express as px
import json
from side_bar_filters import apply_filters
from flat_cards import display_cards
from dashboard import make_dashboard
import os

st.set_page_config(page_title="Анализ квартир", layout="wide")

@st.cache_data
def load_data():

    #Правильное расположение файла
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'Farpost_detail.json')

    with open(file_path,'r',encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    for field in ['price','deposit','agency_service','area','floor']:
        df[field] = pd.to_numeric(df[field])
        df[field] = df[field].fillna(0)
    
    df['rent_period'] = df['rent_period'].fillna('Не указано')
    
    return df

df = load_data()

filtered_df,current_hash = apply_filters(df)
hash_key = 'filters_hash'

if hash_key not in st.session_state or st.session_state[hash_key] != current_hash:
    st.session_state[hash_key] = current_hash
    st.session_state['flat_page'] = 1


# Основная область — две вкладки: "Таблица" и "Статистика"
tab1, tab2 = st.tabs(["📋 Таблица квартир", "📊 Статистика и графики"])


with tab1:
    if filtered_df.empty:
        st.info('Нет квартир, соответствующих фильтрам')

    else:
        display_cards(
            filtered_df, 
            cols_per_row=2,       # можно 2 или 3
            cards_per_page=12,    # количество на страницу
            key_prefix="flat"
        )


with tab2:
    if filtered_df.empty:
        st.info('Нет квартир, измените фильтры')
    else:
        make_dashboard(filtered_df)


