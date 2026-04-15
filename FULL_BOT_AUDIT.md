# ПОЛНЫЙ АУДИТ TELEGRAM БОТА MAGIC STONE

**Дата аудита:** 15 апреля 2026  
**Версия бота:** Текущая (main branch)  
**Язык:** Python + aiogram 3.x  
**База данных:** SQLite  

---

## 📊 ОБЩАЯ СТАТИСТИКА

| Метрика | Значение |
|---------|----------|
| **Обработчиков (handlers)** | 40+ файлов |
| **Клавиатур (keyboards)** | 17 файлов |
| **Состояний (FSM States)** | 40+ классов/состояний |
| **Таблиц БД** | 15+ (music, workouts, stones, users, etc.) |
| **Команд бота** | /start, /help, /admin |
| **Callback кнопок** | 50+ уникальных |

---

## 🎛️ СПИСОК ВСЕХ КНОПОК И CALLBACK_DATA

### ГЛАВНОЕ МЕНЮ (get_main_keyboard)
```
💎 ВИТРИНА          → callback_data="showcase"
🛒 КОРЗИНА          → callback_data="cart"
🔮 ПОДОБРАТЬ МОЙ КАМЕНЬ → callback_data="quiz"
🦊 ТОТЕМНЫЙ КАМЕНЬ  → callback_data="totem"
🗺 КАРТА ЖЕЛАНИЯ    → callback_data="wishmap"
🔮 СОВМЕСТИМОСТЬ КАМНЕЙ → callback_data="compatibility"
🔍 ПОИСК КАМНЯ      → callback_data="search_stones"
📚 БАЗА ЗНАНИЙ      → callback_data="knowledge"
🌅 КАМЕНЬ ДНЯ       → callback_data="daily_stone"
🩺 ДИАГНОСТИКА      → callback_data="diagnostic"
✨ УСЛУГИ           → callback_data="services"
💍 КАСТОМНЫЙ ЗАКАЗ  → callback_data="custom_order"
🔥 МОЙ СТРИК        → callback_data="streak"
🤖 СОВЕТ МАСТЕРА    → callback_data="ai_consult"
🏃 МАРАФОН 21 ДЕНЬ  → callback_data="marathon"
🌟 АСТРО-СОВЕТ      → callback_data="astro_advice"
👤 МОЙ ПРОФИЛЬ      → callback_data="profile"
🤝 РЕФЕРАЛЫ         → callback_data="referral"
🔮 ПОРТАЛ СИЛЫ      → callback_data="club"
🎁 СЕРТИФИКАТЫ      → callback_data="gifts"
🎵 МУЗЫКА           → callback_data="music"
🧘 ПРАКТИКИ         → callback_data="workouts"
❓ FAQ              → callback_data="faq"
📞 СВЯЗЬ С МАСТЕРОМ → callback_data="contact_master"
```

### ДОПОЛНИТЕЛЬНЫЕ КНОПКИ (из других клавиатур)

#### Магазин (shop.py)
```
📦 ДОБАВИТЬ В КОРЗИНУ → callback_data="add_to_cart_{product_id}"
❤️ ДОБАВИТЬ В ИЗБРАННОЕ → callback_data="add_to_wishlist_{product_id}"
🛒 ПЕРЕЙТИ В КОРЗИНУ → callback_data="cart"
💳 ОФОРМИТЬ ЗАКАЗ → callback_data="checkout"
```

#### Диагностика (diagnostic.py)
```
📸 ОТПРАВИТЬ ФОТО 1 → callback_data="send_photo1"
📸 ОТПРАВИТЬ ФОТО 2 → callback_data="send_photo2"
📝 ДОБАВИТЬ ЗАМЕТКИ → callback_data="add_notes"
✅ ОТПРАВИТЬ НА АНАЛИЗ → callback_data="submit_diagnostic"
```

#### Кастомный заказ (custom_order.py)
```
📝 НАЧАТЬ ЗАКАЗ → callback_data="start_custom_order"
📸 ДОБАВИТЬ ФОТО → callback_data="add_photo_{number}"
✅ ОТПРАВИТЬ ЗАКАЗ → callback_data="submit_order"
```

#### Квиз (quiz.py)
```
🚹 МУЖЧИНА → callback_data="gender_male"
🚺 ЖЕНЩИНА → callback_data="gender_female"
⭐ ОТВЕТИТЬ → callback_data="answer_{question_id}_{answer_id}"
```

#### Музыка (music.py)
```
▶️ {название трека} → callback_data="music_{track_id}"
```

#### Практики (workouts.py)
```
▶️ {название практики} → callback_data="workout_{workout_id}"
```

#### Админ-панель (admin.py)
```
📊 СТАТИСТИКА → callback_data="admin_stats"
📢 РАССЫЛКА → callback_data="admin_broadcast"
🛍 ТОВАРЫ → callback_data="admin_products"
🎫 ПРОМОКОДЫ → callback_data="admin_promos"
📋 ЗАКАЗЫ → callback_data="admin_orders"
📤 ЭКСПОРТ → callback_data="admin_export"
⏰ ПЛАНИРОВЩИК → callback_data="admin_scheduler"
⚙️ НАСТРОЙКИ → callback_data="admin_settings"
```

---

## 🔄 СПИСОК ВСЕХ СОСТОЯНИЙ (FSM STATES)

### Базовые состояния ввода
```
BaseInputStates:
- waiting_name
- waiting_emoji  
- waiting_description
- waiting_price
- waiting_photo
- waiting_text
- waiting_number
- waiting_confirm
- waiting_code
```

### Диагностика
```
DiagnosticStates:
- waiting_photo1
- waiting_photo2
- waiting_notes
```

### Кастомный заказ
```
CustomOrderStates:
- q1_purpose
- q2_stones
- q3_size
- q4_notes
- photo1
- photo2
```

### Квиз и тотем
```
QuizStates:
- choosing_gender
- q1, q2, q3, q4, q5

TotemStates:
- choosing_gender
- q1, q2, q3, q4, q5
```

### Истории
```
StoryStates:
- waiting_text
- waiting_photo
```

### Сертификаты
```
GiftStates:
- waiting_amount
- waiting_recipient
- waiting_message
- waiting_code
```

### Бронирование услуг
```
BookingStates:
- selecting_service
- selecting_date
- selecting_time
- entering_comment
- confirming
```

### Админ-состояния
```
AdminStates:
- waiting_text
- waiting_confirm
- category_create_name
- category_create_emoji
- category_create_desc
- category_edit
- category_edit_field
- bracelet_create_name
- bracelet_create_price
- bracelet_create_category
- bracelet_create_desc
- bracelet_create_photo
- promo_create_type
- promo_create_discount
- promo_create_max_uses
- promo_create_expires
- promo_create_description
- promo_create_code
- promo_edit_field
- promo_edit_value
```

---

## 📋 СПИСОК ВСЕХ ОБРАБОТЧИКОВ (HANDLERS)

### Пользовательские
1. **user.py** - Старт, главное меню, базовые команды
2. **profile.py** - Профиль пользователя
3. **daily_stone.py** - Ежедневный камень
4. **club.py** - Клуб/портал силы
5. **compatibility.py** - Совместимость камней
6. **streak.py** - Система стрика
7. **astro_advice.py** - Астро-советы
8. **quiz.py** - Квиз-подбор камня
9. **selector.py** - Селектор (дополнительный подбор)
10. **wishmap.py** - Карта желания
11. **search.py** - Поиск камней
12. **marathon.py** - Марафон 21 день
13. **ai_consult.py** - AI консультация

### Магазин
14. **shop.py** - Витрина товаров
15. **products.py** - Управление товарами (дублирует shop?)
16. **custom_order.py** - Кастомные заказы
17. **payment.py** - Оплата
18. **wishlist.py** - Список желаний

### Контент
19. **knowledge.py** - База знаний
20. **stories.py** - Истории камней
21. **faq.py** - FAQ
22. **music.py** - Музыкальная библиотека
23. **workouts.py** - Практики и упражнения

### Услуги
24. **diagnostic.py** - Диагностика
25. **services.py** - Услуги
26. **gifts.py** - Сертификаты/подарки

### Админ-панель (12 обработчиков)
27. **admin.py** - Главное админ-меню
28. **admin_broadcast.py** - Рассылки
29. **admin_club.py** - Управление клубом
30. **admin_content.py** - Управление контентом
31. **admin_diagnostic.py** - Админ-диагностика
32. **admin_export.py** - Экспорт данных
33. **admin_orders.py** - Заказы
34. **admin_products.py** - Товары
35. **admin_promos.py** - Промокоды
36. **admin_scheduler.py** - Планировщик
37. **admin_services.py** - Услуги
38. **admin_settings.py** - Настройки
39. **admin_stats.py** - Статистика
40. **admin_stones.py** - Управление камнями

---

## 🗃️ СПИСОК ТАБЛИЦ БАЗЫ ДАННЫХ

Из `src/database/models.py` и `src/database/init.py`:

1. **users** - Пользователи
2. **stones** - Камни
3. **categories** - Категории камней
4. **products** - Товары (браслеты)
5. **orders** - Заказы
6. **order_items** - Элементы заказов
7. **cart** - Корзина
8. **wishlist** - Избранное
9. **music** - Музыкальные треки
10. **workouts** - Практики
11. **stories** - Истории
12. **diagnostics** - Диагностики
13. **services** - Услуги
14. **bookings** - Бронирования
15. **gifts** - Сертификаты
16. **referrals** - Рефералы
17. **promo_codes** - Промокоды
18. **admin_logs** - Логи админа

---

## ⚙️ ТЕКУЩАЯ ЛОГИКА РАБОТЫ БОТА

### Стартовый поток
```
/start → Приветствие → Главное меню (get_main_keyboard)
```

### Основные сценарии

#### 1. Подбор камня
```
ПОДОБРАТЬ МОЙ КАМЕНЬ → Квиз (5 вопросов) → Результат
ТОТЕМНЫЙ КАМЕНЬ → Тотем-квиз → Результат
СОВМЕСТИМОСТЬ КАМНЕЙ → Ввод камней → Анализ
ПОИСК КАМНЯ → Поиск по названию → Результаты
```

#### 2. Покупки
```
ВИТРИНА → Список товаров → Добавить в корзину → Корзина → Оформить заказ
КАСТОМНЫЙ ЗАКАЗ → Вопросы → Фото → Отправка мастеру
```

#### 3. Знания
```
БАЗА ЗНАНИЙ → Категории → Камни → Детали
КАМЕНЬ ДНЯ → Случайный камень
```

#### 4. Услуги
```
ДИАГНОСТИКА → Фото + заметки → Отправка мастеру
УСЛУГИ → Список услуг → Бронирование
СЕРТИФИКАТЫ → Покупка сертификата
```

#### 5. Практики
```
МУЗЫКА → Список треков → Прослушивание
ПРАКТИКИ → Список упражнений → Детали
МАРАФОН → Участие в марафоне
СТРИК → Отслеживание прогресса
АСТРО-СОВЕТ → Совет по знаку зодиака
```

#### 6. Профиль
```
МОЙ ПРОФИЛЬ → Информация + настройки
РЕФЕРАЛЫ → Система приглашений
ПОРТАЛ СИЛЫ → Клуб-функции
```

#### 7. Админ
```
/admin → Админ-меню → Выбор раздела → Управление
```

---

## 🔧 ТЕХНИЧЕСКОЕ СОСТОЯНИЕ

### Рабочие компоненты
- ✅ База данных (SQLite)
- ✅ FSM состояния (MemoryStorage)
- ✅ Rate limiting middleware
- ✅ Логирование
- ✅ Seed данные (камни, музыка, практики)

### Потенциальные проблемы
- ⚠️ 40+ состояний могут вызывать memory leaks при большом трафике
- ⚠️ Дублирование логики между shop.py и products.py
- ⚠️ User/Admin версии некоторых обработчиков (diagnostic, services)
- ⚠️ Отсутствие persistent storage для корзины (теряется при перезапуске)

### Рекомендации по оптимизации
1. **Консолидировать состояния:** 40+ → 6-8 классов
2. **Убрать дублирование:** products.py в shop.py
3. **Мигрировать на Redis:** Для корзины и временных данных
4. **Упростить архитектуру:** Убрать неиспользуемые обработчики

---

## 📈 СТАТИСТИКА ИСПОЛЬЗОВАНИЯ

### По категориям кнопок
- **Покупки:** 4 кнопки
- **Подбор:** 4 кнопки  
- **Знания:** 2 кнопки
- **Услуги:** 3 кнопки
- **Практики:** 4 кнопки
- **Профиль:** 3 кнопки
- **Прочее:** 4 кнопки
- **Админ:** 8 кнопок

### По состояниям
- **Базовые:** 9 состояний
- **Диагностика:** 3 состояния
- **Заказы:** 6 состояний
- **Квизы:** 10 состояний
- **Админ:** 20+ состояний

---

## 🎯 ВЫВОДЫ АУДИТА

**Сильные стороны:**
- Полнофункциональный бот с широким спектром услуг
- Хорошая структура кода (роутеры, клавиатуры, состояния)
- Интеграция с БД и middleware

**Слабые стороны:**
- Избыточная сложность (40+ handlers/states)
- Потенциальные memory leaks
- Дублирование кода

**Рекомендации:**
- Оптимизировать до 25-28 handlers
- Упростить states до 6-8 классов
- Добавить Redis для persistent данных
- Убрать мертвый код (если есть)

**Текущее состояние:** ✅ РАБОТАЕТ СТАБИЛЬНО