# SSL Certificates

Помістіть сюди SSL сертифікати для production:

- `fullchain.pem` — повний ланцюг сертифікатів
- `privkey.pem` — приватний ключ

## Let's Encrypt (рекомендовано)

```bash
# Встановлення certbot
sudo apt install certbot

# Отримання сертифіката
sudo certbot certonly --webroot -w /var/www/html -d your-domain.com

# Копіювання сертифікатів
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./docker/nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./docker/nginx/ssl/
```

## Автоматичне оновлення

```bash
# Додайте до crontab
0 0 1 * * certbot renew --quiet && docker compose -f docker-compose.prod.yml restart nginx
```

