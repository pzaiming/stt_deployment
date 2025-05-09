import gradio as gr
import requests
import pandas as pd
import os
import pytz

API_URL = os.getenv('API_URL', 'http://localhost:8000')

def login(request: gr.Request):
    params = str(request.query_params).split('&')
    result_json = {}

    for i in range(len(params)):
        if '=' in params[i]:
            key, value = params[i].split('=')
            result_json[key] = value

    return result_json.get('u', None), result_json.get('p', None)

def get_dataset(u, p):
    response = requests.get(f"{API_URL}/get_all_user_data/", params={"latest": 1, 'user': u, 'password': p})
    if response.status_code == 200:
        data = response.json()["data"]
        df = pd.DataFrame(data)
        if not df.empty:
            df['start_time'] = pd.to_datetime(df['start_time'])
            df['Start Time'] = df['start_time'].dt.strftime('%d/%m/%Y %H:%M:%S')

            df['last_modified'] = pd.to_datetime(df['last_modified'].str.split('.').str[0])
            df['Last Modified'] = df['last_modified'].dt.strftime('%d/%m/%Y %H:%M:%S')

            now = pd.Timestamp.now(tz=pytz.timezone('Asia/Singapore')).strftime('%Y-%m-%d %H:%M:%S')
            now = pd.to_datetime(now) # Why???
            time_diff = now - df['last_modified']
            total_seconds = time_diff.dt.total_seconds()

            days = (total_seconds // 86400).astype(int)
            remaining_seconds = total_seconds % 86400
            hours = (remaining_seconds // 3600).astype(int)
            minutes = ((remaining_seconds % 3600) // 60).astype(int)

            def format_time_ago(days, hours, minutes):
                time_ago = ''
                if days > 0:
                    time_ago += f'{days}d'
                if hours > 0 or days > 0:
                    time_ago += f'{hours}h'
                time_ago += f'{minutes}m'
                return time_ago

            df['Time Ago'] = [format_time_ago(d, h, m) for d, h, m in zip(days, hours, minutes)]

            df_display = df[['circuit', 'file_name', 'Start Time', 'Last Modified', 'Time Ago']]
            df_display.columns = ['Circuit', 'File Name', 'Start Time', 'Last Modified', 'Time Ago']
        else:
            df_display = pd.DataFrame(columns=['Circuit', 'File Name', 'Start Time', 'Last Modified' 'Time Ago'])
        return df_display, data
    else:
        return pd.DataFrame(columns=['Circuit', 'File Name', 'Start Time', 'Last Modified', 'Time Ago']), []

def on_row_select(evt: gr.SelectData, data):
    selected_row = evt.index[0]
    if selected_row is not None and data:
        df = pd.DataFrame(data)
        selected_data = df.iloc[selected_row]
        circuit_val = selected_data['circuit']
        start_time_val = selected_data['start_time']
        file_name_val = selected_data['file_name']
        return circuit_val, start_time_val, file_name_val
    else:
        return "", "", ""


with gr.Blocks(title='Circuit Monitoring', theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Circuit Monitoring")
    u = gr.State()
    p = gr.State()

    with gr.Row():
        get_dataset_btn = gr.Button("Update", variant='primary')
    data_df = gr.DataFrame(headers=['Circuit', 'File Name', 'Start Time', 'Last Modified', 'Time Ago'], interactive=False)

    data_store = gr.State()

    demo.load(fn=login, outputs=[u, p])
    get_dataset_btn.click(fn=get_dataset, inputs=[u, p], outputs=[data_df, data_store])

demo.launch(server_name="0.0.0.0")
