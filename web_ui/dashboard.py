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
    
    # --- График 1: Распределение цен (гистограмма) ---
        fig_price = px.histogram(
            df, 
            x='price', 
            nbins=30,
            title='Распределение цен аренды',
            labels={'price': 'Цена (₽/мес)', 'count': 'Количество квартир'},
            color_discrete_sequence=['#2E86AB']
        )
        fig_price.update_layout(bargap=0.05)
        st.plotly_chart(fig_price, width='stretch')
    
    # --- График 2: Средняя цена по районам (топ-10) ---
        price_by_district = df.groupby('district')['price'].mean().sort_values(ascending=False).reset_index()
        fig_district = px.bar(
            price_by_district,
            x='district',
            y='price',
            title='Средняя цена аренды по районам',
            labels={'district': 'Район', 'price': 'Средняя цена (₽/мес)'},
            text_auto='.0f',
            color_discrete_sequence=['#A23B72']
        )
        fig_district.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_district, width='stretch')

    # --- График 3: Зависимость цены от площади (scatter) с цветом по комнатам ---
        # Извлекаем количество комнат из flat_type (например, "3-комнатная" → 3)
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
        flat_type_counts = df['flat_type'].value_counts().reset_index()
        flat_type_counts.columns = ['Тип квартиры', 'Количество']
        fig_pie = px.pie(
            flat_type_counts,
            values='Количество',
            names='Тип квартиры',
            title='Доля предложений по типу квартир',
            hole=0.3
        )
        st.plotly_chart(fig_pie, width='stretch')
    
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
    
    # --- График 6: Круговая диаграмма по типам продавцов
        seller_type_counts = df['seller_type'].value_counts().reset_index()
        seller_type_counts.columns = ['Тип продавца', 'Количество']
        seller_pie = px.pie(
            seller_type_counts,
            values='Количество',
            names='Тип продавца',
            title='Доля предложений по типу продавца',
            hole=0.3
        )
        st.plotly_chart(seller_pie, width='stretch')


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
    
    # ---График 8: Сдаётся только русским или нет
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




    