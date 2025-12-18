from datetime import datetime
from models import Policy

# Проверяет доступ пользователя к ресурсу по политикам из БД
def check_access(user, resource, client_ip=None):
    """
    Проверяет доступ пользователя к ресурсу
    """
    # 1. Статус аккаунта
    if user.account_status != 'active':
        return False, 'Аккаунт не активен'
    
    # 2. Уровень подписки
    if resource.access_level == 'premium' and user.subscription_level != 'premium':
        return False, 'Требуется premium подписка'
    
    # 3. Проверка времени (с учётом "всегда доступно")
    if resource.available_hours != '00:00-23:59':
        current_time = datetime.now().time()
        start_str, end_str = resource.available_hours.split('-')
        start = datetime.strptime(start_str, '%H:%M').time()
        end = datetime.strptime(end_str, '%H:%M').time()
        
        if not (start <= current_time <= end):
            return False, f'Ресурс доступен с {start_str} до {end_str}'
    
    return True, 'Доступ разрешён'