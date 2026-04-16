# Гайд по Deep Links для Telegram Бота

## Обзор
Deep links позволяют открывать Telegram бота напрямую в определённом разделе или с предустановленными параметрами при переходе с сайта или других источников. Это улучшает пользовательский опыт, интегрируя сайт и бота.

## Как работают Deep Links в Telegram
- **Формат ссылки**: `https://t.me/{bot_username}?start={payload}`
- **Payload**: Произвольная строка (до 64 символов), передаваемая в бота при старте.
- **Обработка**: В хендлере `/start` парсится параметр `start` и выполняется соответствующая логика.

## Текущая реализация в коде
В `src/handlers/user.py` функция `cmd_start` обрабатывает deep links:

```python
@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    # ... регистрация пользователя ...
    
    # Обработка deep link payload
    if command.args:
        payload = command.args.strip()
        if payload.startswith('ref_'):
            # Реферальная ссылка
            referrer_id = int(payload[4:])
            # ... логика реферала ...
        elif payload == 'daily_stone':
            # Переход к камню дня
            await show_daily_stone(message, state)
        elif payload == 'knowledge':
            # Переход к базе знаний
            await show_knowledge(message, state)
        elif payload.startswith('stone_'):
            # Переход к конкретному камню
            stone_name = payload[7:]
            await show_stone_info(message, stone_name, state)
        elif payload == 'compatibility':
            # Переход к совместимости
            await show_compatibility(message, state)
        elif payload == 'diagnostic':
            # Переход к диагностике
            await show_diagnostic(message, state)
        elif payload == 'services':
            # Переход к услугам
            await show_services(message, state)
        elif payload == 'shop':
            # Переход к витрине
            await show_showcase(message, state)
        elif payload == 'profile':
            # Переход к профилю
            await show_profile(message, state)
        else:
            # Неизвестный payload - показать главное меню
            await show_main_menu(message, state)
    else:
        # Обычный старт - показать главное меню
        await show_main_menu(message, state)
```

## Примеры Deep Links
### 1. Переход к камню дня
- **Ссылка**: `https://t.me/your_bot_username?start=daily_stone`
- **Действие**: Показывает информацию о камне дня.

### 2. Переход к базе знаний
- **Ссылка**: `https://t.me/your_bot_username?start=knowledge`
- **Действие**: Открывает раздел базы знаний.

### 3. Переход к конкретному камню
- **Ссылка**: `https://t.me/your_bot_username?start=stone_amethyst`
- **Действие**: Показывает информацию об аметисте.

### 4. Переход к совместимости
- **Ссылка**: `https://t.me/your_bot_username?start=compatibility`
- **Действие**: Открывает раздел совместимости камней.

### 5. Переход к диагностике
- **Ссылка**: `https://t.me/your_bot_username?start=diagnostic`
- **Действие**: Начинает диагностику.

### 6. Переход к услугам
- **Ссылка**: `https://t.me/your_bot_username?start=services`
- **Действие**: Показывает доступные услуги.

### 7. Переход к витрине
- **Ссылка**: `https://t.me/your_bot_username?start=shop`
- **Действие**: Открывает витрину товаров.

### 8. Переход к профилю
- **Ссылка**: `https://t.me/your_bot_username?start=profile`
- **Действие**: Показывает пользовательский профиль.

### 9. Реферальная ссылка
- **Ссылка**: `https://t.me/your_bot_username?start=ref_12345`
- **Действие**: Привязывает реферала к пользователю 12345.

## Интеграция с сайтом
### Добавление кнопок на сайт
На сайте `magic-stone.org` добавьте кнопки с deep links:

```html
<!-- Кнопка "Открыть в боте" для камня дня -->
<a href="https://t.me/your_bot_username?start=daily_stone" target="_blank">
    <button>Открыть камень дня в боте</button>
</a>

<!-- Кнопка для конкретного камня -->
<a href="https://t.me/your_bot_username?start=stone_amethyst" target="_blank">
    <button>Узнать больше об аметисте в боте</button>
</a>

<!-- Кнопка для базы знаний -->
<a href="https://t.me/your_bot_username?start=knowledge" target="_blank">
    <button>Посмотреть базу знаний в боте</button>
</a>
```

### JavaScript для динамических ссылок
```javascript
function openInBot(payload) {
    const botUsername = 'your_bot_username';
    const url = `https://t.me/${botUsername}?start=${payload}`;
    window.open(url, '_blank');
}

// Пример использования
openInBot('stone_amethyst');
```

## Расширение функционала
### Добавление новых payload
1. Добавьте обработку в `cmd_start`:
```python
elif payload == 'new_feature':
    await show_new_feature(message, state)
```

2. Создайте соответствующую функцию `show_new_feature`.

3. Добавьте кнопку на сайт.

### Параметры в payload
Payload может содержать несколько параметров, разделённых подчёркиванием:
- `stone_amethyst_details` - камень + действие
- `category_1_page_2` - категория + страница

Парсите в коде:
```python
parts = payload.split('_')
if parts[0] == 'stone':
    stone_name = '_'.join(parts[1:])
    action = 'details'  # или parts[-1] если есть
```

## Тестирование
1. Создайте тестовую ссылку.
2. Откройте в браузере или Telegram.
3. Проверьте, что бот открывается в правильном разделе.
4. Тестируйте на разных устройствах.

## Ограничения
- Payload до 64 символов.
- Пользователь должен иметь Telegram установлен.
- Если бот не запущен, откроется чат с ботом, и пользователь должен нажать /start вручную.

## Рекомендации
- Используйте понятные payload (stone_name, feature_name).
- Добавляйте fallback для неизвестных payload.
- Логируйте использование deep links для аналитики.
- Обновляйте сайт при добавлении новых разделов в боте.