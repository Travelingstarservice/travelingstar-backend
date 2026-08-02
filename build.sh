#!/bin/sh
set -eu

python -m pip install -r requirements.txt

if [ -d "traveling-star-frontend" ]; then
  FRONTEND_DIR="traveling-star-frontend"
elif [ -d "../traveling-star-frontend" ]; then
  FRONTEND_DIR="../traveling-star-frontend"
else
  echo "Frontend directory not found" >&2
  exit 1
fi

cd "$FRONTEND_DIR"
npm install
npm run build

cd ..
exec gunicorn app:app
