# ТЕХНИЧЕСКАЯ ИНТЕГРАЦИЯ ЮKASSA ДЛЯ MAGIC-STONE.ORG

**Стек:** React (фронтенд), Node.js (бэкенд), Railway (хостинг), GitHub (деплой).

---

## ШАГ 1. ПОЛУЧЕНИЕ КЛЮЧЕЙ ЮKASSA

1. Зарегистрироваться / войти в [ЮMoney](https://yoomoney.ru).
2. Создать магазин или тестовый кабинет.
3. Сохранить:
   - `shopId`
   - `secretKey`

> Для работы в тестовом режиме надо использовать ключи тестового магазина.

---

## ШАГ 2. УСТАНОВКА SDK НА БЭКЕНД

```bash
npm install yookassa-ts-sdk express dotenv
```

Если вы используете TypeScript:

```bash
npm install -D typescript @types/node ts-node
```

---

## ШАГ 3. ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ

Создайте файл `.env` в корне проекта и добавьте:

```env
YOOKASSA_SHOP_ID=ваш_shopId
YOOKASSA_SECRET_KEY=ваш_secretKey
BASE_URL=https://your-project.railway.app
```

> `BASE_URL` нужен для корректных callback/webhook ссылок.

---

## ШАГ 4. ПРИМЕР БЭКЕНДА НА Node.js + Express

```javascript
const express = require('express');
const bodyParser = require('body-parser');
const { YooKassa } = require('yookassa-ts-sdk');
require('dotenv').config();

const app = express();
app.use(bodyParser.json());

const yookassa = new YooKassa({
  shopId: process.env.YOOKASSA_SHOP_ID,
  secretKey: process.env.YOOKASSA_SECRET_KEY,
});

app.post('/create-payment', async (req, res) => {
  try {
    const { amount, currency, description, returnUrl } = req.body;
    const payment = await yookassa.createPayment({
      amount: { value: amount.toFixed(2), currency },
      confirmation: {
        type: 'redirect',
        return_url: returnUrl,
      },
      capture: true,
      description,
    });

    res.json({
      paymentUrl: payment.confirmation.confirmation_url,
      paymentId: payment.id,
    });
  } catch (error) {
    console.error('YooKassa create payment error', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/webhook/yookassa', (req, res) => {
  const event = req.body;
  // Обработать статус платежа, проверить payment_id и статус
  console.log('YooKassa webhook:', event);
  res.sendStatus(200);
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Server started on port ${port}`);
});
```

> Если ваш проект на Python, аналогичная логика реализуется через `aiohttp` или `fastapi`.

---

## ШАГ 5. ФРОНТЕНД: ЗАПРОС НА СОЗДАНИЕ ПЛАТЕЖА

### Простой пример для React

```javascript
async function createPayment(amount) {
  const response = await fetch('/create-payment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      amount,
      currency: 'RUB',
      description: 'Оплата заказа на magic-stone.org',
      returnUrl: `${window.location.origin}/payment-success`,
    }),
  });

  const data = await response.json();
  if (data.paymentUrl) {
    window.location.href = data.paymentUrl;
  } else {
    throw new Error(data.error || 'Ошибка при создании платежа');
  }
}
```

### Кнопка на сайте

```jsx
<button onClick={() => createPayment(1990)}>Оплатить 1990 ₽</button>
```

---

## ШАГ 6. Обработка webhooks ЮKassa

ЮKassa будет отправлять уведомления на указанный URL. Это должно быть публичный endpoint, доступный из интернета.

```javascript
app.post('/webhook/yookassa', (req, res) => {
  const event = req.body;
  if (event.type === 'payment.succeeded') {
    // Здесь логика: сохранить оплату, обновить заказ, отправить уведомление
    console.log('Оплата прошла:', event.object);
  }
  res.sendStatus(200);
});
```

### Важно

- Для боевого запуска нужен HTTPS.
- Railway предоставляет HTTPS автоматически.
- Для безопасности проверяйте подпись webhook (по документации YooKassa).

---

## ШАГ 7. СТРУКТУРА ФАЙЛОВ

```
project-root/
├── .env
├── package.json
├── server.js
├── public/
│   └── index.html
└── src/
    └── App.jsx
```

---

## ШАГ 8. ДЕПЛОЙ НА RAILWAY

1. Залейте код на GitHub.
2. Создайте проект Railway из репозитория.
3. В секции Variables добавьте `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`, `BASE_URL`.
4. Убедитесь, что Railway выставил `PORT`.
5. Запустите проект. В логах должно появиться `Server started on port ...`.

---

## ШАГ 9. Проверка

1. Запустите локально: `node server.js`.
2. Сделайте запрос к `/create-payment`.
3. Убедитесь, что получаете `paymentUrl`.
4. Перейдите по ссылке и завершите тестовый платёж.
5. Проверяйте webhook в Railway: события должны приходить на `/webhook/yookassa`.

---

## ШАГ 10. Если вы хотите интегрировать ЮKassa в текущий Python-проект

1. Создайте в `web` endpoint `POST /api/create-payment`.
2. Используйте HTTP-клиент `httpx` или `aiohttp` для обращения к YooKassa API.
3. Сгенерируйте платёж аналогично:
   - `amount.value`
   - `amount.currency`
   - `confirmation.type=redirect`
   - `confirmation.return_url`
4. Отправьте пользователю `confirmation.confirmation_url`.
5. Обработайте webhook на отдельном эндпоинте.

---

## Итог

Этот документ описывает шаги для запуска YooKassa в вашем проекте, с примерами и готовой схемой. Если нужно, дальше могу подготовить точный backend-скрипт для вашего Python/Aiohttp проекта или полный фронтенд-интегратор под React.
