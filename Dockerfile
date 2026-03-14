# Base image sifatida Python 3.11 ishlatamiz
FROM python:3.11-slim

# Ishchi katalogni belgilaymiz
WORKDIR /app

# Tizim paketlarini o'rnatish (psycopg2 va boshqalar uchun kerak bo'lishi mumkin)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Kutubxonalarni yuklash
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha fayllarini nusxalash
COPY . .

# Statik fayllarni yig'ish (Django admin paneli uchun)
# BOT_TOKEN kabi o'zgaruvchilar bo'lmasa ham collectstatic xato bermasligi uchun fake qiymatlar ishlatiladi (settings.py da allaqachon sozlangan)
RUN python manage.py collectstatic --noinput

# Portni ochish (faqat web uchun kerak, lekin Dockerfile umumiy bo'ladi)
EXPOSE 8000
