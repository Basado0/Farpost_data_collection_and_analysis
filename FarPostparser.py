import requests
from bs4 import BeautifulSoup
import re
import json
import time
import os
from config import BASE_URL,HEADERS,DELAY
from webdriver import refresh_session


#session = refresh_session(BASE_URL,HEADERS)

def parse_listing_page(session,page_number: int):
    """Парсит страницу со списком, возвращает список словарей {'id': ..., 'url': ...}"""
    url = BASE_URL if page_number == 1 else f'{BASE_URL}?page={page_number}'
    response = session.get(url)
    is_captcha = False
    
    if response.status_code != 200:
        print(f'❌ Ошибка {response.status_code} на странице {page_number}')
        return [], is_captcha
    
    if 'Вы не робот' in response.text:
        is_captcha = True
        return [], is_captcha
    

    soup = BeautifulSoup(response.text, 'lxml')
    items = soup.select('tr[data-doc-id]')
    result = []
    
    for item in items:
        doc_id = item.get('data-doc-id')
        title_elem = item.select_one('.bulletinLink')

        if title_elem:
            url_path = title_elem.get('href')
            if url_path:
                full_url = f'https://www.farpost.ru{url_path}'
        
        city_elem = item.select_one('.bull-delivery__city')
        city = city_elem.get_text(strip=True) if city_elem else 'Владивосток'
        
        # Просмотры
        views_elem = item.select_one('.nano-eye-text')
        views = views_elem.get_text(strip=True).replace(' ', '') if views_elem else None

        result.append({'id': doc_id, 'url': full_url, 'city':city, 'views': views})
    
    return result, is_captcha


def parse_ad_details(soup: BeautifulSoup, **kwargs):
    """
    Парсит страницу конкретного объявления (soup уже загружен).
    Возвращает словарь со всеми полями.
    """
    result = kwargs.copy()

    def get_clean_text(element) -> str | None:
        if not element:
            return None
        text = element.get_text(separator=' ', strip=True)
        return re.sub(r'\s+', ' ', text)

    # ----- 1. Заголовок -----
    title_elem = soup.select_one('h1.subject span[data-field="subject"]')
    result['title'] = get_clean_text(title_elem)

    # ----- 2. Дата публикации -----
    date_elem = soup.select_one('.viewbull-actual-date')
    result['date'] = get_clean_text(date_elem)

    # ----- 3. Цена -----
    price_elem = soup.select_one('.viewbull-summary-price__value')
    if price_elem:
        price_text = price_elem.get_text(strip=True)
        price = re.sub(r'\s+', '', price_text).replace('₽', '').replace('руб', '')
        result['price'] = price
    else:
        result['price'] = None

    # ----- 4. Коммунальные услуги -----
    bills_elem = soup.select_one('.viewbull-summary-price__realty-bills')
    result['utilities'] = bills_elem.get_text(strip=True) if bills_elem else None

    # ----- 5. Залог -----
    deposit_elem = soup.select_one('.viewbull-summary__add-payment span[data-field="guarantee"]')
    if deposit_elem:
        deposit_text = deposit_elem.get_text(strip=True)
        match = re.search(r'(\d[\d\s]*)', deposit_text)
        result['deposit'] = re.sub(r'\s', '', match.group(1)) if match else None
    else:
        result['deposit'] = None
    
    agency_service_elem = soup.select_one('.viewbull-summary__add-payment span[data-field="agencyServicePrice"]')
    if agency_service_elem:
        agency_service = agency_service_elem.get_text(strip=True)
        match = re.search(r'(\d[\d\s]*)', agency_service)
        result['agency_service'] = re.sub(r'\s', '', match.group(1)) if match else None
    else:
        result['agency_service'] = None


    # ----- 6. Тип продавца -----
    seller_type_elem = soup.select_one('.viewbull-summary__owner-type span[data-field="isAgency"]')
    result['seller_type'] = seller_type_elem.get_text(strip=True) if seller_type_elem else None

    # ----- 7. Имя продавца -----
    seller_name_elem = soup.select_one('.seller-summary-user .userNick a')
    result['seller_name'] = seller_name_elem.get_text(strip=True) if seller_name_elem else None

    # ----- Вспомогательная функция для полей с лейблами -----
    def get_field_by_label(label_text: str) -> str | None:
        """Ищет блок .field, содержащий div.label с нужным текстом, и возвращает текст из .value"""
        label = soup.find('div', class_='label', string=label_text)
        if label:
            value_div = label.find_next_sibling('div', class_='value')
            if value_div:
                # Убираем лишние пробелы и переносы
                return ' '.join(get_clean_text(value_div).split())
        return None

    # ----- 8. Район -----
    result['district'] = get_field_by_label('Район')

    # ----- 9. Адрес -----
    street_address = get_field_by_label('Адрес')
    if street_address: 
        street_address = street_address.replace('Подробности о доме', '')
    result['street_address'] = street_address

    # ----- 10. Тип квартиры (Комнат в квартире) -----
    result['flat_type'] = get_field_by_label('Комнат в квартире')

    # ----- 11. Сторона окон -----
    result['window_direction'] = get_field_by_label('Сторона окон')

    # ----- 12. Площадь -----
    area_raw = get_field_by_label('Площадь без учета балкона')
    if area_raw:
        match = re.search(r'(\d+[.,]?\d*)', area_raw)
        result['area'] = match.group(1).replace(',', '.') if match else None
    else:
        result['area'] = None

    # ----- 13. Срок аренды -----
    result['rent_period'] = get_field_by_label('Срок аренды')

    # ----- 14. Этаж -----
    floor_raw = get_field_by_label('Этаж')
    if floor_raw:
        match_floor = re.search(r'(\d+)-й', floor_raw)
        result['floor'] = match_floor.group(1) if match_floor else None

    else:
        result['floor'] = None

    # ----- 15. Можно ли с животными -----
    # Ищем лейбл, содержащий слово "животными"
    label_pets = soup.find('div', class_='label', string=re.compile(r'животными', re.IGNORECASE))
    if label_pets:
        value_div = label_pets.find_next_sibling('div', class_='value')
        result['pets_allowed'] = value_div.get_text(strip=True) if value_div else None
    else:
        result['pets_allowed'] = None

    # ----- 16. Состояние и особенности -----
    features_elem = soup.select_one('.viewbull-field__container p[data-field="realtyFeature"]')
    result['features'] = features_elem.get_text(strip=True) if features_elem else None

    # ----- 17. Мебель -----
    furniture_elem = soup.select_one('.viewbull-field__container p[data-field="realtyFurniture"]')
    result['furniture'] = furniture_elem.get_text(strip=True) if furniture_elem else None

    # ----- 18. Бытовая техника -----
    appliances_elem = soup.select_one('.viewbull-field__container p[data-field="realtyHouseHold"]')
    result['appliances'] = appliances_elem.get_text(strip=True) if appliances_elem else None

    # ----- 19. Инфраструктура и коммуникации -----
    infra_elem = soup.select_one('.viewbull-field__container p[data-field="realtyInfrastructure"]')
    result['infrastructure'] = infra_elem.get_text(strip=True) if infra_elem else None

    # ----- 20. Особые требования к съемщикам -----
    requirements_elem = soup.select_one('.viewbull-field__container p[data-field="renterRequirements"]')
    result['renter_requirements'] = requirements_elem.get_text(strip=True) if requirements_elem else None

    small_images = soup.select('.image-gallery__small-images-grid .small-images-grid__image')
    total = len(small_images)
    images = []
    if total > 0:
        if total <= 3:
            indices = range(total)
        else:
            indices = [0, total // 2, -1]
        for idx in indices:
            img = small_images[idx]
            data_info = img.get('data-image-info')
            if data_info:
                try:
                    info = json.loads(data_info)
                    src = info.get('src')
                    if src:
                        images.append(src)
                except json.JSONDecodeError:
                    # запасной вариант: взять src из атрибута img
                    src = img.get('src')
                    if src:
                        images.append(src)
            else:
                src = img.get('src')
                if src:
                    images.append(src)

    result['images'] = images   

    return result

def parse_ad_page(session,**ad_info):
    """ad_info: словарь, содержащий как минимум ключ 'url'.
    Обычно это результат parse_listing_page: {'id', 'url', 'city', 'views'}"""

    ad_url = ad_info['url']
    response = session.get(ad_url)
    if response.status_code != 200:
        return None
    if "Вы не робот?" in response.text:
        print("Капча на странице объявления")
        return None
    soup = BeautifulSoup(response.text, 'lxml')
    return parse_ad_details(soup, **ad_info)


def full_urls_pars(session = None,page_continue = None, urls_list_path = 'data\Farpost_list_pages.json'):
    """
    Обходит страницы списка (начиная с 1), пока есть объявления.
    Возвращает список словарей с полями id, url, city, views для каждого объявления.
    """
    start_time = time.time()

    if not session:
        current_session = refresh_session(BASE_URL)
    else: current_session = session
    pages = []          # список всех собранных ссылок
    if page_continue:
        current_page = page_continue
    else:
        current_page = 1

    while True:
        print(f"\n📄 Загрузка страницы {current_page}...")
        ads, is_captcha = parse_listing_page(current_session, current_page)  # возвращает список, может быть пустым

        if not ads and not is_captcha:                     # если нет объявлений — выходим
            print(f"⚠️ На странице {current_page} нет объявлений. Это была последняя страница, завершаем.")
            break

        if not ads and is_captcha:
            print(f"❌ На странице {current_page} обнаружена капча\nПересоздаём сессию и пробуем заново...")
            current_session = refresh_session(url=BASE_URL+'?page={current_page}')
            continue

        else:
            pages.extend(ads)               # добавляем новые объявления в общий список
            print(f"✅ Страница {current_page}: добавлено {len(ads)} объявлений, всего {len(pages)}")

            current_page += 1
            time.sleep(DELAY)     # задержка между запросами

    # После завершения сбора ссылок:

    unique_pages = {item['id']:item for item in pages}
    pages = list(unique_pages.values())
    
    with open(urls_list_path, 'w', encoding='utf-8') as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)

    print(f'Сбор ссылок завершён!\nКоличество уникальных ссылок - {len(pages)}\nЗатрачено времени: {time.time() - start_time} сек.')



def add_details(session = None,id_continue = None, input_file = 'data/Farpost_list_all.json',output_file = 'data/farpost_detail.jsonl'):
    """ Парсит детали объявлений из JSON-файла со ссылками.
    
    Аргументы:
        session: requests.Session с уже установленными куками/заголовками
        id_continue: если указан, начинает с объявления с этим id (строка или число)
        input_file: путь к JSON-файлу со списком объявлений (список словарей с ключами id, url, city, views)
        output_file: выходной файл в формате JSON Lines (каждая строка — JSON объекта)"""
    
    with open(input_file,'r',encoding='utf-8') as f:
        ads = json.load(f)
    
    processed_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        processed_ids.add(data['id'])
                    except json.JSONDecodeError:
                        continue
    
    # Если указан id_continue, находим индекс начала
    start_index = 0
    if id_continue is not None:
        for i, ad in enumerate(ads):
            if str(ad['id']) == str(id_continue):
                start_index = i
                break
        else:
            print(f"⚠️ id_continue {id_continue} не найден в файле, начинаем с начала.")
            start_index = 0
    
    total = len(ads)
    if session:
        current_session = session
    else: current_session = refresh_session(BASE_URL)
    idx = start_index

    # Функция для сохранения текущего ID при прерывании
    def save_continue_id(ad_id):
        with open('continue.txt', 'w', encoding='utf-8') as cf:
            cf.write(str(ad_id))
        print(f"\n💾 Сохранён ID для продолжения: {ad_id} (файл continue.txt)")

    try:
        while idx < total:
            ad_info = ads[idx]
            ad_id = ad_info['id']
            
            # Пропускаем уже обработанные
            if ad_id in processed_ids:
                print(f"⏭️ Пропускаем {ad_id} (уже обработано)")
                idx += 1
                continue
            
            print(f"\n📦 Обработка {idx+1}/{total}: {ad_id} {ad_info['url']}")
            
            try:
                details = parse_ad_page(current_session, **ad_info)
                if details:
                    # Дописываем в файл в формате JSON Lines
                    with open(output_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(details, ensure_ascii=False) + '\n')
                    processed_ids.add(ad_id)
                    print(f"✅ Успешно сохранено объявление {ad_id}")
                    idx += 1
                else:
                    print(f"❌ Не удалось спарсить {ad_id} (возможно капча или ошибка)")
                    url = ad_info['url']
                    # Если капча, можно прервать или сделать паузу
                    if "Вы не робот?" in current_session.get(url).text:
                        print("🛑 Обнаружена капча. Парсинг остановлен. создаём новую сессию и продолжаем с id=" + ad_id)
                        current_session = refresh_session(url,HEADERS)  # новая сессия
                        print("✅ Сессия обновлена. Повторяем попытку для того же объявления.")
                        time.sleep(2)
                        continue
                    
                    else:
                        print(f"❌ Не удалось спарсить {ad_id} (неизвестная ошибка)")
                        idx += 1
                        
            except Exception as e:
                print(f"⚠️ Ошибка при обработке {ad_id}: {e}")
                # Пауза перед следующей попыткой
                time.sleep(4)
                idx += 1
            
            # Задержка между запросами
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Получен сигнал Ctrl+C. Завершаем работу...")
        if idx < total:
            current_ad_idx = ads[idx]['id']
            save_continue_id(current_ad_idx)
        else:
            print("✅ Все объявления уже обработаны.")
        print("👋 Выход. При следующем запуске используйте id_continue из файла continue.txt")
        return
    
    if idx == total:
        print("\n🏁 Парсинг деталей завершён!")
        if os.path.exists('continue.txt'):
            os.remove('continue.txt')


if __name__ == "__main__":

    #full_urls_pars(session,82)
    '''with open('continue.txt','r',encoding='utf-8') as f:
        id_continue = f.read()'''
    session = refresh_session(BASE_URL)
    add_details(session,id_continue=13264229815)

