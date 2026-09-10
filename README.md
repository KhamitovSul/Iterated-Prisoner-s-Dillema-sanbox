# Axelrod Lab

A local web application for experimenting with the **Iterated Prisoner's Dilemma**.

The server is built with **FastAPI** and uses **Axelrod-Python** to run tournaments and individual matches. The frontend is located in `static/`.

> No database or separate frontend build tool is required.

---

## Requirements

* **Python 3.10–3.13**
* `python` command available in the terminal

---

## Quick Start

Clone the repository and open the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

When you see:

```text
Uvicorn running on http://127.0.0.1:8000
```

open:

**http://127.0.0.1:8000**

> ⚠️ Do not open `static/index.html` by double-clicking it.
> The browser will not be able to communicate with the API correctly.

To stop the server:

```text
Ctrl + C
```

For subsequent launches:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

---

## Live Server

The frontend can also be opened using the **Live Server** VS Code extension:

```text
http://127.0.0.1:5500
```

The server allows requests from this origin.

However, the FastAPI server must still be running at:

```text
http://127.0.0.1:8000
```

because `static/app.js` sends API requests to this address.

---

## Features

* 🔎 **Strategy catalog** — browse and search built-in `Axelrod-Python` strategies
* 🏆 **Round-robin tournaments** — compete with 2–8 strategies
* ⚙️ **Custom parameters** — configure:

  * Turns: **5–500**
  * Repetitions: **1–100**
  * Noise: **0–30%**
* 📊 **Rankings** — compare strategies by total score
* 🎮 **Individual matches** — play a match between two strategies
* 📜 **Round history** — inspect the result of every round

---

## Tech Stack

| Technology                  | Purpose                        |
| --------------------------- | ------------------------------ |
| **Python**                  | Backend                        |
| **FastAPI**                 | REST API                       |
| **Axelrod-Python**          | Prisoner's Dilemma simulations |
| **HTML / CSS / JavaScript** | Frontend                       |
| **Uvicorn**                 | ASGI server                    |

---

## Project Structure

```text
Axelrod Lab/
│
├── main.py
├── requirements.txt
│
└── static/
    ├── index.html
    ├── styles.css
    └── app.js
```

### Main files

* `main.py` — FastAPI application and simulation API
* `requirements.txt` — Python dependencies
* `static/index.html` — application interface
* `static/styles.css` — styling
* `static/app.js` — frontend logic and API requests

---

## Security

The server does **not execute arbitrary user-submitted Python code**.

Only strategies provided by `Axelrod-Python` can be selected and executed. This is an intentional security limitation.

Supporting user-created strategies would require running untrusted code inside a properly isolated sandbox or runtime.

---


