FROM python:3.12-slim

WORKDIR /app
COPY server.py ./server.py
COPY puzzles ./puzzles
COPY public ./public

EXPOSE 8080
CMD ["python", "server.py"]
