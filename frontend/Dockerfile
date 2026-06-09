FROM node:20-alpine

WORKDIR /app

# Копіюємо package.json та встановлюємо залежності
COPY package.json package-lock.json* ./
RUN npm install

# Копіюємо решту коду
COPY . .

# Порт Vite dev server
EXPOSE 5173

# Запуск dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
