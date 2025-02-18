class Config:
    RESPONSE_DELAY = (3, 6)  # Увеличены задержки
    MAX_MESSAGE_LENGTH = 300
    TEMPERATURE = 0.7  # Снижена случайность
    TOP_P = 0.85
    SAFETY_SETTINGS = {'HARASSMENT': 'BLOCK_NONE'}
    REQUEST_INTERVAL = 5  # 5 секунд между запросами
