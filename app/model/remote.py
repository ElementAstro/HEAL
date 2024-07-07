import json
import requests
from app.model.config import get_json

def get_base_url(route_key: str) -> str:
    config_file = './config/config.json'
    server_url = get_json(config_file, 'SERVER_URL')
    route = get_json(config_file, route_key)
    return f'https://{server_url}{route}'

def handle_request(url: str, params: dict) -> tuple:
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        response_json = response.json()
        
        if response_json.get('retcode') == 200:
            return 'success', response_json.get('message', '')
        else:
            return 'error', response_json.get('message', 'Unknown error')

    except requests.exceptions.HTTPError as http_err:
        print(f'网络请求失败: {http_err}')
        return 'error', str(http_err)

    except requests.exceptions.RequestException as req_err:
        print(f'请求错误: {req_err}')
        return 'error', str(req_err)

    except Exception as err:
        print(f'未知错误: {err}')
        return 'error', str(err)

def handleApply(uid: str) -> tuple:
    base_url = get_base_url('ROUTE_APPLY')
    params = {'uid': uid}
    return handle_request(base_url, params)

def handleVerify(uid: str, code: str, key: str) -> tuple:
    base_url = get_base_url('ROUTE_VERIFY')
    params = {
        'uid': uid,
        'code': code,
        'password': key
    }
    return handle_request(base_url, params)

def handleCommandSend(uid: str, key: str, command: str) -> tuple:
    base_url = get_base_url('ROUTE_REMOTE')
    params = {
        'uid': uid,
        'key': key,
        'command': command
    }
    return handle_request(base_url, params)