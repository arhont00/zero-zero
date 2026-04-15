# ТЕХНИЧЕСКАЯ ИНТЕГРАЦИЯ ЮKASSA ДЛЯ MAGIC-STONE.ORG

**Стек:** React (фронтенд), Node.js (бэкенд), Railway (хостинг), GitHub (деплой).

---

## ШАГ 1. ПОЛУЧЕНИЕ КЛЮЧЕЙ ЮKASSA

1. Зарегистрироваться / войти в [ЮMoney](https://yoomoney.ru).
2. Создать тестовый магазин (для отладки).
3. Сохранить:
   - `shopId`
   - `secretKey`

---

## ШАГ 2. УСТАНОВКА SDK НА БЭКЕНД

```bash
npm install yookassa-ts-sdk
```

---

## ШАГ 3. НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ

В Railway или локальном `.env` добавить:

```env
YOOKASSA_SHOP_ID=ваш_shop_id
YOOKASSA_SECRET_KEY=ваш_secret_key
YOOKASSA_RETURN_URL=https://magic-stone.org/payment/success
YOOKASSA_WEBHOOK_URL=https://your-railway-app.railway.app/api/yookassa/webhook
```

---

## ШАГ 4. СОЗДАНИЕ МОДУЛЯ ОПЛАТЫ (Node.js)

Создать файл `src/services/yookassa.js`:

```javascript
const YooKassa = require('yookassa-ts-sdk');
require('dotenv').config();

const yooKassa = new YooKassa({
  shopId: process.env.YOOKASSA_SHOP_ID,
  secretKey: process.env.YOOKASSA_SECRET_KEY,
});

class YooKassaService {
  // Создание платежа
  async createPayment(orderData) {
    try {
      const payment = await yooKassa.createPayment({
        amount: {
          value: orderData.amount.toString(),
          currency: 'RUB'
        },
        confirmation: {
          type: 'redirect',
          return_url: process.env.YOOKASSA_RETURN_URL
        },
        capture: true,
        description: `Заказ #${orderData.orderId} - ${orderData.description}`,
        metadata: {
          orderId: orderData.orderId,
          userId: orderData.userId
        },
        receipt: {
          customer: {
            email: orderData.customerEmail
          },
          items: orderData.items.map(item => ({
            description: item.name,
            quantity: item.quantity.toString(),
            amount: {
              value: item.price.toString(),
              currency: 'RUB'
            },
            vat_code: 1, // НДС 0%
            payment_mode: 'full_prepayment',
            payment_subject: 'commodity'
          }))
        }
      });

      return {
        paymentId: payment.id,
        confirmationUrl: payment.confirmation.confirmation_url,
        status: payment.status
      };
    } catch (error) {
      console.error('YooKassa create payment error:', error);
      throw new Error('Ошибка создания платежа');
    }
  }

  // Получение статуса платежа
  async getPaymentStatus(paymentId) {
    try {
      const payment = await yooKassa.getPayment(paymentId);
      return {
        status: payment.status,
        paid: payment.paid,
        amount: payment.amount,
        metadata: payment.metadata
      };
    } catch (error) {
      console.error('YooKassa get payment error:', error);
      throw new Error('Ошибка получения статуса платежа');
    }
  }

  // Обработка вебхука
  async handleWebhook(event) {
    try {
      const payment = event.object;

      if (payment.status === 'succeeded') {
        // Платеж успешен
        const orderId = payment.metadata.orderId;
        const userId = payment.metadata.userId;

        // Обновить статус заказа в БД
        await this.updateOrderStatus(orderId, 'paid');

        // Отправить уведомление пользователю
        await this.sendPaymentSuccessNotification(userId, orderId);

        return { success: true };
      }

      return { success: false };
    } catch (error) {
      console.error('Webhook processing error:', error);
      throw error;
    }
  }

  // Вспомогательные методы
  async updateOrderStatus(orderId, status) {
    // Реализовать обновление в БД
    console.log(`Order ${orderId} status updated to ${status}`);
  }

  async sendPaymentSuccessNotification(userId, orderId) {
    // Реализовать отправку уведомления
    console.log(`Payment success notification sent to user ${userId} for order ${orderId}`);
  }
}

module.exports = new YooKassaService();
```

---

## ШАГ 5. ИНТЕГРАЦИЯ В БЭКЕНД (Express.js)

Добавить в основной файл сервера (`app.js` или `server.js`):

```javascript
const express = require('express');
const yooKassaService = require('./src/services/yookassa');

const app = express();

// Middleware для парсинга JSON
app.use(express.json());

// Маршрут для создания платежа
app.post('/api/payment/create', async (req, res) => {
  try {
    const { orderId, amount, description, customerEmail, items, userId } = req.body;

    const paymentData = await yooKassaService.createPayment({
      orderId,
      amount,
      description,
      customerEmail,
      items,
      userId
    });

    res.json({
      success: true,
      paymentUrl: paymentData.confirmationUrl,
      paymentId: paymentData.paymentId
    });
  } catch (error) {
    console.error('Create payment error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Маршрут для проверки статуса платежа
app.get('/api/payment/status/:paymentId', async (req, res) => {
  try {
    const { paymentId } = req.params;
    const status = await yooKassaService.getPaymentStatus(paymentId);

    res.json({ success: true, status });
  } catch (error) {
    console.error('Get payment status error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Вебхук для обработки платежей
app.post('/api/yookassa/webhook', async (req, res) => {
  try {
    const event = req.body;

    // Проверка подписи (рекомендуется добавить)
    // const isValid = yooKassaService.verifyWebhookSignature(req.headers, req.body);

    await yooKassaService.handleWebhook(event);

    res.json({ success: true });
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

---

## ШАГ 6. ИНТЕГРАЦИЯ В ФРОНТЕНД (React)

Создать компонент оплаты `src/components/PaymentForm.js`:

```javascript
import React, { useState } from 'react';
import axios from 'axios';

const PaymentForm = ({ orderData, onSuccess, onError }) => {
  const [loading, setLoading] = useState(false);

  const handlePayment = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/payment/create', orderData);

      if (response.data.success) {
        // Перенаправление на страницу оплаты ЮKassa
        window.location.href = response.data.paymentUrl;
      } else {
        onError('Ошибка создания платежа');
      }
    } catch (error) {
      console.error('Payment creation error:', error);
      onError('Ошибка подключения к платежной системе');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="payment-form">
      <h3>Оплата заказа</h3>
      <div className="order-summary">
        <p>Заказ №{orderData.orderId}</p>
        <p>Сумма: {orderData.amount} ₽</p>
      </div>
      <button
        onClick={handlePayment}
        disabled={loading}
        className="payment-button"
      >
        {loading ? 'Создание платежа...' : 'Оплатить с ЮKassa'}
      </button>
    </div>
  );
};

export default PaymentForm;
```

---

## ШАГ 7. СТРАНИЦА УСПЕШНОЙ ОПЛАТЫ

Создать страницу `src/pages/PaymentSuccess.js`:

```javascript
import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const PaymentSuccess = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    const checkPayment = async () => {
      try {
        const paymentId = searchParams.get('paymentId');

        if (paymentId) {
          const response = await axios.get(`/api/payment/status/${paymentId}`);
          const paymentStatus = response.data.status;

          if (paymentStatus.paid) {
            setStatus('success');
            // Дополнительные действия при успешной оплате
          } else {
            setStatus('pending');
          }
        }
      } catch (error) {
        console.error('Payment check error:', error);
        setStatus('error');
      }
    };

    checkPayment();
  }, [searchParams]);

  if (status === 'checking') {
    return <div>Проверяем статус оплаты...</div>;
  }

  if (status === 'success') {
    return (
      <div className="payment-success">
        <h2>✅ Оплата прошла успешно!</h2>
        <p>Спасибо за покупку. Ваш заказ будет обработан в ближайшее время.</p>
        <a href="/orders">Посмотреть мои заказы</a>
      </div>
    );
  }

  if (status === 'pending') {
    return (
      <div className="payment-pending">
        <h2>⏳ Оплата в обработке</h2>
        <p>Платеж находится в обработке. Мы уведомим вас о завершении.</p>
      </div>
    );
  }

  return (
    <div className="payment-error">
      <h2>❌ Ошибка оплаты</h2>
      <p>Произошла ошибка при обработке платежа. Свяжитесь с поддержкой.</p>
    </div>
  );
};

export default PaymentSuccess;
```

---

## ШАГ 8. ДОБАВЛЕНИЕ МАРШРУТОВ

В `src/App.js` добавить:

```javascript
import PaymentSuccess from './pages/PaymentSuccess';

function App() {
  return (
    <Router>
      <Routes>
        {/* Другие маршруты */}
        <Route path="/payment/success" element={<PaymentSuccess />} />
      </Routes>
    </Router>
  );
}
```

---

## ШАГ 9. ТЕСТИРОВАНИЕ

### Тестовый платеж

1. Перейти в тестовый режим ЮKassa
2. Использовать тестовые карты:
   - Номер: `5555 5555 5555 4477`
   - Срок: `12/25`
   - CVV: `123`
   - Имя: `TEST CARD`

### Проверка вебхука

```bash
# Локально с ngrok
npm install -g ngrok
ngrok http 3000

# Обновить YOOKASSA_WEBHOOK_URL в настройках магазина
```

---

## ШАГ 10. ПРОДАКШН НАСТРОЙКИ

### Безопасность

1. **Проверка подписи вебхука:**
```javascript
const crypto = require('crypto');

function verifyWebhookSignature(headers, body) {
  const signature = headers['x-yookassa-signature'];
  const secret = process.env.YOOKASSA_SECRET_KEY;

  const hash = crypto
    .createHmac('sha256', secret)
    .update(JSON.stringify(body))
    .digest('hex');

  return signature === hash;
}
```

2. **Валидация данных:**
```javascript
const Joi = require('joi');

const paymentSchema = Joi.object({
  orderId: Joi.string().required(),
  amount: Joi.number().positive().required(),
  description: Joi.string().required(),
  customerEmail: Joi.string().email().required(),
  items: Joi.array().items(
    Joi.object({
      name: Joi.string().required(),
      quantity: Joi.number().integer().positive().required(),
      price: Joi.number().positive().required()
    })
  ).required()
});
```

### Мониторинг

1. **Логирование платежей:**
```javascript
const winston = require('winston');

const paymentLogger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'payments.log' })
  ]
});
```

2. **Метрики:**
```javascript
// Использовать Prometheus или аналог
app.get('/metrics', (req, res) => {
  // Возвращать метрики платежей
});
```

---

## ШАГ 11. ОБРАБОТКА ОШИБОК

### Типичные ошибки

1. **Недостаточно средств:**
```javascript
if (error.code === 'insufficient_funds') {
  return res.status(400).json({
    success: false,
    error: 'Недостаточно средств на карте'
  });
}
```

2. **Карта заблокирована:**
```javascript
if (error.code === 'card_blocked') {
  return res.status(400).json({
    success: false,
    error: 'Карта заблокирована. Используйте другую карту'
  });
}
```

3. **Превышен лимит:**
```javascript
if (error.code === 'limit_exceeded') {
  return res.status(400).json({
    success: false,
    error: 'Превышен лимит платежей. Попробуйте позже'
  });
}
```

---

## ШАГ 12. ДОКУМЕНТАЦИЯ И ПОДДЕРЖКА

### API Документация

```javascript
/**
 * @api {post} /api/payment/create Создание платежа
 * @apiName CreatePayment
 * @apiGroup Payment
 *
 * @apiParam {String} orderId ID заказа
 * @apiParam {Number} amount Сумма платежа
 * @apiParam {String} description Описание платежа
 * @apiParam {String} customerEmail Email покупателя
 * @apiParam {Array} items Массив товаров
 *
 * @apiSuccess {String} paymentUrl URL для оплаты
 * @apiSuccess {String} paymentId ID платежа
 */
```

### Поддержка клиентов

1. **Часто задаваемые вопросы:**
   - Как оплатить заказ?
   - Что делать если платеж не прошел?
   - Как вернуть деньги?

2. **Контакты поддержки:**
   - Email: support@magic-stone.org
   - Telegram: @magic_stone_support

---

## ЗАКЛЮЧЕНИЕ

Интеграция ЮKassa позволяет принимать платежи безопасно и удобно. Следуйте шагам по порядку, тестируйте на тестовом окружении, и только потом переходите в продакшн.

**Важно:** Всегда проверяйте соответствие требованиям PCI DSS при работе с платежами.</content>
<parameter name="filePath">/workspaces/zero-zero/YOOKASSA_INTEGRATION.md