import re
import json
import csv


def find_emails(text):
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    return re.findall(email_pattern, text)


with open('traders.txt', 'r') as file:
    inn_list = [line.strip() for line in file]

with open('traders.json', 'r', encoding='utf-8') as file:
    traders_data = json.load(file)

filtered_traders = []
for trader in traders_data:
    if trader['inn'] in inn_list:
        filtered_traders.append({
            'inn': trader['inn'],
            'ogrn': trader['ogrn'],
            'address': trader['address']
        })

with open('traders.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['inn', 'ogrn', 'address']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for trader in filtered_traders:
        writer.writerow(trader)

with open('1000_efrsb_messages.json', 'r', encoding='utf-8') as file:
    messages_data = json.load(file)

emails_by_inn = {}

for message in messages_data:
    inn = message.get('publisher_inn')
    msg_text = message.get('msg_text', '')
    emails = find_emails(msg_text)
    if inn and emails:
        if inn not in emails_by_inn:
            emails_by_inn[inn] = set()
        emails_by_inn[inn].update(emails)

emails_by_inn = {inn: list(emails) for inn, emails in emails_by_inn.items()}

with open('emails.json', 'w', encoding='utf-8') as jsonfile:
    json.dump(emails_by_inn, jsonfile, ensure_ascii=False, indent=4)

print("Данные сохранены в файлы traders.csv и emails.json")
