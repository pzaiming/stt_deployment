import gradio as gr
import pandas as pd
import os
from datetime import datetime
import re
import requests
import soundfile as sf

API_URL = os.getenv('API_URL', 'http://localhost:8000')
print(API_URL, '=======================')

shortcut_js = """
<script>
function getAudioElement(elemId) {
    let elem = document.querySelector('#' + elemId);
    if (elem) {
        let waveformDiv = elem.querySelector('#waveform');
        if (waveformDiv) {
            let childDiv = waveformDiv.querySelector('div');
            let shadowRoot = childDiv ? childDiv.shadowRoot : null;
            if (shadowRoot) {
                let audioElement = shadowRoot.querySelector('audio');
                return audioElement;
            }
        }
    }
    return null;
}

document.addEventListener("keyup", function (e) {
    if (e.key === "Escape") {
        const audioElement = getAudioElement("left_audio");
        if (audioElement) {
            // Get the current time of the audio
            const currentTime = audioElement.currentTime;
            console.log("Current audio time:", currentTime);
            navigator.clipboard.writeText(currentTime);
        } else {
            console.log("Audio element not found in shadow DOM.");
        }
    }
});

function setupKeyListeners() {
    window.addEventListener('keydown', (e) => {
        if (e.code.includes('Numpad')) {
            e.preventDefault();
        }
    });

    window.addEventListener('keyup', (e) => {
        var left_audio = getAudioElement('left_audio');
        var right_audio = getAudioElement('right_audio');
        var b_audio = getAudioElement('b_audio');

        if (e.code === 'Numpad4') {
            if (!b_audio.paused) {
                b_audio.currentTime -= 1;
                if (left_audio) left_audio.currentTime -= 1;
                if (right_audio) right_audio.currentTime -= 1;
            } else if (
                b_audio.paused &&
                (left_audio ? left_audio.paused : true) &&
                (right_audio ? right_audio.paused : true)
            ) {
                if (left_audio) left_audio.currentTime -= 1;
                if (right_audio) right_audio.currentTime -= 1;
                b_audio.currentTime -= 1;
            } else {
                if (left_audio && !left_audio.paused) {
                    left_audio.currentTime -= 1;
                }
                if (right_audio && !right_audio.paused) {
                    right_audio.currentTime -= 1;
                }
            }
            console.log('Rewind button triggered by Ctrl+Numpad4');
        } else if (e.code === 'Numpad6') {
            if (!b_audio.paused) {
                b_audio.currentTime += 1;
                if (left_audio) left_audio.currentTime += 1;
                if (right_audio) right_audio.currentTime += 1;
            } else if (
                b_audio.paused &&
                (left_audio ? left_audio.paused : true) &&
                (right_audio ? right_audio.paused : true)
            ) {
                if (left_audio) left_audio.currentTime += 1;
                if (right_audio) right_audio.currentTime += 1;
                b_audio.currentTime += 1;
            } else {
                if (left_audio && !left_audio.paused) {
                    left_audio.currentTime += 1;
                }
                if (right_audio && !right_audio.paused) {
                    right_audio.currentTime += 1;
                }
            }
            console.log('Skip button triggered by Ctrl+Numpad6');
        } else if (e.code === 'Numpad5') {
            if (b_audio.paused) {
                b_audio.play();
                if (left_audio) left_audio.pause();
                if (right_audio) right_audio.pause();

                if (left_audio) left_audio.currentTime = b_audio.currentTime;
                if (right_audio) right_audio.currentTime = b_audio.currentTime;
            } else {
                b_audio.pause();
                if (left_audio) left_audio.currentTime = b_audio.currentTime;
                if (right_audio) right_audio.currentTime = b_audio.currentTime;
            }
            console.log('Play button triggered by Ctrl+Numpad5');
        } else if (e.code === 'Numpad1') {
            if (left_audio) {
                if (left_audio.paused) {
                    left_audio.play();
                    if (right_audio) right_audio.pause();
                    b_audio.pause();
                } else {
                    left_audio.pause();
                }
            }
        } else if (e.code === 'Numpad3') {
            if (right_audio) {
                if (right_audio.paused) {
                    right_audio.play();
                    if (left_audio) left_audio.pause();
                    b_audio.pause();
                } else {
                    right_audio.pause();
                }
            }
        } else if (e.code === 'Numpad0') {
            document.getElementById("filterbutton").click();
            console.log('Filter button triggered by Ctrl+Numpad0');
        } else if (e.code === 'NumpadDivide') {
            document.getElementById("prevbutton").click();
            console.log('Prev button triggered by Ctrl+NumpadDivide');
        } else if (e.code === 'NumpadMultiply') {
            document.getElementById("nextbutton").click();
            console.log('Next button triggered by Ctrl+NumpadMultiply');
        }
    });
    console.log('Key listeners set up');
}

// Call the function to set up the listeners
setupKeyListeners();


function disablePropagation(){
    const observer = new MutationObserver((mutations, obs) => {
        const textareas = document.querySelectorAll('textarea[data-testid="textbox"]');
        
        // If text areas are found, apply the event listener and stop observing
        if (textareas.length > 0) {
            textareas.forEach((textarea) => {
                textarea.addEventListener('keydown', function(event) {
                    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
                        event.stopPropagation();
                    }
                });
            });
            obs.disconnect(); // Stop observing after applying listeners
        }
    });

    // Start observing the document for added nodes
    observer.observe(document, { childList: true, subtree: true });
}

// Execute the function immediately
disablePropagation();

function shortcuts(e) {
}
document.addEventListener('keyup', shortcuts, false);

function audioSync() {
    const b_audio = getAudioElement('b_audio');
    
    if (!b_audio) {
        console.log('b_audio not found');
        return;
    }

    const left_audio = getAudioElement('left_audio');
    const right_audio = getAudioElement('right_audio');

    if (b_audio.syncListenerAdded) {
        b_audio.removeEventListener('play', b_audio.syncOnPlay);
        b_audio.removeEventListener('pause', b_audio.syncOnPause);
        b_audio.removeEventListener('ended', b_audio.syncOnPause);
        b_audio.syncListenerAdded = false;
    }
    
    function syncAudioTime() {
        if (!b_audio.paused) {
            if (left_audio) {
                left_audio.currentTime = b_audio.currentTime;
            }
            if (right_audio) {
                right_audio.currentTime = b_audio.currentTime;
            }
        }
    }
    
    function startSync() {
        b_audio.addEventListener('timeupdate', syncAudioTime);
    }
    
    function stopSync() {
        b_audio.removeEventListener('timeupdate', syncAudioTime);
    }
    
    b_audio.syncOnPlay = startSync;
    b_audio.syncOnPause = stopSync;
    
    b_audio.addEventListener('play', startSync);
    b_audio.addEventListener('pause', stopSync);
    b_audio.addEventListener('ended', stopSync);
    
    if (!b_audio.paused) {
        startSync();
    }

    b_audio.syncListenerAdded = true;

    function syncOnSeeked() {
        if (left_audio) {
            left_audio.currentTime = b_audio.currentTime;
        }
        if (right_audio) {
            right_audio.currentTime = b_audio.currentTime;
        }
    }

    if (!b_audio.seekedListenerAdded) {
        b_audio.addEventListener('seeked', syncOnSeeked);
        b_audio.seekedListenerAdded = true;
    }
}

function startObserving(target) {
    const observer = new MutationObserver(audioSync);
    const config = { attributes: true, childList: true, subtree: true };
    observer.observe(target, config);
}

const intervalId = setInterval(() => {
    const targetNode = document.getElementById('audios');
    if (targetNode) {
        startObserving(targetNode);
        clearInterval(intervalId);
    }
}, 100);
</script>
"""

def login(request: gr.Request):
    params = str(request.query_params).split('&')
    result_json = {}

    for i in range(len(params)):
        if '=' in params[i]:
            key, value = params[i].split('=')
            result_json[key] = value

    return result_json.get('u', None), result_json.get('p', None)

def add_user_data(base_url, circuit, audio_file_path, file_name, duration, stt_transcript, gt_transcript,
                operator_remark, start_time, src, dst, m_plan, u, p):
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
    response = requests.post(f"{base_url}/add_user_data/", json=data, params={"user": u, "password": p})
    if response.status_code == 200:
        return response.json()
    
def get_filtered_user_data(base_url, circuit=None, operator_remark_contains=None, src=None, dst=None, start_time=None, end_time=None, bookmark=None, mplan=None, u=None, p=None):
    params = {
        "circuit": circuit,
        "operator_remark_contains": operator_remark_contains,
        "src": src,
        "dst": dst,
        "start_time": start_time,
        "end_time": end_time,
        "bookmark": bookmark,
        "mplan": mplan,
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

def update_user_data_partial(base_url, circuit, start_time, file_name, data, u=None, p=None):
    url = f"{base_url}/update_user_data_partial/"
    params = {"circuit": circuit, "start_time": start_time, "file_name": file_name, 'user': u, 'password': p}
    response = requests.patch(url, json=data, params=params)
    return response.json()

def get_all_keywords(base_url, u, p):
    response = requests.get(f"{base_url}/get_all_keywords/", params={'user': u, 'password': p})
    return response.json()

def get_dropdown_values(u, p):
    try:
        circuit = get_unique_values(base_url=API_URL,column='circuit', u=u, p=p)['unique_values']
        src = get_unique_values(base_url=API_URL,column='src', u=u, p=p)['unique_values']
        dst = get_unique_values(base_url=API_URL,column='dst', u=u, p=p)['unique_values']
        circuit.insert(0,'empty')
        src.insert(0,'empty')
        dst.insert(0,'empty')
    except:
        print('Database is empty')
        circuit, src, dst = ['empty'], ['empty'], ['empty']

    return circuit, src, dst

def edit_transcript(edit_text_area_value, left_edit_text_area_value, right_edit_text_area_value, primary_key, u, p):
    # Determine if stereo
    if primary_key['stereo']:
        # stereo == True
        # Get left and right texts
        left_text = left_edit_text_area_value
        right_text = right_edit_text_area_value
        # Add back 'L ' and 'R ' prefixes
        left_lines = left_text.strip().split('\n')
        right_lines = right_text.strip().split('\n')
        left_lines_prefixed = ['L ' + line.strip() for line in left_lines if line.strip()]
        right_lines_prefixed = ['R ' + line.strip() for line in right_lines if line.strip()]
        # Combine the lines
        combined_lines = left_lines_prefixed + right_lines_prefixed
    else:
        # stereo == False
        # Get text from edit_text_area_value
        text = edit_text_area_value
        # Add back 'B ' prefix
        lines = text.strip().split('\n')
        combined_lines = ['B ' + line.strip() for line in lines if line.strip()]

    # Now, sort the combined lines by the first time in each line
    # Assuming each line has the format: 'L start_time end_time text', we need to extract start_time

    def get_start_time(line):
        parts = line.split()
        if len(parts) >= 3:
            try:
                return float(parts[1])
            except ValueError:
                return float('inf')
        else:
            return float('inf')

    combined_lines.sort(key=get_start_time)
    # Reconstruct the transcript
    new_transcript = '\n'.join(combined_lines)
    # Post to DB
    print(primary_key)
    response = update_user_data_partial(API_URL, primary_key['circuit'], primary_key['start_time'], primary_key['file_name'], {'gt_transcript': f'{new_transcript}'}, u, p)
    print(response)
    gr.Info('Edit transcript submitted')

    # Return highlight text to highlight
    df = get_keyword(u, p)
    print(df)
    if df.empty:
        return [(new_transcript, None)]
    
    else:
        priority_one_list = df.loc[df['priority_'] == 1, 'keyword'].tolist()
        priority_two_list = df.loc[df['priority_'] == 2, 'keyword'].tolist()
        highlight_text = str_to_keyword_transcript(new_transcript, priority_one_list, priority_two_list)
    return gr.Highlight(value=highlight_text)

def str_to_keyword_transcript(sentence='hello this is a test', keyword1=['hello'], keyword2=['test']):
    sentence = sentence.lower()
    tokens = re.findall(r'\w+|\s+|[^\w\s]+', sentence)
    highlighted_words = []
    
    for token in tokens:
        symbol = None
        if re.match(r'\w+', token):
            if token in keyword1:
                symbol = 'Priority 1'
            elif token in keyword2:
                symbol = 'Priority 2'
        highlighted_words.append((token, symbol))
    return highlighted_words

def dataframe_to_keyword_transcript(df):
    df = df.sort_values(by='priority_')
    highlighted_words = [
    (row['keyword'] + '\n', 'Priority 1' if row['priority_'] == 1 else 'Priority 2' if row['priority_'] == 2 else None)
    for _, row in df.iterrows()
    ]
    return highlighted_words

def get_keyword(u, p):
    keywords = get_all_keywords(base_url=API_URL, u=u, p=p)
    df = pd.DataFrame()
    if 'data' in keywords and keywords['data']:
        df = pd.DataFrame(keywords['data'])
    return df

def get_keyword_highlight(u = None, p = None):
    if u is None or p is None or isinstance(u, gr.components.State) or isinstance(p, gr.components.State):
        return [('No User or Password', 'Priority 1')]
    df = get_keyword(u, p)
    if df.empty:
        return [('No Keyword in Database','Priority 1')]
    else:
        highlighted_text = dataframe_to_keyword_transcript(df)  
        print(highlighted_text, 'ticker is running')  
        return highlighted_text

def split_to_mono(file_path):
    data, sample_rate = sf.read(file_path)
    if data.ndim != 2 or data.shape[1] != 2:
        raise ValueError("The audio file must be stereo (2 channels)")
    
    left_channel = data[:, 0]
    right_channel = data[:, 1]
    
    return (sample_rate, data), (sample_rate, left_channel), (sample_rate, right_channel)

def update_audio_files(row_selected):
    audio_file_path = row_selected['audio_file_path']
    print(row_selected)
    stereo = row_selected.get('stereo', False)

    if stereo == True:
        both_audio, left_audio, right_audio = split_to_mono(audio_file_path)
        return gr.Audio(both_audio), gr.Audio(value=left_audio, visible=True), gr.Audio(value=right_audio, visible=True)
    else:
        return gr.Audio(audio_file_path), gr.Audio(value=audio_file_path, visible=False), gr.update(value=None, visible=False)


with gr.Blocks(title='Audio Transcription App',theme=gr.themes.Soft(), fill_width=False, head=shortcut_js) as demo:
    keyword_transcript = gr.State([])
    multi_keyword_transcript = gr.State({})
    edit_transcript_text = gr.State([])
    row_selected = gr.State({}) 
    current_index = gr.State(0)
    data_gr_dataframe = gr.State(pd.DataFrame())
    
    circuit_val, src_val, dst_val = gr.State(), gr.State(), gr.State()
    
    ### USER LOGIN
    u = gr.State()
    p = gr.State()

    def auth(user):
        if user.lower()=='editor':
            return gr.Audio(visible=True), gr.Tab(visible=True)
        else:
            return gr.Audio(visible=False), gr.Tab(visible=False)
    
    with gr.Row():
        with gr.Column():
            gr.Markdown('# AILAB - OTTERSPHERE')
        with gr.Group():
            with gr.Column():
                username_box = gr.Textbox(label='User', placeholder='Please provide username to unlock edit feature')
            with gr.Column():
                user_login = gr.Button('Submit', variant='huggingface')

    ### FILTER ACCORDIAN
    # circuit_val, src_val, dst_val = get_dropdown_values(u ,p)

    with gr.Accordion("Filter Audio"):
        with gr.Row():
            with gr.Column():
                # circuit_dropdown = gr.Dropdown(label='Circuit', choices=circuit_val, interactive=True, value=circuit_val[0])
                circuit_dropdown = gr.Dropdown(label='Circuit', interactive=True)
            with gr.Column():
                operator_textbox = gr.Textbox(label='Operator Remark', placeholder="Find remarks with this word")
            with gr.Column():
                start_time_textbox = gr.DateTime(label='Start Time', info='eg. 2017-01-05 17:52:30', timezone='Asia/Singapore')
            with gr.Column():
                end_time_textbox = gr.DateTime(label='End Time', info="If only Start Time, then get until live", timezone='Asia/Singapore')
        with gr.Row():
            with gr.Column():
                gr.Textbox(label='Filename')
            with gr.Column():
                source_dropdown = gr.Dropdown(label='Src', interactive=True)
                # source_dropdown = gr.Dropdown(label='Src', choices=src_val, interactive=True)
            with gr.Column():
                dst_dropdown = gr.Dropdown(label='Dst', interactive=True)
                # dst_dropdown = gr.Dropdown(label='Dst', choices=dst_val, interactive=True)
            with gr.Column():
                filter_checkbox = gr.Checkbox(label='Bookmark')
                mplan_checkbox = gr.Checkbox(label='mplan')
        with gr.Row():
            with gr.Column(): 
                filter_button = gr.Button(value='Filter (Press 0)', elem_id='filterbutton', variant='primary')
        
        with gr.Row():
            full_df_state = gr.Dataframe(label='Files retrieved', value=[['Press Filter Button']])

        def refresh_dropdown(u, p):
            circuit_val, src_val, dst_val = get_dropdown_values(u, p)
            convert_dropdown = lambda x: gr.Dropdown(choices=x, interactive=True)
            return convert_dropdown(circuit_val), convert_dropdown(src_val), convert_dropdown(dst_val)

        def get_filter_data(circuit, operator_remark_contains, src, dst, start_time, end_time, checkbox, mplan_checkbox, u, p):
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            elif isinstance(start_time, float):
                start_time = datetime.fromtimestamp(start_time)

            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            elif isinstance(end_time, float):
                end_time = datetime.fromtimestamp(end_time)
                
            circuit=None if circuit=='empty' else circuit
            src=None if src=='empty' else src
            dst=None if dst=='empty' else dst
            print(checkbox)
            checkbox='True' if checkbox else None
            mplan_checkbox='True' if mplan_checkbox else None


            data = get_filtered_user_data(base_url=API_URL,
                                        circuit=circuit,
                                        operator_remark_contains=operator_remark_contains,
                                        src=src,
                                        dst=dst,
                                        start_time=start_time,
                                        end_time=end_time,
                                        bookmark=checkbox,
                                        mplan=mplan_checkbox,
                                        u=u,
                                        p=p
                                        )
            
            if 'data' in data and data['data']:
                df = pd.DataFrame(data['data'])
                filtered_df = df.drop(['start_year', 'start_month', 'start_day', 'start_hour', 'start_minute', 'start_second'], axis=1)
                columns_titles = ['circuit', 'src', 'dst', 'file_name', 'duration', 'stt_transcript', 'gt_transcript', 'operator_remark', 'start_time', 'last_modified', 'bookmark', 'mplan', 'audio_file_path', 'stereo']
                reindex_df = filtered_df.reindex(columns=columns_titles)
                if not reindex_df.empty:
                    first_row = reindex_df.iloc[[0]]
                else:
                    first_row = pd.DataFrame()
                return first_row, reindex_df, 0, get_highlight_overview_text(reindex_df, u, p, use_mixed_transcript=True), get_highlight_overview_text(reindex_df, u, p, use_mixed_transcript=False)
            else:
                return pd.DataFrame(), pd.DataFrame(), 0, [()], [()]

        def on_row_select(evt: gr.SelectData, full_dataframe):
            selected_row = evt.index[0]
            if selected_row is not None and not full_dataframe.empty:
                selected_data = full_dataframe.iloc[[selected_row]]
            else:
                selected_data = pd.DataFrame()
            return selected_data, selected_row

        def on_change(cached_df, u, p):
            if cached_df.empty:
                return None, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), None
            row_df = cached_df.iloc[0]
            transcription_data = row_df[['stt_transcript', 'gt_transcript']]
            primary_key  = {
                'circuit': row_df['circuit'],
                'file_name': row_df['file_name'], 
                'start_time': row_df['start_time'],
                'operator_remark': row_df['operator_remark'],
                'audio_file_path': row_df['audio_file_path'],
                'stereo': row_df['stereo']
            } 
            transcription_data_dict = transcription_data.to_dict()
            df = get_keyword(u, p)

            if df.empty:
                priority_one_list = []
                priority_two_list = []
            else:
                priority_one_list = df.loc[df['priority_'] == 1, 'keyword'].tolist()
                priority_two_list = df.loc[df['priority_'] == 2, 'keyword'].tolist()

            if transcription_data_dict['gt_transcript'] != "" and transcription_data_dict['gt_transcript'] is not None:
                text = transcription_data_dict['gt_transcript']
            else: 
                text = transcription_data_dict['stt_transcript']

            # Now, process the text depending on stereo
            if primary_key['stereo']:
                # stereo == True
                # Split the text into left and right transcripts
                left_lines = []
                right_lines = []
                for line in text.strip().split('\n'):
                    line = line.strip()
                    if line.startswith('L '):
                        left_lines.append(line[2:].strip())  # Remove 'L ' prefix
                    elif line.startswith('R '):
                        right_lines.append(line[2:].strip())  # Remove 'R ' prefix
                    else:
                        pass  # Skip lines not starting with 'L ' or 'R '
                left_text = '\n'.join(left_lines)
                right_text = '\n'.join(right_lines)
                # Update visibility: edit_text_area visible=False, left_edit_text_area and right_edit_text_area visible=True
                edit_text_area_update = gr.update(visible=False)
                left_edit_text_area_update = gr.update(visible=True, value=left_text)
                right_edit_text_area_update = gr.update(visible=True, value=right_text)
            else:
                # stereo == False
                # Remove the first character 'B ' (if present)
                lines = []
                for line in text.strip().split('\n'):
                    line = line.strip()
                    if line.startswith('B '):
                        lines.append(line[2:].strip())  # Remove 'B ' prefix
                    else:
                        lines.append(line.strip())
                edited_text = '\n'.join(lines)
                # Update visibility: edit_text_area visible=True, left and right text areas visible=False
                edit_text_area_update = gr.update(visible=True, value=edited_text)
                left_edit_text_area_update = gr.update(visible=False)
                right_edit_text_area_update = gr.update(visible=False)

            # Prepare highlighted transcript (for keyword_transcript)
            if df.empty:
                priority_one_list = []
                priority_two_list = []
            else:
                priority_one_list = df.loc[df['priority_'] == 1, 'keyword'].tolist()
                priority_two_list = df.loc[df['priority_'] == 2, 'keyword'].tolist()

            # For the highlighted transcript, we need to process appropriately
            transcript = str_to_keyword_transcript(text, priority_one_list, priority_two_list)

            return transcript, edit_text_area_update, left_edit_text_area_update, right_edit_text_area_update, primary_key

        def show_row(full_df, index):
            if full_df.empty:
                return pd.DataFrame(), index
            row = full_df.iloc[[index]]
            return row, index

        def navigate(full_df, index, direction):
            if full_df.empty:
                return gr.update(), index
            if direction == 'next':
                index = (index + 1) % len(full_df)
            elif direction == 'prev':
                index = (index - 1) % len(full_df)
            row = full_df.iloc[[index]]
            return row, index

        gr.Timer(value=10).tick(fn=refresh_dropdown, inputs=[u, p], outputs=[circuit_dropdown, source_dropdown, dst_dropdown])    

    ### AUDIO TRANSCRIPT
    highlighted_text = get_keyword_highlight(u, p)
    print(highlighted_text)
    if not isinstance(highlighted_text, list):
        highlighted_text = [('Invalid data', None)]
    keyword_state = gr.State(value=highlighted_text)

    audio_file = './audio/start.wav'
    sentence = [('Nothing Selected', 'Priority 1')]

    with gr.Row():
        with gr.Column(scale=20):
            with gr.Group(elem_id='audios', visible=False) as audios:
                audio = gr.Audio(value=audio_file, editable=False, visible=True, elem_id='b_audio', label='B')
                with gr.Row():
                    audio_l = gr.Audio(value=audio_file, editable=False, visible=False, elem_id='left_audio', label='L')
                    audio_r = gr.Audio(value=audio_file, editable=False, visible=False, elem_id='right_audio', label='R')

            with gr.Tabs() as tabs:
                with gr.TabItem('Transcript Overview (Mixed)'):
                    with gr.Row():
                        with gr.Column(scale=2):
                            keyword_transcript_text_overview = gr.HighlightedText(
                                value=sentence,
                                label="Transcript",
                                combine_adjacent=True,
                                show_legend=True,
                                color_map={"Priority 1": "red", "Priority 2": "purple"})
                        
                        with gr.Column(scale=1):
                            keywords_text1 = gr.HighlightedText(
                                value=highlighted_text,
                                label="Keyword",
                                combine_adjacent=True,
                                show_legend=True,
                                color_map={"Priority 1": "red", "Priority 2": "purple"})
                
                with gr.TabItem('Transcript Overview (only GT)'):
                    with gr.Row():
                        with gr.Column(scale=2):
                            keyword_transcript_text_overview_gt = gr.HighlightedText(
                                value=sentence,
                                label="Transcript",
                                combine_adjacent=True,
                                show_legend=True,
                                color_map={"Priority 1": "red", "Priority 2": "purple"})
                        
                        with gr.Column(scale=1):
                            keywords_text2 = gr.HighlightedText(
                                value=highlighted_text,
                                label="Keyword",
                                combine_adjacent=True,
                                show_legend=True,
                                color_map={"Priority 1": "red", "Priority 2": "purple"})

                edit_tab = gr.TabItem('Edit Transcript', visible=False)
                with edit_tab:
                    with gr.Row():
                        prev_button_2 = gr.Button(value='Prev', variant='secondary')
                        next_button_2 = gr.Button(value='Next', variant='secondary')
                    with gr.Row():
                        edit_text_area = gr.TextArea(value='nothing selected', interactive=True, visible=True, label='Transcript')
                        left_edit_text_area = gr.TextArea(value='nothing selected', interactive=True, visible=False, label='Transcript Left')
                        right_edit_text_area = gr.TextArea(value='nothing selected', interactive=True, visible=False, label='Transcript Right')
                    submit_edit_button = gr.Button(value='Submit Changes', variant='primary')
                    next_button_2.click(fn=lambda df, idx: navigate(df, idx, 'next'), inputs=[full_df_state, current_index], outputs=[data_gr_dataframe, current_index])
                    prev_button_2.click(fn=lambda df, idx: navigate(df, idx, 'prev'), inputs=[full_df_state, current_index], outputs=[data_gr_dataframe, current_index])

                with gr.TabItem('Transcript Single'):
                    with gr.Row():
                        prev_button = gr.Button(value='Prev', variant='secondary', elem_id='prevbutton')
                        next_button = gr.Button(value='Next', variant='secondary', elem_id='nextbutton')
                    with gr.Row():
                        with gr.Column(scale=2):
                            keyword_transcript_text = gr.HighlightedText(
                                value=sentence,
                                label="Transcript",
                                combine_adjacent=True,
                                show_legend=True,
                                color_map={"Priority 1": "red", "Priority 2": "purple"})
                        
                        with gr.Column(scale=1):
                            keywords_text = gr.HighlightedText(
                                value=highlighted_text,
                                label="Keyword",
                                combine_adjacent=True,
                                show_legend=True,
                                color_map={"Priority 1": "red", "Priority 2": "purple"})
                    
                    submit_edit_button.click(fn=edit_transcript, inputs=[edit_text_area, left_edit_text_area, right_edit_text_area, row_selected, u, p], outputs=keyword_transcript_text)
                    full_df_state.select(fn=on_row_select, inputs=full_df_state, outputs=[data_gr_dataframe, current_index])
                    data_gr_dataframe.change(fn=on_change, inputs=[data_gr_dataframe, u, p], outputs=[keyword_transcript, edit_text_area, left_edit_text_area, right_edit_text_area, row_selected])


                    next_button.click(fn=lambda df, idx: navigate(df, idx, 'next'), inputs=[full_df_state, current_index], outputs=[data_gr_dataframe, current_index])
                    prev_button.click(fn=lambda df, idx: navigate(df, idx, 'prev'), inputs=[full_df_state, current_index], outputs=[data_gr_dataframe, current_index])

        def get_highlight_overview_text(df, u, p, use_mixed_transcript=False):
            key_df = get_keyword(u, p)
            
            if key_df.empty:
                priority_one_list, priority_two_list = [], [] 
                return [('Nothing has been returned', None)]
            else:
                priority_one_list = key_df.loc[key_df['priority_'] == 1, 'keyword'].tolist()
                priority_two_list = key_df.loc[key_df['priority_'] == 2, 'keyword'].tolist()
                try:
                    df = df.sort_values(by='start_time')
                except:
                    return [('Nothing Selected', None)]

                    
            transcript_tuples = []
            for _, row in df.iterrows():
                transcription_type = ''


                if row['gt_transcript'] and not pd.isna(row['gt_transcript']):
                    filename = str(row['file_name'])
                    transcript_tuples.append((filename, None))
                    transcript_tuples.append(('User Editted\n', '1'))
                    transcript = row['gt_transcript']
                elif use_mixed_transcript and row['stt_transcript'] and not pd.isna(row['stt_transcript']):
                    filename = str(row['file_name'])
                    transcript_tuples.append((filename, None))
                    transcript_tuples.append(('STT generated\n', '2'))
                    transcript = row['stt_transcript']
                else:
                    transcript = None
                
                if transcript:
                    highlighted_transcript = str_to_keyword_transcript(
                        transcript, priority_one_list, priority_two_list
                    )
                    transcript_tuples.extend(highlighted_transcript)

                if transcript_tuples[-1][0] != '\n':
                    transcript_tuples.extend([('\n', None), ('\n', None)])
                elif transcript_tuples[-1][0] == '\n' and transcript_tuples[-2][0] != '\n':
                    transcript_tuples.append(('\n', None))

            return transcript_tuples

        keyword_timer = gr.Timer(value=10, active=True).tick(fn=get_keyword_highlight, inputs=[u, p], outputs=keyword_state)    
        keyword_transcript.change(fn=lambda x:x, inputs=keyword_transcript, outputs=keyword_transcript_text)
        edit_transcript_text.change(fn=lambda x:x, inputs=edit_transcript_text, outputs=[edit_text_area, left_edit_text_area, right_edit_text_area])

        keyword_state.change(fn=lambda x:[gr.HighlightedText(value=x), gr.HighlightedText(value=x), gr.HighlightedText(value=x)], inputs=keyword_state, outputs=[keywords_text, keywords_text1, keywords_text2])
        row_selected.change(fn=update_audio_files, inputs=row_selected, outputs=[audio, audio_l, audio_r])

        user_login.click(fn=auth, inputs=username_box, outputs=[audios, edit_tab])
        filter_button.click(fn=get_filter_data, inputs=[circuit_dropdown, operator_textbox, source_dropdown, dst_dropdown, start_time_textbox, end_time_textbox, filter_checkbox, mplan_checkbox, u, p], outputs=[data_gr_dataframe, full_df_state, current_index, keyword_transcript_text_overview,  keyword_transcript_text_overview_gt])

    ### OPERATOR FEATURES
    def operator_remark_update(text, primary_key={'circuit': 'test', 'start_time': 'test', 'file_name': 'test'}, u=None, p=None):
        response = update_user_data_partial(API_URL, primary_key['circuit'], primary_key['start_time'], primary_key['file_name'], {'operator_remark': f'{text}'}, u, p )
        gr.Info('Operator Remark Saved submitted')

    def bookmark_update(check, primary_key={'circuit': 'test', 'start_time': 'test', 'file_name': 'test'}, u=None, p=None):
        response = update_user_data_partial(API_URL, primary_key['circuit'], primary_key['start_time'], primary_key['file_name'], {'bookmark': f'{check}'}, u, p )
        file_name = primary_key['file_name'] 
        gr.Info(f'{file_name} has been bookmarked')
    
    with gr.Group():
        operator_text_area = gr.TextArea(label='Operator Remark', placeholder='Submit Remark', interactive=True)
        
        with gr.Row():
            operator_submit_button = gr.Button(value='Submit Remark', variant='primary')
            bookmark_checkbox = gr.Checkbox(value=False, label='Bookmark', info='Click Checkbox to Bookmark')

        operator_submit_button.click(fn=operator_remark_update, inputs=[operator_text_area, row_selected, u, p])
        row_selected.change(fn=lambda x: x['operator_remark'], inputs=row_selected, outputs=operator_text_area)
        
        bookmark_checkbox.change(fn=bookmark_update, inputs=[bookmark_checkbox, row_selected, u, p])
    
    demo.load(fn=login, outputs=[u, p]).then(refresh_dropdown, inputs=[u, p], outputs=[circuit_dropdown, source_dropdown, dst_dropdown])

    demo.launch(server_name="0.0.0.0", share=True, allowed_paths=['/app/output', '/app/audio', './audio', '/audio', './output', '/app/input', './input', '/tmp'])