import streamlit as st
import pandas as pd
import hashlib
import json

def apply_filters(df:pd.DataFrame) -> tuple[pd.DataFrame,str]:
    '''Отрисовывает виджеты фильтрации в боковой панели
    и возвращает отфильтрованный DataFrame.
    '''
    # Боковая панель с фильтрами
    st.sidebar.header('Фильтры')

    # Фильтр по цене
    price_range = get_range(df,'price','Цена аренды',1000)
    deposit_range = get_range(df,'deposit','Цена залога',1000)
    service_range = get_range(df,'agency_service','Комиссия агенства',1000)

    seller_type = get_multi_select(df,'seller_type','Тип продавца')
    district_type = get_multi_select(df,'district','Район')
    flat_type = get_multi_select(df,'flat_type','Тип квариры/кол-во комнат')
    #window_direction = get_multi_select(df,'window_direction','Направление окон',True)
    area_range = get_range(df,'area','Площадь (м²)',step=1.0,isfloat=True)

    rent_period = get_multi_select(df,'rent_period','Срок аренды')
    floor_range = get_range(df,'floor','Этаж',1)


    filters_state = {
        'price': price_range,
        'deposit': deposit_range,
        'agency_service': service_range,
        'seller_type': tuple(seller_type),
        'district': tuple(district_type),
        'flat_type': tuple(flat_type),
        'area': area_range,
        'rent_period': tuple(rent_period),
        'floor': floor_range,
    }

    filters_hash = hashlib.md5(json.dumps(filters_state, sort_keys=True).encode()).hexdigest()


    filtered = df[
        (df['price'] >= price_range[0]) & (df['price'] <= price_range[1]) & 
        (df['deposit'] >= deposit_range[0]) & (df['deposit'] <= deposit_range[1]) &
        (df['agency_service'] >= service_range[0]) & (df['agency_service'] <= service_range[1]) &
        (df['seller_type'].isin(seller_type)) &
        (df['district'].isin(district_type)) &
        (df['flat_type'].isin(flat_type)) &
        (df['area'] >= area_range[0]) & (df['area'] <= area_range[1]) &
        (df['rent_period'].isin(rent_period)) &
        (df['floor'] >= floor_range[0]) & (df['floor'] <= floor_range[1])
    ]

    return filtered,filters_hash

def get_range(df:pd.DataFrame, column_name: str, label: str, step: int|float, isfloat:bool = False):
    # Фильтр по цене
    if isfloat:
        min_price = float(df[column_name].min())
        max_price = float(df[column_name].max())
    
    else:
        min_price = int(df[column_name].min())
        max_price = int(df[column_name].max())

    price_range = st.sidebar.slider(
        label,
        min_value=min_price,
        max_value=max_price,
        value=(min_price,max_price),
        step= step
    )

    return price_range


def get_multi_select(df:pd.DataFrame,column_name: str,label:str):
    options = sorted(df[column_name].unique())

    selected_options = st.sidebar.multiselect(
        label=label,
        options=options,
        default=options
    )

    return selected_options


    