FROM python:3.11-slim

COPY requirements/base.txt /src/requirements/base.txt
COPY requirements/production.txt /src/requirements/production.txt

RUN pip install --no-cache-dir --upgrade -r /src/requirements/production.txt

COPY src /src
COPY nginx /nginx

CMD ["uvicorn", "src.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]