import gradio as gr
import os
import requests

IP_ADDRESS = os.getenv('IP_ADDRESS', 'http://127.0.0.1')
AUDIO_TRANSCRIPTION_PORT = os.getenv('AUDIO_TRANSCRIPTION_PORT', '7681')
KEYWORD_PORT = os.getenv('KEYWORD_PORT', '7682')
MONITOR_PORT = os.getenv('MONITOR_PORT', '7683')
ERROR_PORT = os.getenv('ERROR_PORT', '8050')
DRIFT_PORT = os.getenv('DRIFT_PORT', '7684')
DOWNLOAD_PORT = os.getenv('DOWNLOAD_PORT', '7685')
ANALYTICS_PORT = os.getenv('ANALYTICS_PORT', '7686')

API_URL = os.getenv('API_URL', 'http://localhost:8000')

def login(username, password):
    try:
        response = requests.post(f"{API_URL}/login_user/", json={"username": username, "password": password})
        if response.status_code == 200:
            return True, [username, password], "Login successful."
        else:
            return False, None, "Invalid username or password."
    except Exception as e:
        return False, None, f"Error: {str(e)}"

def update_all_buttons(authenticated, user_info):
    if authenticated:
        u, p = user_info[0], user_info[1]
    else:
        u, p = '', ''

    if u and p:
        return (
            gr.Button(
                    link=f"{IP_ADDRESS}:{AUDIO_TRANSCRIPTION_PORT}?u={u}&p={p}",
                    interactive=True
                ),
            gr.Button(
                    link=f"{IP_ADDRESS}:{KEYWORD_PORT}?u={u}&p={p}",
                    interactive=True
                ),
            gr.Button(
                    link=f"{IP_ADDRESS}:{DRIFT_PORT}?u={u}&p={p}",
                    interactive=True
                ),
            gr.Button(
                    link=f"{IP_ADDRESS}:{ERROR_PORT}?u={u}&p={p}",
                    interactive=True
                ),
            gr.Button(
                    link=f"{IP_ADDRESS}:{MONITOR_PORT}?u={u}&p={p}",
                    interactive=True
                ),
            gr.Button(
                    link=f"{IP_ADDRESS}:{DOWNLOAD_PORT}?u={u}&p={p}",
                    interactive=True
                ),
            gr.Button(
                    link=f"{IP_ADDRESS}:{ANALYTICS_PORT}?u={u}&p={p}",
                    interactive=True
                )
        )
    else:
        return [gr.Button(interactive=False) for _ in range(7)]

with gr.Blocks(title="Overview Application", theme=gr.themes.Soft()) as demo:
    gr.Markdown('# AI LAB - WELCOME TO OTTERSPHERE')
    gr.Markdown('### Click on the button to go to the App:')
    gr.Markdown('# _________________________________')

    authenticated = gr.State(False)
    user_info = gr.State(None)

    with gr.Row():
        with gr.Column():
            gr.Markdown('## Overview')
            audio_transcription_button = gr.Button(
                value='Audio Transcription App',
                variant='primary',
                link=f"{IP_ADDRESS}:{AUDIO_TRANSCRIPTION_PORT}",
                interactive=False
            )

            keyword_manager_button = gr.Button(
                value='Keyword Manager App',
                variant='primary',
                link=f"{IP_ADDRESS}:{KEYWORD_PORT}",
                interactive=False
            )

            drift_app_button = gr.Button(
                value='Drift App',
                variant='huggingface',
                link=f"{IP_ADDRESS}:{DRIFT_PORT}",
                interactive=False
            )

            error_analysis_button = gr.Button(
                value='Error Analysis App',
                variant='huggingface',
                link=f"{IP_ADDRESS}:{ERROR_PORT}",
                interactive=False
            )

            circuit_monitoring_button = gr.Button(
                value='Circuit Monitoring App',
                link=f"{IP_ADDRESS}:{MONITOR_PORT}",
                interactive=False
            )

            download_data_button = gr.Button(
                value='Download Data App',
                link=f"{IP_ADDRESS}:{DOWNLOAD_PORT}",
                interactive=False
            )
            
            analytics_app_button = gr.Button(
                value='Analytics App',
                variant='stop',
                link=f"{IP_ADDRESS}:{ANALYTICS_PORT}",
                interactive=False
            )
        with gr.Column():
            gr.Markdown("## Login")
            username_input = gr.Textbox(label="Username")
            password_input = gr.Textbox(label="Password", type="password")
            login_button = gr.Button("Login")
            login_output = gr.Textbox(label="Status", interactive=False)


    login_button.click(
        login,
        inputs=[username_input, password_input],
        outputs=[authenticated, user_info, login_output]
    ).then(
        update_all_buttons,
        inputs=[authenticated, user_info],
        outputs=[
            audio_transcription_button,
            keyword_manager_button,
            drift_app_button,
            error_analysis_button,
            circuit_monitoring_button,
            download_data_button,
            analytics_app_button
        ]
    )

demo.launch(server_name="0.0.0.0")