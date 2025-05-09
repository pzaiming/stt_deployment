import gradio as gr
import requests
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"

def get_dataset():
    response = requests.get(f"{BASE_URL}/get_all_user_data/?latest=1")
    if response.status_code == 200:
        data = response.json()["data"]
        df = pd.DataFrame(data)
        if not df.empty:
            df['start_time'] = pd.to_datetime(df['start_time'])
            df['Start Time'] = df['start_time'].dt.strftime('%d/%m/%Y %H:%M:%S')

            now = pd.Timestamp.now()
            time_diff = now - df['start_time']
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

            df_display = df[['circuit', 'Start Time', 'file_name', 'Time Ago']]
            df_display.columns = ['Circuit', 'Start Time', 'File Name', 'Time Ago']
        else:
            df_display = pd.DataFrame(columns=['Circuit', 'Start Time', 'File Name', 'Time Ago'])
        return df_display, data
    else:
        return pd.DataFrame(columns=['Circuit', 'Start Time', 'File Name', 'Time Ago']), []

def add_user_data(circuit, audio_file_path, file_name, duration, stt_transcript, gt_transcript,
                  operator_remark, start_time, src, dst, m_plan):
    data = {
        "circuit": circuit,
        "audio_file_path": audio_file_path,
        "file_name": file_name,
        "duration": duration,
        "stt_transcript": stt_transcript,
        "gt_transcript": gt_transcript,
        "operator_remark": operator_remark,
        "start_time": start_time,
        "src": src,
        "dst": dst,
        "m_plan": m_plan
    }
    response = requests.post(f"{BASE_URL}/add_user_data/", json=data)
    if response.status_code == 200:
        return "User data added successfully"
    else:
        return f"Error: {response.text}"

def remove_user_data(circuit, start_time, file_name):
    params = {
        "circuit": circuit,
        "start_time": start_time,
        "file_name": file_name
    }
    response = requests.delete(f"{BASE_URL}/delete_user_data/", params=params)
    if response.status_code == 200:
        return "User data deleted successfully"
    else:
        return f"Error: {response.text}"

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


with gr.Blocks() as demo:
    gr.Markdown("# Circuit Monitoring")

    with gr.Row():
        get_dataset_btn = gr.Button("Get Dataset")
    data_df = gr.DataFrame(headers=['Circuit', 'Start Time', 'File Name', 'Time Ago'], interactive=False)

    data_store = gr.State()

    with gr.Tabs():
        with gr.TabItem("Add"):
            with gr.Row():
                circuit = gr.Textbox(label="Circuit")
                start_time = gr.Textbox(label="Start Time (ISO format, e.g., 2018-11-19T02:04:57.426872)")
            with gr.Row():
                audio_file_path = gr.Textbox(label="Audio File Path")
                file_name = gr.Textbox(label="File Name")
                duration = gr.Textbox(label="Duration")
            with gr.Row():
                stt_transcript = gr.Textbox(label="STT Transcript")
                gt_transcript = gr.Textbox(label="GT Transcript")
            with gr.Row():
                src = gr.Textbox(label="Src")
                dst = gr.Textbox(label="Dst")
            with gr.Row():
                operator_remark = gr.Textbox(label="Operator Remark")
                m_plan = gr.Textbox(label="M Plan")

            add_btn = gr.Button("Add")
            add_output = gr.Textbox(label="Status")

            add_btn.click(
                fn=add_user_data,
                inputs=[circuit, audio_file_path, file_name, duration, stt_transcript, gt_transcript,
                        operator_remark, start_time, src, dst, m_plan],
                outputs=add_output
            )

        with gr.TabItem("Remove"):
            circuit_r = gr.Textbox(label="Circuit")
            start_time_r = gr.Textbox(label="Start Time (ISO format, e.g., 2018-11-19T02:04:57.426872)")
            file_name_r = gr.Textbox(label="File Name")

            remove_btn = gr.Button("Remove")
            remove_output = gr.Textbox(label="Status")

            remove_btn.click(
                fn=remove_user_data,
                inputs=[circuit_r, start_time_r, file_name_r],
                outputs=remove_output
            )

    get_dataset_btn.click(fn=get_dataset, inputs=[], outputs=[data_df, data_store])

    data_df.select(fn=on_row_select, inputs=[data_store], outputs=[circuit_r, start_time_r, file_name_r])

demo.launch(server_name="0.0.0.0", server_port=7869)
