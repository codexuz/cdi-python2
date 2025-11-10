# CDI IELTS Platform
A Django-based platform for IELTS practice and test management with user profiles, payments, and admin tools.

- API docs: /api/docs
- Schema: /api/schema

Table of contents
- Overview
- Features
- Tech stack
- Quick start (local)
- Environment variables
- Running (local and Docker)
- Payments (Click) — Top-up flow
- Project structure
- Useful commands
- Contributing

Overview
CDI IELTS is a backend service that powers an IELTS practice platform. It provides authentication, user profiles, tests, speaking module, teacher checking, and payment top-ups via Click.

Features
- JWT auth and user accounts
- Profiles with balances and top-up history
- IELTS tests and user test tracking
- Speaking module and teacher checking flows
- Payments: Click integration (top-up redirect + webhook)
- OpenAPI/Swagger docs with drf-spectacular

Tech stack
- Python 3 + Django REST Framework
- PostgreSQL
- JWT (simplejwt)
- Docker (optional)

Quick start (local)
1) Clone and enter the project
- git clone <your_repo_url>
- cd CDI_IELTS

2) Create virtualenv and install deps
- python -m venv .venv
- source .venv/bin/activate  # Windows: .venv\Scripts\activate
- pip install -r requirements.txt

3) Configure .env (see Environment variables)

4) Migrate and run
- python manage.py migrate
- python manage.py runserver

Open http://127.0.0.1:8000/api/docs to explore the API.

Environment variables
Create .env in the project root. Required keys:

# Django
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
TIME_ZONE=Asia/Tashkent

# PostgreSQL (docker-compose uses service name "db")
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Click (payment) configuration
# Values below must be provided by Click.uz merchant panel
CLICK_SERVICE_ID=11111
CLICK_MERCHANT_ID=22222
CLICK_MERCHANT_USER_ID=33333
CLICK_SECRET_KEY=your_click_secret
# Click payment page base URL, e.g. https://my.click.uz/services/pay
CLICK_BASE_URL=https://my.click.uz/services/pay
# Where Click should redirect the user after payment or cancel
CLICK_RETURN_URL=https://your-frontend.example.com/payments/return
CLICK_CANCEL_URL=https://your-frontend.example.com/payments/cancel

# Optional CORS/CSRF
CORS_ALLOW_ALL_ORIGINS=True
CSRF_TRUSTED_ORIGINS=http://localhost:8000

Payments (Click) — Top-up flow
This project implements a simple top-up flow using Click.

1) Create top-up session (frontend)
- Method: POST /api/payments/topup/
- Auth: Bearer token (user)
- Body: { "amount": 50000 }
- Response: 201 Created with JSON:
  {
    "id": "<uuid>",
    "status": "created",
    "amount": "50000.00",
    "currency": "UZS",
    "created_at": "2025-01-01T12:00:00Z",
    "completed_at": null,
    "redirect_url": "https://my.click.uz/services/pay?..."
  }
- Frontend should redirect the user to redirect_url.

2) User completes/cancels payment on Click page
- Click redirects back to your frontend using the provided return/cancel URLs.
- Frontend stores payment_id from the return URL query if needed.

3) Click server invokes webhook (backend)
- Endpoint: POST /api/payments/click/webhook/
- The backend verifies IP and signature and updates the payment status to pending/paid/failed/canceled.
- No user action is required here.

4) Frontend polls payment status
- Method: GET /api/payments/status/?payment_id=<uuid>
- Response:
  {
    "id": "<uuid>",
    "student": "<student_uuid>",
    "provider": "click",
    "status": "paid|pending|failed|canceled|created",
    "is_paid": true|false,
    "amount": "50000.00",
    "currency": "UZS",
    "provider_invoice_id": "...",
    "provider_txn_id": "...",
    "created_at": "...",
    "completed_at": "..."
  }

Notes
- Minimal and maximal top-up amounts are controlled by settings:
  - PAYMENTS.MIN_TOPUP (default 1000)
  - PAYMENTS.MAX_TOPUP (default 5_000_000)
- Webhook security:
  - Signature is verified.
  - Allowed IPs are restricted in settings.CLICK.ALLOWED_IPS.

Running with Docker
- docker-compose up --build
Then open http://127.0.0.1:8000/api/docs.

Project structure
- apps/ — project apps: accounts, users, tests, user_tests, payments, profiles, speaking, teacher_checking
- config/ — Django settings and URLs
- bot/ — bot integration
- static/, media/ — static/user media

Useful commands
- Run server: python manage.py runserver
- Apply migrations: python manage.py migrate
- Create superuser: python manage.py createsuperuser

Contributing
1) Fork the repo
2) Create a feature branch: git checkout -b feature/awesome
3) Commit: git commit -m "feat: add awesome thing"
4) Push: git push origin feature/awesome
5) Open a Pull Request
