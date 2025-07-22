import requests

OAUTH_TOKEN = "oauth_token"
ORG_ID = "org_id"
TARGET_ENDPOINT = "https://api.tracker.yandex.net/v3/issues/"  

headers = {
    "Authorization": f"OAuth {OAUTH_TOKEN}",
    "X-Cloud-Org-ID": ORG_ID,
    "Content-Type": "application/json"
}

def get_all_queues():
    response = requests.get(
        "https://api.tracker.yandex.net/v3/queues?perPage=1000",
        headers=headers
    )
    return [q['key'] for q in response.json()]

def get_queue_triggers(queue_key):
    try:
        response = requests.get(
            f"https://api.tracker.yandex.net/v3/queues/{queue_key}/triggers",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 403:
            print(f"Нет доступа к очереди или она была удалена: {queue_key}")
            return None
            
        if response.status_code != 200:
            print(f"Ошибка {response.status_code} для очереди {queue_key}")
            return None
            
        return response.json()
        
    except Exception as e:
        print(f"Ошибка запроса: {queue_key} - {str(e)}")
        return None

def check_trigger_actions(trigger):
    if not isinstance(trigger, dict):
        return False
        
    if not trigger.get('active', False):
        return False

    actions = trigger.get('actions', [])
    for action in actions:
        if action.get('type') == 'Webhook' and action.get('endpoint') == TARGET_ENDPOINT:
            return True
    return False

def find_triggers_by_endpoint():
    queues = get_all_queues()
    found_in = []
    
    print(f"Проверяем {len(queues)} очередей...")
    
    for queue in queues:
        triggers = get_queue_triggers(queue)
        if not triggers:
            continue
            
        for trigger in triggers:
            if check_trigger_actions(trigger):
                found_in.append({
                    'queue': queue,
                    'trigger_id': trigger.get('id'),
                    'trigger_name': trigger.get('name')
                })
                print(f"Найден в очереди {queue} (ID: {trigger.get('id')}, Name: {trigger.get('name')})")
    
    print("\nРезультаты поиска:")
    if found_in:
        for item in found_in:
            print(f"• Очередь: {item['queue']} | Триггер: {item['trigger_name']} (ID: {item['trigger_id']})")
    else:
        print("Активные триггеры с указанным адресом запроса не найдены")
    
    return found_in

find_triggers_by_endpoint()