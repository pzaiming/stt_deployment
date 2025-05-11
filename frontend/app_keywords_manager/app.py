import gradio as gr
import requests
import pandas as pd
import os

API_URL = os.getenv('API_URL', 'http://localhost:8000')

def login(request: gr.Request):
    params = str(request.query_params).split('&')
    result_json = {}

    for i in range(len(params)):
        if '=' in params[i]:
            key, value = params[i].split('=')
            result_json[key] = value

    return result_json.get('u', None), result_json.get('p', None)

def get_keywords(u, p):
    url = f'{API_URL}/get_all_keywords/'
    response = requests.get(url, params={"user": u, "password": p})
    if response.status_code == 200:
        data = response.json().get('data', [])
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame({"keyword": [], "priority_": [], "service_": []})
        return df
    else:
        return pd.DataFrame({"keyword": [], "priority_": [], "service_": []})
    
def add_keyword(keyword, priority_, service_, u, p):
    url = f'{API_URL}/add_keyword/'
    data = {
        "keyword": keyword,
        "priority_": str(priority_),
        "service_": service_,
        "created_by": u
    }

    print(data)
    response = requests.post(url, json=data, params={"user": u, "password": p})
    if response.status_code == 200:
        return "Keyword added successfully."
    else:
        return f"Failed to add keyword. Error: {response.text}"
    
def delete_keyword(keyword, priority_, service_, u, p):
    url = f'{API_URL}/delete_keyword/'
    params = {
        "keyword": keyword,
        "priority_": int(priority_),
        "service_": service_,
        "user": u,
        "password": p,
        "created_by": u
    }
    response = requests.delete(url, params=params)
    if response.status_code == 200:
        return "Keyword deleted successfully."
    else:
        return f"Failed to delete keyword. Error: {response.text}"
    
def on_select(evt: gr.SelectData, df):
    row_index = evt.index[0]
    row_data = df.iloc[row_index]
    keyword = row_data['keyword']
    priority_ = str(row_data['priority_'])
    service_ = row_data['service_']
    return keyword, priority_, service_

with gr.Blocks(title='Keyword Manager', theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Keywords")
    
    u = gr.State()
    p = gr.State()

    get_db_btn = gr.Button("Update")
    keyword_df = gr.Dataframe(headers=["keyword", "priority_", "service_"], interactive=False)
    get_db_btn.click(fn=get_keywords, inputs=[u, p], outputs=keyword_df)
    
    with gr.Tabs():
        with gr.TabItem("Add Keyword"):
            keyword_input = gr.Textbox(label="Keyword")
            priority_input = gr.Dropdown(choices=['1','2','3','4'], label="Priority", value='1')
            service_input = gr.Textbox(label="Service")
            add_btn = gr.Button("Add Keyword", variant='primary')
            add_result = gr.Textbox(label="Result")
            add_btn.click(fn=add_keyword, inputs=[keyword_input, priority_input, service_input, u, p], outputs=add_result)
        
        with gr.TabItem("Delete Keyword"):
            keyword_input_del = gr.Textbox(label="Keyword")
            priority_input_del = gr.Dropdown(choices=['1','2','3','4'], label="Priority", value='1')
            service_input_del = gr.Textbox(label="Service")
            del_btn = gr.Button("Delete Keyword", variant='primary')
            del_result = gr.Textbox(label="Result")
            del_btn.click(fn=delete_keyword, inputs=[keyword_input_del, priority_input_del, service_input_del, u, p], outputs=del_result)
    
    keyword_df.select(fn=on_select, inputs=[keyword_df], outputs=[keyword_input_del, priority_input_del, service_input_del])

    demo.load(fn=login, outputs=[u, p])

demo.launch(server_name="0.0.0.0", share=True)
