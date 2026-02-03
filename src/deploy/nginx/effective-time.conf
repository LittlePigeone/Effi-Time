server {
    listen 80;
    server_name effective-time.ru www.effective-time.ru;
    resolver 127.0.0.11 ipv6=off valid=10s;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location /static/ {
        alias /var/www/static/;
        access_log off;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000" always;
    }

    location /media/ {
        alias /var/www/media/;
        access_log off;
        expires 7d;
        add_header Cache-Control "public, max-age=604800" always;
    }

    location / {
        set $upstream http://app:8000;
        proxy_pass $upstream;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
}

map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}
