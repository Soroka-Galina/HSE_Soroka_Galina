import requests
import pandas as pd
import json
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from pathlib import Path


class ParserCBRF:
    def __init__(self, url, download_path='mb_bd.xlsx', save_dir='parsed_data'):
        self.url = url
        self.download_path = download_path
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def start(self):
        self.__download_file()
        processed_data = self.__parse_file()
        self.save_to_json(processed_data)
        return processed_data

    def __download_file(self):
        response = requests.get(self.url)
        response.raise_for_status()
        with open(self.download_path, 'wb') as file:
            file.write(response.content)

    def __parse_file(self):
        raw_data = pd.read_excel(self.download_path, sheet_name=None, engine='openpyxl')
        processed_data = {}
        for sheet_name, df_raw in raw_data.items():
            start_row_index = df_raw[df_raw.iloc[:, 0] == "01.01.1995"].index[0]
            df_selected = df_raw.iloc[start_row_index:, :9]
            df_selected.columns = df_raw.iloc[3].astype(str)
            df_selected = df_selected.reset_index(drop=True)
            df_selected = df_selected.where(pd.notnull(df_selected), None)
            df_selected = self.convert_dates_to_strings(df_selected)

            records = []
            for _, row in df_selected.iterrows():
                record = {}
                for col, value in row.items():
                    if pd.notnull(value):
                        if col == 'nan':
                            col = 'Дата'
                        record[col] = self.convert_value(value)
                records.append(record)

            records = [item for item in records if any(item.values())]
            processed_data[sheet_name] = records

        return processed_data

    @staticmethod
    def convert_dates_to_strings(df):
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d')
        return df

    @staticmethod
    def convert_value(value):
        if isinstance(value, (int, float)):
            return str(Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        elif isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        else:
            return value

    def save_to_json(self, processed_data, json_file='parsed_data.json'):
        json_path = self.save_dir / json_file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=4)


class CBRFDataHandler:
    def __init__(self, data):
        self.data = data

    @classmethod
    def from_json(cls, json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(data)

    def get_data_by_sheet(self, sheet_name):
        return self.data.get(sheet_name, [])

    def filter_data_by_year(self, sheet_name, year):
        sheet_data = self.get_data_by_sheet(sheet_name)
        filtered_data = [record for record in sheet_data if record.get('Дата', '').startswith(year)]
        return filtered_data

    def print_data_in_columns(self, sheet_name, year):
        filtered_data = self.filter_data_by_year(sheet_name, year)
        if filtered_data:
            print(f"Данные для {sheet_name} в {year}:")
            for record in filtered_data:
                for key, value in record.items():
                    print(f"{key}: {value}")
                print("-" * 20)
        else:
            print(f"Данные не найдены для {sheet_name} в {year}.")


if __name__ == "__main__":
    cbr_url = "https://www.cbr.ru/vfs/statistics/ms/mb_bd.xlsx"
    parser = ParserCBRF(cbr_url)
    parsed_data = parser.start()

    handler = CBRFDataHandler(parsed_data)
    sheet_name_to_print = "Лист1"
    year_to_filter = "2023"  # Укажите год, по которому вы хотите отфильтровать данные
    handler.print_data_in_columns(sheet_name_to_print, year_to_filter)
