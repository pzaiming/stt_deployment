import requests
import os

all_data = requests.get('http://127.0.0.1:8000/get_all_user_data', params={'user': 'user2', 'password':'userpassword'})

existing = os.listdir()
for file in all_data.json()['data']:
    circuit = file['circuit']
    file_name = file['file_name']
    start_time = file['start_time']

    if file_name not in existing:
        continue
    
    with open(file_name.replace('.wav', '.txt'), 'r', encoding='utf-8') as f:
        requests.patch('http://127.0.0.1:8000/update_user_data_partial', params={'circuit': circuit, 'start_time': start_time, 'file_name': file_name, 'user': 'user2', 'password': 'userpassword'}, json={'gt_transcript': f.read()})