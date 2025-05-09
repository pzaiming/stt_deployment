import gradio as gr
import pandas as pd
import os
from datetime import datetime
import requests

from calculate_wer import process_pair, generate_summary_and_zip

API_URL = os.getenv('API_URL', 'http://localhost:8000')

def login(request: gr.Request):
    params = str(request.query_params).split('&')
    result_json = {}

    for i in range(len(params)):
        if '=' in params[i]:
            key, value = params[i].split('=')
            result_json[key] = value

    return result_json.get('u', ""), result_json.get('p', "")

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

def get_data(circuit, start_time, end_time, u, p):
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
        df = df[['file_name', 'stt_transcript', 'gt_transcript']]
        df['stt_available'] = df['stt_transcript'].notnull() & df['stt_transcript'].str.strip().astype(bool)
        df['gt_available'] = df['gt_transcript'].notnull() & df['gt_transcript'].str.strip().astype(bool)
        data_list = list(zip(df['file_name'], df['stt_transcript'], df['gt_transcript']))
        display_df = df[['file_name', 'stt_available', 'gt_available']]
        return data_list, display_df
    else:
        return [], pd.DataFrame(columns=['file_name', 'stt_available', 'gt_available'])

def refresh_dropdown(u, p):
    circuit_val = get_dropdown_values(u, p)
    return gr.Dropdown(choices=circuit_val, interactive=True, value=circuit_val[0])


def evaluate_data(data_list):
    results = []
    for item in data_list:
        file_name, stt_transcript, gt_transcript = item
        if (
            pd.notna(stt_transcript) and pd.notna(gt_transcript) and
            stt_transcript.strip() and gt_transcript.strip()
        ):
            result = process_pair(gt_transcript, stt_transcript, file_name)
            if result is not None:
                results.append(result)
    if results:
        output_files, zip_file_path = generate_summary_and_zip(results)
        return output_files + [zip_file_path]
    else:
        return [None for _ in range(5)]

def load_data(circuit, start_time, end_time, u, p):
    data_list, display_df = get_data(circuit, start_time, end_time, u, p)
    return data_list, display_df

with gr.Blocks(title='Drifting App', theme=gr.themes.Soft()) as demo:
    gr.Markdown('# Evaluate')

    u = gr.State("")
    p = gr.State("")

    circuit_dropdown = gr.Dropdown(label='Circuit', choices=None, interactive=False)

    with gr.Row():
        start_time_input = gr.Textbox(label='Start Time', info='e.g., 2024-01-05 17:52:30')
        end_time_input = gr.Textbox(label='End Time', info='e.g., 2024-01-05 17:52:30')

    load_data_button = gr.Button(value='Load Data', variant='huggingface')
    with gr.Row():
        refresh_button = gr.Button(value='Refresh Circuits', variant='huggingface')

    data_table = gr.Dataframe(label='User Data')

    evaluate_button = gr.Button(value='Evaluate', variant='huggingface')

    with gr.Row():
        errors_file = gr.File(label='Errors Context (CSV)')
        word_errors_file = gr.File(label='Word Errors (CSV)')

    download_zip = gr.File(label='Download All Results (ZIP)')

    data_state = gr.State([])

    demo.load(fn=login, outputs=[u, p]).then(refresh_dropdown, inputs=[u, p], outputs=circuit_dropdown)

    load_data_button.click(fn=load_data, inputs=[circuit_dropdown, start_time_input, end_time_input, u, p], outputs=[data_state, data_table])
    refresh_button.click(fn=refresh_dropdown, inputs=[u, p], outputs=circuit_dropdown)
    evaluate_button.click(fn=evaluate_data, inputs=[data_state], outputs=[errors_file, word_errors_file, download_zip])

demo.launch(server_name="0.0.0.0", share=True)
