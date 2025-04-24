#!/bin/bash
# docker-debug.sh for DB Agent application
# Created: Current date
# Author: Claude 3.7 Sonnet
# Description: 用于调试的Docker脚本，进入容器内部

# 清理现有容器
docker stop dbagent 2>/dev/null || true
docker rm dbagent 2>/dev/null || true

# 设置端口（默认8080）
PORT=${PORT:-8080}

echo "启动调试容器..."
docker run -it --rm \
  --name dbagent \
  -p $PORT:5000 \
  -e SUPABASE_DB_URI="${SUPABASE_DB_URI:-""}" \
  -e FLASK_ENV="development" \
  dbagent /bin/bash

# 提示: 在容器内部可以运行 python3 app.py 或 gunicorn --bind 0.0.0.0:5000 app:app 