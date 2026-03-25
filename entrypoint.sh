#!/bin/sh

set -eou pipefail

gunicorn --bind :8000 --workers 3 "$PROJECT.wsgi:application" --timeout 120
