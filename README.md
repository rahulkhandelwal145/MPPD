# MP Scorer

MP Scorer is a civic accountability web application for tracking the parliamentary performance of all 543 MPs in India's 18th Lok Sabha.

## Backend

Start the backend server from the `backend` folder:

```bash
pip install -r backend/requirements.txt
uvicorn backend.api.main:app --reload --port 8000
```

The backend connects to the database using `DATABASE_URL` from `.env`. For MySQL, use a URL like `mysql+asyncmy://root:password@localhost:3306/mpscorer`.

## Frontend

Start the frontend from the `frontend` folder:

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend API to be available at `http://localhost:8000/api/v1`.

## Environment

Copy `.env.example` to `.env` and update the values.
