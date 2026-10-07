# 计算器后端 Docker 镜像
# 构建:  docker build -t calculator-backend .
# 运行:  docker run -p 5000:5000 -e CALC_DEBUG=0 calculator-backend

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV CALC_HOST=0.0.0.0 \
    CALC_PORT=5000 \
    CALC_DEBUG=0 \
    CALC_DB_PATH=/app/data/calculator.db

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60"]
