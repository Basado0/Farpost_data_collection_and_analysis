import pandas as pd
import streamlit as st
from streamlit_scroll_to_top import scroll_to_here

import math

def display_cards(df:pd.DataFrame,cols_per_row=2,cards_per_page=20,key_prefix='card'):
    """
    Отображает карточки квартир в виде сетки с пагинацией.
    
    Параметры:
    - df: DataFrame с данными
    - cols_per_row: количество карточек в строке (2 или 3)
    - cards_per_page: карточек на странице
    - key_prefix: префикс для уникальных ключей виджетов
    """

    if 'scroll_to_top' not in st.session_state:
        st.session_state.scroll_to_top = False

    def scroll_to_top():
        st.session_state.scroll_to_top = True

    if st.session_state.scroll_to_top:
        scroll_to_here(0, key='top')
        st.session_state.scroll_to_top = False

    
    total_cards = len(df)
    total_pages = math.ceil(total_cards/cards_per_page)

    page_key = f'{key_prefix}_page'
    if page_key not in st.session_state:
        st.session_state[page_key] = 1


    start_idx = (st.session_state[page_key] - 1) * cards_per_page
    end_idx = min(start_idx + cards_per_page, total_cards)

    st.caption(f'Показаны квартиры {start_idx + 1}-{end_idx} из {total_cards}')

    page_df = df.iloc[start_idx:end_idx].reset_index(drop=True)

    for i in range(0,len(page_df),cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i+j < len(page_df):
                row = page_df.iloc[i+j]
                with col:
                    with st.container(border=True):
                        # Заголовок:
                        title = row.get('title','Без заголовка')
                        st.markdown(f'## {title}')

                        district = row.get('district', 'Район не указан')
                        st.markdown(f"#### Район - {district}")

                        street_address = row.get('street_address')
                        st.markdown(f'#### Адрес - {street_address}')

                        flat_type = row.get('flat_type')
                        st.markdown(f"#### 🛏 **Тип квартиры/Кол-во комнат:** {flat_type if pd.notna(flat_type) else '—'}")

                        seller_type = row.get('seller_type')
                        st.write(f"**🏢 Тип продавца:** {seller_type if pd.notna(seller_type) else '-'}")
                        
                        rent_period = row.get('rent_period')
                        st.write(f"**Срок аренды:** {rent_period if pd.notna(rent_period) else 'Не указан'}")

                        images = row.get("images")
                        if images and isinstance(images, list) and len(images) > 0:
                            # Показываем до 3 изображений в строке
                            num_images = min(len(images), 3)
                            img_cols = st.columns(num_images)
                            for k in range(num_images):
                                with img_cols[k]:
                                    try:
                                        st.markdown(
                                            f'<img src="{images[k]}" style="width:100%; height:300px; object-fit:cover; border-radius:8px;">',
                                            unsafe_allow_html=True
                                            )
                                    except Exception:
                                        st.image("https://placehold.co/200x150?text=Ошибка", width='stretch')
                        else:
                            st.image("https://placehold.co/600x200?text=Нет+фото", width='stretch')
                        
                        # Цена с форматированием
                        price = row.get('price')
                        st.metric("💰 Цена аренды", f"{price:,.0f} ₽/мес")

                        # Залог
                        deposit = row.get('deposit')
                        st.write(f"💵 **Залог:** {deposit:,.0f} ₽" if pd.notna(deposit) else "💵 **Залог:** Без залога")

                        #Комиссия агенства
                        agency_service = row.get('agency_service')
                        st.write(f"**Комиссия агенства:** {agency_service:,.0f} ₽" if pd.notna(agency_service) else "**Комиссия агенства:** Без комиссии")
                        
                        # Основные характеристики в две колонки
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"📐 **Площадь:** {row.get('area')} м²")
                        with c2:
                            floor = row.get('floor')
                            st.write(f"🏢 **Этаж:** {int(floor) if pd.notna(floor) else '-'}")
                        
                        # Дополнительная информация (можно добавить под спойлер)
                        with st.expander("Подробнее"):

                            options_dict = {
                                'Продавец':'seller_name',
                                'Описание':'features',
                                'Бытовая техника':'appliances',
                                'Инфраструктура':'infrastructure',
                                'Требования к арендатору':'renter_requirements',
                                'Направление окон':'window_direction',
                                'Можно с животными':'pets_allowed',
                                'Ссылка на объявление':'url'
                            }

                            for option_title,column_name in options_dict.items():
                                show_optional_info(row,column_name,option_title)

    st.markdown('---')
    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        new_page = st.number_input(
            label='Страница',
            min_value = 1,
            max_value=total_pages,
            value=st.session_state[page_key],
            step=1,
            key=f'{key_prefix}_page_input'
        )

        if new_page != st.session_state[page_key]:
            st.session_state[page_key] = new_page
            scroll_to_top()
            st.rerun()
        


def show_optional_info(row:pd.Series,column_name: str, title: str):
    info = row.get(column_name)
    st.write(f'{title}: {info if pd.notna(info) else 'Не указано'}')