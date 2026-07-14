FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY gtin_core.py csv_report.py pdf_report.py sample_data.py ./
COPY brand_fonts/ ./brand_fonts/
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
