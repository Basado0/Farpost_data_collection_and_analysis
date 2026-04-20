import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def make_dashboard(df:pd.DataFrame):
    st.header('📊 Аналитика по отфильтрованным объявлениям')

    if df.empty:
        st.warning('Нет данных для отображения статистики. Измените фильтры.')
    
    else:
        col1,col2,col3,col4 = st.columns(4)

        with col1:
            st.metric('🏠 Всего квартир',len(df))
        with col2:
            avg_price = df['price'].mean()
            st.metric('💰 Средняя цена',f'{avg_price:,.0f} ₽/мес')
        with col3:
            median_price = df['price'].median()
            st.metric('📊 Медианная цена',f'{median_price:,.0f} ₽/мес')
        with col4:
            avg_area = df['area'].mean()
            st.metric('📐 Средняя площадь',f'{avg_area:.1f} м²')
        
        st.divider()

        col5,col6,col7,col8 = st.columns(4)

        with col5:
            st.empty()

        with col6:
            avg_deposit = df['deposit'].mean()
            median_deposit = df['deposit'].median()
            st.markdown('### Залог')
            st.metric(f'💰 Средний залог',f'{avg_deposit:,.0f} ₽')
            st.metric(f'📊 Медианный залог',f'{median_deposit:,.0f} ₽')

        with col7:
            avg_service = df['agency_service'].mean()
            median_service = df['agency_service'].median()
            st.markdown('### Комиссия агентства')
            st.metric(f'💰 Средний залог',f'{avg_service:,.0f} ₽')
            st.metric(f'📊 Медианный залог',f'{median_service:,.0f} ₽')
        
        with col8:
            st.empty()
        
        st.divider()

    # --- График 1: Распределение цен (гистограмма) ---
        hist1,hist2,hist3 = st.columns(3)
        with hist1:
            make_hist(df,'price','Распределение цен аренды','Цена (₽/мес)','#2E86AB')
        
        with hist2:
            make_hist(df,'deposit','Распределение цен залога','Цена (₽)',"#BAD61B")
        
        with hist3:
            make_hist(df,'agency_service','Распределение цен комиссии агентства','Цена (₽)',"#E03E33")

    
    # --- График 2: Средняя цена по районам (топ-10) ---
        bar1,bar2,bar3 = st.columns(3)
        with bar1:
            make_district_bar(df,'price','Средняя цена аренды по районам','Средняя цена (₽/мес)','#A23B72')
        with bar2:
             make_district_bar(df,'deposit','Средняя цена залога по районам','Средний залог (₽)',"#D6DA21")
        with bar3:
             make_district_bar(df,'agency_service','Средняя цена комиссии агентства по районам','Средняя комиссии (₽)',"#830808")

    # --- График 3: Зависимость цены от площади (scatter) с цветом по комнатам ---
        fig_scatter = px.scatter(
            df,
            x='area',
            y='price',
            color='flat_type',
            title='Цена vs Площадь (цвет = количество комнат)',
            labels={'area': 'Площадь (м²)', 'price': 'Цена (₽/мес)', 'flat_type': 'Тип квартиры'},
            hover_data=['district', 'flat_type'],
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_scatter, width='stretch')
    
    # --- График 4: Количество предложений по типу квартир ---
        pie1,pie2,pie3 = st.columns(3)

        with pie1:
            make_pie(df,'flat_type','Тип квартиры','Доля предложений по типу квартир')

        with pie2:
            make_pie(df,'seller_type','Тип продавца','Доля предложений по типу продавца')
        
        with pie3:
            def has_russian_only(text):
                if pd.isna(text):
                    return False
                text_lower = str(text).lower()
                keywords = ['русск','славян','только русские','русский']
                return any(keyword in text_lower for keyword in keywords)
        
            df['russian_only'] = df['renter_requirements'].apply(has_russian_only)
            russian_counts = df['russian_only'].value_counts().reset_index()
            russian_counts.columns = ['Требование','Количество']
            russian_counts['Требование'] = russian_counts['Требование'].map({True:'Только русским',False:'Не указано / другое'})

            russian_pie = px.pie(
                russian_counts,
                values='Количество',
                names='Требование',
                title='Доля объявлений с требованием "только русским"',
                hole=0.3,
                color_discrete_sequence=['#E63946', '#A8DADC']
                )
            st.plotly_chart(russian_pie, width='stretch')

    
    # --- График 5: гистограмма по сроку аренды
        rent_period_counts = df['rent_period'].value_counts().reset_index()
        rent_period_counts.columns = ['Срок аренды', 'Количество']
        fig_rent = px.bar(
            rent_period_counts,
            x='Срок аренды',
            y='Количество',
            title='Предложения по срокам аренды',
            text_auto=True,
            color_discrete_sequence=['#06A77D']
        )
        st.plotly_chart(fig_rent, width='stretch')
    

    # --- График 7: Цена по типу продавца
        fig_seller = px.box(
            df,
            x='seller_type',
            y='price',
            title='Распределение цен по типу продавца',
            labels={'seller_type': 'Тип продавца', 'price': 'Цена (₽/мес)'},
            color='seller_type'
        )
        st.plotly_chart(fig_seller, width='stretch')
    


def make_hist(df:pd.DataFrame,x:str,title:str,price_label:str,color:str):
    fig = px.histogram(
                df, 
                x=x, 
                nbins=30,
                title=title,
                labels={x: price_label, 'count': 'Количество квартир'},
                color_discrete_sequence=[color]
            )
    fig.update_layout(bargap=0.05)
    st.plotly_chart(fig, width='stretch')


def make_district_bar(df:pd.DataFrame,column_name:str,title:str,label:str,color:str):
    district = df.groupby('district')[column_name].mean().sort_values(ascending=False).reset_index()
    fig_district = px.bar(
        district,
        x='district',
        y=column_name,
        title=title,
        labels={'district': 'Район', column_name: label},
        text_auto='.0f',
        color_discrete_sequence=[color]
    )
    fig_district.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_district, width='stretch')


def make_pie(df:pd.DataFrame,column_name:str,column_title:str,title:str):
    counts = df[column_name].value_counts().reset_index()
    counts.columns = [column_title, 'Количество']
    seller_pie = px.pie(
        counts,
        values='Количество',
        names=column_title,
        title=title,
        hole=0.3
    )
    st.plotly_chart(seller_pie, width='stretch')


    