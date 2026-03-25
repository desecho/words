#!/bin/bash

export DEBUG=True
export FRONTEND_URL=http://localhost:5173
export FRONTEND_URL2=http://localhost:4173
export SECRET_KEY=key
export PROJECT_DOMAIN=localhost
export INTERNAL_IP=127.0.0.1
export STATIC_URL=/static/
export ADMIN_EMAIL=admin@example.com
export EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
export DB_ENGINE=django.db.backends.mysql
export DB_NAME=words
export DB_USER=root
export DB_PASSWORD=password
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DJANGO_SETTINGS_MODULE=words.settings
