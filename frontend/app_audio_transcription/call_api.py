

import requests

def add_user_data(base_url, circuit, audio_file_path, file_name, duration, stt_transcript, gt_transcript,
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
    response = requests.post(f"{base_url}/add_user_data/", json=data)
    if response.status_code == 200:
        return response.json()
    
def get_filtered_user_data(base_url, circuit=None, operator_remark_contains=None, src=None, dst=None, start_time=None, end_time=None, bookmark=None, mplan=None):
    params = {
        "circuit": circuit,
        "operator_remark_contains": operator_remark_contains,
        "src": src,
        "dst": dst,
        "start_time": start_time,
        "end_time": end_time,
        "bookmark": bookmark,
        "mplan": mplan
    }
    response = requests.get(f"{base_url}/filter_user_data/", params=params)
    return response.json()

def get_unique_values(base_url, column=None):
    params = {
        "column": column,
    }
    response = requests.get(f"{base_url}/unique_values/", params=params)
    return response.json()

def update_user_data_partial(base_url, circuit, start_time, file_name, data):
    url = f"{base_url}/update_user_data_partial/"
    params = {"circuit": circuit, "start_time": start_time, "file_name": file_name}
    response = requests.patch(url, json=data, params=params)
    return response.json()

def add_keyword(base_url, keyword, priority_, service_):
    url = f"{base_url}/add_keyword/"
    data = {"keyword": keyword, "priority_": priority_, "service_": service_}
    response = requests.post(url, json=data)
    return response.json()

def get_all_keywords(base_url):
    response = requests.get(f"{base_url}/get_all_keywords/")
    return response.json()

def delete_keyword(base_url, keyword, priority_, service_):
    url = f"{base_url}/delete_keyword/"
    params = {"keyword": keyword, "priority_": priority_, "service_": service_}
    response = requests.delete(url, params=params)
    return response.json()

