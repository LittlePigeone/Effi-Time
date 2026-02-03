# Деплой на Ubuntu 24.04 (Docker) для effective-time.ru

Цель: поднять Django (ASGI+daphne) + PostgreSQL в Docker, с Nginx reverse-proxy и бесплатным SSL (Let’s Encrypt).

## 0) DNS
В панели домена:
- `A effective-time.ru` → `77.95.201.98`
- `A www.effective-time.ru` → `77.95.201.98` (или `CNAME www` → `effective-time.ru`)

Проверь:
```bash
dig +short effective-time.ru A
dig +short www.effective-time.ru A
dig @1.1.1.1 +short effective-time.ru A
dig @1.1.1.1 +short www.effective-time.ru A
```

## 1) Сервер: базовая подготовка
```bash
sudo apt update
sudo apt install -y ufw
```

Firewall:
```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

## 2) Загрузка файлов через SFTP и .env
Ты загружаешь проект через SFTP, поэтому на сервере нужно просто подготовить директорию и залить туда файлы.

На сервере:
```bash
cd /opt
sudo mkdir -p /opt/time_shape_manager
sudo chown -R $USER:$USER /opt/time_shape_manager
cd /opt/time_shape_manager
```

Через SFTP залей содержимое проекта так, чтобы на сервере были:
- `/opt/time_shape_manager/src-tim/compose.yaml`
- `/opt/time_shape_manager/src-tim/Dockerfile`
- `/opt/time_shape_manager/src-tim/requirements.txt`
- `/opt/time_shape_manager/src-tim/manage.py` и весь код проекта

Проверка, что файлы реально на месте:
```bash
ls -la /opt/time_shape_manager
ls -la /opt/time_shape_manager/src-tim
test -f /opt/time_shape_manager/src-tim/compose.yaml && echo OK || echo MISSING
```

Создай env:
```bash
cp src-tim/.env.example .env
nano .env
```

Минимально поменяй:
- `SECRET_KEY=...` (случайная длинная строка)
- `DB_PASSWORD=...`
- `OPENROUTER_API_KEY=...` (если хочешь AI планирование)

Рекомендованные значения под домен:
- `ALLOWED_HOSTS=effective-time.ru,www.effective-time.ru,77.95.201.98,localhost,127.0.0.1`
- `CSRF_TRUSTED_ORIGINS=https://effective-time.ru,https://www.effective-time.ru`

Важно: не храни `.env` внутри `src-tim/` — Docker build контекст копирует файлы в образ, можно случайно зашить секреты.

## 3) Nginx конфиг (первый старт — HTTP)
Стартуй с HTTP-конфига (он нужен для Let’s Encrypt webroot challenge):
```bash
cp src-tim/deploy/nginx/effective-time.conf.http.tpl src-tim/deploy/nginx/effective-time.conf
docker compose -f src-tim/compose.yaml restart nginx
```

HTTP-конфиг проксирует на app и отдаёт `/.well-known/acme-challenge/`.

Создай каталоги под certbot:
```bash
mkdir -p src-tim/deploy/certbot/www
mkdir -p src-tim/deploy/certbot/conf
```

## 4) Старт контейнеров (app+db+nginx)
```bash
cd /opt/time_shape_manager
docker compose --env-file .env -f src-tim/compose.yaml up --build -d
docker compose --env-file .env -f src-tim/compose.yaml ps
```

Если app не стартует и в логах видишь попытку подключиться к Postgres на `localhost`, проверь что в `.env` стоит `DB_HOST=db`.

Проверка HTTP:
```bash
curl -I http://effective-time.ru
```

Если nginx отдаёт `502 Bad Gateway`, а app только что пересоздавался, перезапусти nginx (он кэширует DNS апстрима при старте):
```bash
docker compose -f src-tim/compose.yaml restart nginx
```

Если получаешь `curl: (6) Could not resolve host`, это не проблема Docker — это DNS/резолвинг на сервере или домен ещё не указывает на IP.
Быстрая диагностика:
```bash
getent hosts effective-time.ru || true
getent hosts www.effective-time.ru || true
dig +short effective-time.ru A
dig +short www.effective-time.ru A
cat /etc/resolv.conf
```

Проверка, что nginx реально отвечает локально на сервере:
```bash
curl -I http://127.0.0.1
curl -I http://127.0.0.1:8000
```

Проверка статики (должно быть 200/304, не 404):
```bash
docker compose -f src-tim/compose.yaml exec -T nginx ls -la /var/www/static | head
curl -I http://77.95.201.98/static/ || true
```

Проверка, что домен не обязателен для теста:
```bash
curl -I http://77.95.201.98
```

Важно: не используй бэктики в curl (это не кавычки, а подстановка команды):
```bash
curl -I http://77.95.201.98
```

## 5) Получение SSL (Let’s Encrypt) через webroot
Перед выпуском Let’s Encrypt обязательно включи HTTP-конфиг (без 443/редиректа), чтобы certbot смог проверить `/.well-known/acme-challenge/`:
```bash
cd /opt/time_shape_manager
cp src-tim/deploy/nginx/effective-time.conf.http.tpl src-tim/deploy/nginx/effective-time.conf
docker compose -f src-tim/compose.yaml restart nginx
```

Проверка, что домен уже указывает на сервер:
```bash
dig @1.1.1.1 +short effective-time.ru A
dig @1.1.1.1 +short www.effective-time.ru A
```

Запусти certbot одноразово:
```bash
docker run --rm \
  -v /opt/time_shape_manager/src-tim/deploy/certbot/conf:/etc/letsencrypt \
  -v /opt/time_shape_manager/src-tim/deploy/certbot/www:/var/www/certbot \
  certbot/certbot:latest certonly \
  --webroot -w /var/www/certbot \
  -d effective-time.ru -d www.effective-time.ru \
  --email you@example.com --agree-tos --no-eff-email --non-interactive
```

Важно:
- замени `you@example.com` на свой email (не используй `<...>` — угловые скобки в bash ломают команду)
- не используй бэктики (это не кавычки, а подстановка команды)

Проверь, что сертификаты появились:
```bash
ls -la src-tim/deploy/certbot/conf/live/effective-time.ru/
```

## 6) Переключение nginx на HTTPS
Подмени активный nginx-конфиг на HTTPS-шаблон:
```bash
cp src-tim/deploy/nginx/effective-time.conf.https.tpl src-tim/deploy/nginx/effective-time.conf
```

И перезапусти nginx:
```bash
docker compose -f src-tim/compose.yaml restart nginx
```

Проверка:
```bash
curl -I https://effective-time.ru
```

Если браузер всё ещё ругается как на self-signed, проверь что nginx реально подхватил LetsEncrypt-серты:
```bash
docker compose -f src-tim/compose.yaml logs --tail=200 nginx
ls -la src-tim/deploy/certbot/conf/live/effective-time.ru/
```

## 7) Автообновление сертификата (cron)
Поставь cron (2 раза в день), он безопасный — certbot продлит только если нужно.

Открой cron:
```bash
crontab -e
```

Добавь:
```cron
0 3,15 * * * docker run --rm -v /opt/time_shape_manager/src-tim/deploy/certbot/conf:/etc/letsencrypt -v /opt/time_shape_manager/src-tim/deploy/certbot/www:/var/www/certbot certbot/certbot:latest renew --webroot -w /var/www/certbot && docker compose -f /opt/time_shape_manager/src-tim/compose.yaml restart nginx
```

## 7.1) Self-signed SSL (если Let’s Encrypt пока не доступен)
Это вариант “лишь бы был https”. Браузер будет ругаться, пока ты не добавишь исключение.

Сгенерируй сертификат на сервере:
```bash
mkdir -p /opt/time_shape_manager/src-tim/deploy/selfsigned
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout /opt/time_shape_manager/src-tim/deploy/selfsigned/privkey.pem \
  -out /opt/time_shape_manager/src-tim/deploy/selfsigned/fullchain.pem \
  -subj "/CN=effective-time.ru"
```

Переключи nginx на готовый self-signed конфиг:
```bash
cp src-tim/deploy/nginx/effective-time.conf.selfsigned.tpl src-tim/deploy/nginx/effective-time.conf
```

Применение:
```bash
docker compose -f src-tim/compose.yaml up -d
docker compose -f src-tim/compose.yaml restart nginx
curl -I https://77.95.201.98
```

В `.env` важно: без бэктиков/кавычек, просто CSV:
```env
CSRF_TRUSTED_ORIGINS=https://effective-time.ru,https://www.effective-time.ru
```

## 8) PostgreSQL: удалённое подключение (как лучше)
По умолчанию `POSTGRES_PUBLISH_BIND=127.0.0.1:5432`, то есть БД не торчит наружу.

Подключение с локалки через SSH-туннель:
```bash
ssh -L 5432:127.0.0.1:5432 <user>@77.95.201.98
```

И локально подключайся к:
- host: `127.0.0.1`
- port: `5432`
- db/user/pass: из `src-tim/.env`

Если прям очень надо открыть БД наружу (не рекомендую), тогда в `src-tim/.env`:
- `POSTGRES_PUBLISH_BIND=0.0.0.0:5432`
и добавь firewall правило только на свой IP.

Открыть доступ только для одного IP (пример):
```bash
sudo ufw allow from <твой_IP> to any port 5432 proto tcp
sudo ufw deny 5432/tcp
sudo ufw status
```

## 9) Полезные команды
Логи:
```bash
docker compose -f src-tim/compose.yaml logs -f --tail=200 app
docker compose -f src-tim/compose.yaml logs -f --tail=200 nginx
docker compose -f src-tim/compose.yaml logs -f --tail=200 db
```

Рестарт:
```bash
docker compose -f src-tim/compose.yaml restart
```

Обновление кода (через SFTP):
```bash
cd /opt/time_shape_manager
docker compose -f src-tim/compose.yaml down
# загрузи новые файлы через SFTP в /opt/time_shape_manager/
docker compose -f src-tim/compose.yaml up --build -d
```

Быстрый “перезапуск после обновления” (если менялись только файлы приложения):
```bash
cd /opt/time_shape_manager
docker compose -f src-tim/compose.yaml up --build -d
docker compose -f src-tim/compose.yaml restart nginx
```
