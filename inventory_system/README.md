# Inventory & Supply Chain Management System

## 1) Setup (Python 3.13 compatible)

1. Install Python 3.13 and MySQL 8+.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 2) Database initialization

1. Ensure MySQL server is running.
2. Run the SQL script:
   ```bash
   mysql -u root -p < database.sql
   ```
3. The script creates all tables, constraints, indexes, and the inventory update trigger.

## 3) Configure environment

Set environment variables (Windows CMD):

```bash
set DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/inventory_supply_chain
set FLASK_SECRET_KEY=change-me
```

If `DATABASE_URL` is not set, app defaults to:
`mysql+pymysql://root:password@localhost:3306/inventory_supply_chain`

## 4) Run the application

```bash
python app.py
```

Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your browser.

## Notes

- Database schema is managed by `database.sql` (no `db.create_all()` needed).
- Dashboard includes product/supplier/stock counts and recent stock transactions.
- CRUD routes include validation, error handling, and flash messages.
