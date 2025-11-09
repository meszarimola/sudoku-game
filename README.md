# Sudoku

This project demonstrates a small, self-contained full-stack web application, implemented with a **Python backend** and a **JavaScript frontend**, and deployed in a **Docker container** on **AWS EC2 (Linux)**.

---

## 🧩 Project Overview

The application provides a simple **Sudoku web game** with real-time server-side validation.  
Users can enter numbers into the Sudoku grid and immediately receive feedback:  
- ✅ **Green border** – correct placement  
- ❌ **Red border** – incorrect placement  

All validation logic runs on the **server side** to ensure consistent behavior and integrity.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-------------|
| Backend | Python 3.12 (built-in `http.server`) |
| Frontend | Vanilla JavaScript, HTML, CSS |
| Containerization | Docker |
| Deployment | AWS EC2 (Ubuntu 22.04 LTS) |
| OS | Linux (Ubuntu) |

---

## ⚙️ Features

- Lightweight Sudoku engine with server-side validation  
- Simple static frontend served by the Python backend  
- Automatic Sudoku solution generation at server startup  
- Dockerized for easy deployment  
- Live AWS deployment available:  
  🔗 [http://51.20.41.205/](http://51.20.41.205/)

---

## 🚀 Run locally 

### Open the terminal and run
```bash
python server.py
```
The application will run locally on localhost:8080, which will be accessible from any browser (locally only).

## 🚀 AWS deployment
You can also view the deployed code on [http://51.20.41.205/](http://51.20.41.205/).

