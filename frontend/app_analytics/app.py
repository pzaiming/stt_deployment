import gradio as gr
import requests
import pandas as pd
import os


API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000')

def login(request: gr.Request):
    params = str(request.query_params).split('&')
    result_json = {}

    for i in range(len(params)):
        if '=' in params[i]:
            key, value = params[i].split('=')
            result_json[key] = value

    return result_json.get('u', None), result_json.get('p', None)

def update_analytics(u, p):
    response = requests.get(f"{API_URL}/get_all_user_data/", params={'user': u, 'password': p})
    df = pd.DataFrame(response.json()['data'])
    df['last_modified'] = pd.to_datetime(df['last_modified'].str.split('.').str[0])
    analytics_df = df.groupby('circuit').agg(
        total_files=('file_name', 'count'),
        last_modified=('last_modified', 'max')
    ).reset_index()
    analytics_df['last_modified'] = analytics_df['last_modified'].dt.strftime('%Y-%m-%d %H:%M:%S')

    return analytics_df

with gr.Blocks(title='Analytics App',theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Circuit Analytics")

    u = gr.State()
    p = gr.State()

    with gr.Row():
        refresh_button = gr.Button("Refresh Data", variant='primary')
    df_block = gr.Dataframe()
    refresh_button.click(update_analytics, inputs=[u, p], outputs=[df_block])
    
    demo.load(fn=login, outputs=[u, p])

demo.launch()
