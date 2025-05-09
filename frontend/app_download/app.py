import gradio as gr
import pandas as pd
import os
from datetime import datetime
import zipfile
import tempfile
import requests

API_URL = os.getenv('API_URL', 'http://localhost:8000')

def login(request: gr.Request):
    params = str(request.query_params).split('&')
    result_json = {}

    for i in range(len(params)):
        if '=' in params[i]:
            key, value = params[i].split('=')
            result_json[key] = value

    return result_json.get('u', None), result_json.get('p', None)

def get_filtered_user_data(base_url, circuit=None, operator_remark_contains=None, src=None, dst=None, start_time=None, end_time=None, bookmark=None, u=None, p=None):
    params = {
        "circuit": circuit,
        "operator_remark_contains": operator_remark_contains,
        "src": src,
        "dst": dst,
        "start_time": start_time,
        "end_time": end_time,
        "bookmark": bookmark,
        'user': u,
        'password': p
    }
    response = requests.get(f"{base_url}/filter_user_data/", params=params)
    return response.json()

def get_unique_values(base_url, column=None, u=None, p=None):
    params = {
        "column": column,
        'user': u,
        'password': p
    }
    response = requests.get(f"{base_url}/unique_values/", params=params)
    return response.json()

def get_dropdown_values(u, p):
    try:
        circuit = get_unique_values(base_url=API_URL, column='circuit', u=u, p=p)['unique_values']
        circuit.insert(0, 'empty')
    except:
        print('Database is empty')
        circuit = ['empty']
    return circuit

def download_transcripts(circuit, start_time, end_time, u, p):
    if start_time:
        start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

    if end_time:
        end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    circuit = None if circuit == 'empty' else circuit

    data = get_filtered_user_data(base_url=API_URL,
                                  circuit=circuit,
                                  start_time=start_time,
                                  end_time=end_time,
                                  u=u,
                                  p=p)

    if 'data' in data and data['data']:
        df = pd.DataFrame(data['data'])
        df['last_modified'] = pd.to_datetime(
            df['last_modified'].str.split('.').str[0],
            format='mixed'
        )
        transcripts = df[['file_name', 'stt_transcript']]


        start_time_str = start_time.strftime('%Y%m%d%H%M%S') if start_time else ''
        zip_filename = f"{circuit}_{start_time_str}.zip"
        temp_dir = tempfile.gettempdir()
        zip_file_path = os.path.join(temp_dir, zip_filename)
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            for index, row in transcripts.iterrows():
                file_name = row['file_name']
                stt_transcript = row['stt_transcript']
                transcript = stt_transcript
                if transcript:
                    transcript_filename = f"{file_name}.txt"
                    zip_file.writestr(transcript_filename, transcript)
        return zip_file_path
    else:
        return None

def refresh_dropdown(u, p):
    circuit_val = get_dropdown_values(u, p)
    return gr.Dropdown(choices=circuit_val, interactive=True, value=circuit_val[0])

def update_display(start_time, end_time):
    print(start_time, end_time)
    return start_time.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S")

with gr.Blocks(title='Download Transcripts', theme=gr.themes.Soft()) as demo:
    gr.Markdown('# Download Transcripts')

    u = gr.State()
    p = gr.State()

    circuit_dropdown = gr.Dropdown(label='Circuit', choices=None, interactive=False)

    with gr.Row():
        start_time_input = gr.Textbox(label='Start Time', info='e.g., 2024-01-05 17:52:30 (yyyy-mm-dd hh:mm:ss)')
        end_time_input = gr.Textbox(label='End Time', info='e.g., 2024-01-05 17:52:30  (yyyy-mm-dd hh:mm:ss)')

    download_button = gr.Button(value='Download Transcripts', variant='huggingface')
    refresh_button = gr.Button(value='Refresh Circuits', variant='huggingface')

    output_file = gr.File(label='Download Transcripts')

    demo.load(fn=login, outputs=[u, p]).then(refresh_dropdown, inputs=[u, p], outputs=circuit_dropdown)

    download_button.click(fn=download_transcripts, inputs=[circuit_dropdown, start_time_input, end_time_input, u, p], outputs=output_file)
    refresh_button.click(fn=refresh_dropdown, inputs=[u, p], outputs=circuit_dropdown)

demo.launch(server_name="0.0.0.0", share=True)
