# Welcome to RateMate
## What is RateMate?
RateMate – a social network where everyone can rate everyone.

## Project Stack
FastAPI, sqlalchemy, pydantic, PostgreSQL

## How to run
```bash
    python3.12 -m venv venv 
    . venv/bin/activate   
    pip install -r requirements.txt
    python -m ratemate_app.main
```

## Changelog
You can always check the Version History of the project

[changelog](/changelog/changelog.md)

## Project Structure

```bash
.
├── README.md
├── changelog
│   ├── changelog.md
│   └── markdown
│       └── 0.0.1.md
├── ratemate_app
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── comment.py
│   │   └── post.py
│   ├── auth
│   │   ├── __init__.py
│   │   └── security.py
│   ├── core
│   │   ├── __init__.py
│   │   └── config.py
│   ├── db
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── session.py
│   ├── main.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── comment.py
│   │   ├── follow.py
│   │   ├── media.py
│   │   ├── post.py
│   │   ├── rating.py
│   │   └── user.py
│   ├── schemas
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── comment.py
│   │   ├── follow.py
│   │   ├── media.py
│   │   ├── post.py
│   │   ├── rating.py
│   │   ├── token.py
│   │   └── user.py
│   └── services
│       ├── __init__.py
│       ├── comment.py
│       ├── post.py
│       ├── ratings.py
│       └── user.py
├── requirements.txt
└── tests
    └── test_auth.py

12 directories, 40 files
```

## Project Status and License
Actually, this project is more of a personal playground for experimenting with FastAPI.

There is no license, and the code is completely open

Created with ❤️ by @dulatulyn