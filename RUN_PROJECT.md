# How to Run the Full Project

## 1. Backend (FastAPI)

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m prisma generate
python -m prisma db push    # or run migrations if needed
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- Ensure `.env` has valid `DATABASE_URL` and `SECRET_KEY`.

## 2. Frontend (Vite + React)

```bash
cd Libra_Automated_Library
npm install
npm run dev
```

- App: http://localhost:5173  
- API base URL is set in `src/utils/api.js` (`http://127.0.0.1:8000`). Change if your backend runs elsewhere.

## 3. (Optional) Seed books from frontend dummy data

```bash
cd Backend
source venv/bin/activate
python seed_books.py
```

Requires `Libra_Automated_Library/src/data/dummyBooks.js` to exist (same repo).

## 4. (Optional) NFC reader

- **Issue/return (always on):** `cd Nfc && python pn532_test.py`  
- **Scan for Add Book:** `cd Nfc && python pn532_scan_for_register.py`  
Set `BACKEND_URL=http://your-server:8000` if backend is not on localhost.

---

**Summary:** Start backend first (port 8000), then frontend (port 5173). Use **Student** or **Admin** login; admin can add books (with Scan NFC) and approve requests.
