import requests
import pandas as pd
import json
from datetime import datetime


class ParserCBRF:
    def __init__(self, url, download_path='mb_bd.xlsx'):
        self.url = url
        self.download_path = download_path

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
                        record[col] = value
                records.append(record)

            records = [item for item in records if any(item.values())]

            processed_data[sheet_name] = records

        return processed_data

    @staticmethod
    def convert_dates_to_strings(df):
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%d.%m.%Y')
        return df

    @staticmethod
    def save_to_json(processed_data, json_file='parsed_data.json'):
        def default(o):
            if isinstance(o, datetime):
                return o.strftime('%d.%m.%Y')
            raise TypeError(f'Object of type {o.__class__.__name__} is not JSON serializable')

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, default=default, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    cbr_url = "https://www.cbr.ru/vfs/statistics/ms/mb_bd.xlsx"
    parser = ParserCBRF(cbr_url)
    parsed_data = parser.start()
