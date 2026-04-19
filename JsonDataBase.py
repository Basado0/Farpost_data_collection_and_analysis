import json
import os
from FarPostparser import full_urls_pars, add_details

class JsonDataBase:

    def __init__(self,data_path = 'data/farpost_detail.json'):
        self.data_path = data_path
    
    def create_detail_data(self,urls_list = 'data/Farpost_list_pages.json',continue_id_file = 'continue.txt'):
        id_continue = None
        
        if os.path.exists(continue_id_file):
            with open(continue_id_file,'r',encoding='utf-8') as f:
                id_continue = f.read()
        
        add_details(id_continue=id_continue,input_file=urls_list,output_file='test.jsonl')

    
    def create_detail_json(self,json_lines_path = 'data/farpost_detail.jsonl',detail_json = 'data/Farpost_detail.json'):
        try:
            with open(json_lines_path,'r',encoding='utf-8') as f:
                details = [json.loads(line.strip()) for line in f]
            with open(detail_json,'w',encoding='utf-8') as f:
                json.dump(details, f, ensure_ascii=False, indent=2)
                print(f'Успешное преобразование в {detail_json} 😊')
    
        except FileNotFoundError:
            print(f'Не могу найти файл {json_lines_path} 😵')



    def filter_null_lines(self,json_lines_path):
        kept_lines = []
        lines_count = 0
        try:
            with open(json_lines_path,'r',encoding='utf-8') as f:
                for line in f:
                    lines_count += 1
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if record.get('price') is not None:
                            kept_lines.append(line + '\n')
                    except json.JSONDecodeError:
                        continue

            with open(json_lines_path,'w',encoding='utf-8') as f:
                f.writelines(kept_lines)
                new_lines_count = len(kept_lines)
                print(f'Файл {json_lines_path} отфильтрован 😀, убрано {lines_count - new_lines_count} null значений 😱\n\
Всего осталось {new_lines_count} значений 👍')

        except FileNotFoundError:
            print(f'Не могу найти файл {json_lines_path} 😵')


    def get_urls(self,file_title = 'Farpost_list_all.json'):
        full_urls_pars(urls_list_path=file_title)
    
    


jsondb = JsonDataBase()
#jsondb.get_urls('test_urls.json')
#jsondb.create_detail_data()
jsondb.filter_null_lines('data/farpost_detail.jsonl')
jsondb.create_detail_json(detail_json='Farpost_detail.json')
