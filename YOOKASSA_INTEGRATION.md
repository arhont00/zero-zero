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

В `.env` файле добавить:

```env
YOOKASSA_SHOP_ID=ваш_shop_id
YOOKASSA_SECRET_KEY=ваш_secret_key
YOOKASSA_TEST_MODE=true  # для тестового режима
```

---

## ШАГ 4. ИНИЦИАЛИЗАЦИЯ ЮKASSA В КОДЕ

```javascript
// yookassa.js
const YooKassa = require('yookassa-ts-sdk');

const yooKassa = new YooKassa({
  shopId: process.env.YOOKASSA_SHOP_ID,
  secretKey: process.env.YOOKASSA_SECRET_KEY,
  testMode: process.env.YOOKASSA_TEST_MODE === 'true'
});

module.exports = yooKassa;
```

---

## ШАГ 5. СОЗДАНИЕ ПЛАТЁЖА

```javascript
// routes/payment.js
const express = require('express');
const router = express.Router();
const yooKassa = require('../yookassa');

router.post('/create-payment', async (req, res) => {
  try {
    const { amount, description, orderId } = req.body;

    const payment = await yooKassa.createPayment({
      amount: {
        value: amount.toString(),
        currency: 'RUB'
      },
      capture: true,
      confirmation: {
        type: 'redirect',
        return_url: 'https://magic-stone.org/payment/success'
      },
      description: description,
      metadata: {
        orderId: orderId
      }
    });

    res.json({
      paymentId: payment.id,
      confirmationUrl: payment.confirmation.confirmation_url
    });
  } catch (error) {
    console.error('Payment creation error:', error);
    res.status(500).json({ error: 'Failed to create payment' });
  }
});

module.exports = router;
```

---

## ШАГ 6. ОБРАБОТКА WEBHOOK ОТ ЮKASSA

```javascript
// routes/webhook.js
const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const yooKassa = require('../yookassa');

router.post('/yookassa-webhook', express.raw({ type: 'application/json' }), async (req, res) => {
  try {
    const signature = req.headers['x-yookassa-signature'];
    const body = req.body;

    // Проверка подписи
    const expectedSignature = crypto
      .createHmac('sha256', process.env.YOOKASSA_SECRET_KEY)
      .update(JSON.stringify(body))
      .digest('hex');

    if (signature !== expectedSignature) {
      return res.status(400).json({ error: 'Invalid signature' });
    }

    const event = body.event;
    const payment = body.object;

    if (event === 'payment.succeeded') {
      // Платёж успешен
      const orderId = payment.metadata.orderId;
      // Обновить статус заказа в БД
      await updateOrderStatus(orderId, 'paid');
      // Отправить уведомление пользователю
      await sendPaymentSuccessNotification(orderId);
    } else if (event === 'payment.canceled') {
      // Платёж отменён
      const orderId = payment.metadata.orderId;
      await updateOrderStatus(orderId, 'canceled');
    }

    res.json({ received: true });
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({ error: 'Webhook processing failed' });
  }
});

module.exports = router;
```

---

## ШАГ 7. ФРОНТЕНД ИНТЕГРАЦИЯ (REACT)

```javascript
// PaymentButton.js
import React, { useState } from 'react';

const PaymentButton = ({ orderId, amount, description }) => {
  const [loading, setLoading] = useState(false);

  const handlePayment = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/payment/create-payment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          orderId,
          amount,
          description
        })
      });

      const data = await response.json();

      if (data.confirmationUrl) {
        // Перенаправление на страницу оплаты ЮKassa
        window.location.href = data.confirmationUrl;
      }
    } catch (error) {
      console.error('Payment error:', error);
      alert('Ошибка при создании платежа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handlePayment} disabled={loading}>
      {loading ? 'Создание платежа...' : `Оплатить ${amount} ₽`}
    </button>
  );
};

export default PaymentButton;
```

---

## ШАГ 8. СТРАНИЦА УСПЕШНОЙ ОПЛАТЫ

```javascript
// pages/payment/success.js (Next.js)
import { useRouter } from 'next/router';
import { useEffect } from 'react';

const PaymentSuccess = () => {
  const router = useRouter();

  useEffect(() => {
    // Проверка статуса платежа
    const checkPaymentStatus = async () => {
      const { orderId } = router.query;
      if (orderId) {
        // Запрос к API для проверки статуса
        const response = await fetch(`/api/order/${orderId}/status`);
        const data = await response.json();

        if (data.status === 'paid') {
          // Показать успех
          alert('Оплата прошла успешно!');
          router.push('/profile/orders');
        } else {
          // Показать ошибку
          alert('Оплата не была подтверждена');
        }
      }
    };

    checkPaymentStatus();
  }, [router]);

  return (
    <div>
      <h1>Обработка платежа...</h1>
      <p>Пожалуйста, подождите, пока мы подтвердим оплату.</p>
    </div>
  );
};

export default PaymentSuccess;
```

---

## ШАГ 9. ДОБАВЛЕНИЕ В ОСНОВНОЕ ПРИЛОЖЕНИЕ

```javascript
// app.js или index.js
const express = require('express');
const app = express();

// Middleware
app.use(express.json());
app.use('/api', require('./routes/payment'));
app.use('/webhook', require('./routes/webhook'));

// Для обработки raw body в webhook
app.use('/webhook/yookassa-webhook', express.raw({ type: 'application/json' }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

---

## ШАГ 10. ТЕСТИРОВАНИЕ

1. **Тестовый режим:** Установите `YOOKASSA_TEST_MODE=true`
2. **Тестовые карты:** Используйте тестовые данные ЮKassa
3. **Webhook URL:** В личном кабинете ЮKassa укажите URL webhook: `https://your-domain.com/webhook/yookassa-webhook`

---

## ШАГ 11. ПРОДАКШЕН НАСТРОЙКИ

1. **Переключение в боевой режим:** `YOOKASSA_TEST_MODE=false`
2. **SSL сертификат:** Обязателен для webhook
3. **Мониторинг:** Добавьте логирование всех платежей
4. **Безопасность:** Валидируйте все входящие данные

---

## ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ

### Возврат платежа
```javascript
const refund = await yooKassa.createRefund({
  payment_id: paymentId,
  amount: {
    value: refundAmount.toString(),
    currency: 'RUB'
  }
});
```

### Получение информации о платеже
```javascript
const paymentInfo = await yooKassa.getPayment(paymentId);
```

### Список платежей
```javascript
const payments = await yooKassa.getPayments({
  limit: 10,
  status: 'succeeded'
});
```

---

## ОБРАБОТКА ОШИБОК

```javascript
// Обработка типичных ошибок
if (error.code === 'invalid_request') {
  // Неверные параметры запроса
} else if (error.code === 'authentication_error') {
  // Проблемы с аутентификацией
} else if (error.code === 'payment_method_invalid') {
  // Неподдерживаемый способ оплаты
}
```

---

## ИНТЕГРАЦИЯ С СУЩЕСТВУЮЩИМ БОТОМ

Для интеграции с Telegram ботом добавьте обработчик платежей:

```javascript
// В bot handlers/payment.js
bot.on('callback_query', async (query) => {
  if (query.data === 'pay_order') {
    const orderId = query.data.split('_')[2];
    // Получить данные заказа из БД
    const order = await getOrderById(orderId);
    
    // Создать платёж через ЮKassa
    const paymentResponse = await fetch('/api/payment/create-payment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        orderId: order.id,
        amount: order.total,
        description: `Заказ #${order.id}`
      })
    });
    
    const paymentData = await paymentResponse.json();
    
    // Отправить ссылку на оплату
    bot.sendMessage(query.from.id, 
      `Ссылка на оплату: ${paymentData.confirmationUrl}`
    );
  }
});
```

---

## ЗАКЛЮЧЕНИЕ

Эта интеграция позволяет принимать платежи через ЮKassa с автоматической обработкой webhook и обновлением статусов заказов. Тестируйте в тестовом режиме перед переходом в продакшен.