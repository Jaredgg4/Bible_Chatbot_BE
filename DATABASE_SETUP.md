# PostgreSQL Database Setup for Render

Your Flask backend is already configured to use PostgreSQL with SQLAlchemy. Here's how to connect it to a PostgreSQL database on Render.

---

## Option 1: Create PostgreSQL Database on Render (Recommended)

### Step 1: Create a PostgreSQL Database
1. Go to https://dashboard.render.com/
2. Click **New +** → **PostgreSQL**
3. Configure your database:
   - **Name**: `bible-chatbot-db` (or your preferred name)
   - **Database**: `bible_chatbot` (default is fine)
   - **User**: `bible_chatbot_user` (default is fine)
   - **Region**: Same as your backend service (for lower latency)
   - **Plan**: Choose **Free** or **Starter** plan
4. Click **Create Database**
5. Wait for the database to be provisioned (takes ~2-3 minutes)

### Step 2: Get the Database Connection String
1. Once created, go to your PostgreSQL database dashboard
2. Scroll down to **Connections** section
3. Copy the **Internal Database URL** (starts with `postgresql://`)
   - Format: `postgresql://user:password@host:port/database`
   - Example: `postgresql://bible_chatbot_user:abc123@dpg-xyz.oregon-postgres.render.com/bible_chatbot`

### Step 3: Add DATABASE_URL to Your Backend Service
1. Go to your backend service on Render
2. Navigate to **Environment** tab
3. Add a new environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the Internal Database URL from Step 2
4. Click **Save Changes**
5. Your service will automatically redeploy

---

## Option 2: Use External PostgreSQL (e.g., Supabase, Neon, ElephantSQL)

If you prefer to use an external PostgreSQL provider:

### Popular Free Options:
- **Supabase**: https://supabase.com (500MB free)
- **Neon**: https://neon.tech (3GB free)
- **ElephantSQL**: https://www.elephantsql.com (20MB free)

### Steps:
1. Create an account on your chosen provider
2. Create a new PostgreSQL database
3. Get the connection string (usually in format: `postgresql://user:password@host:port/database`)
4. Add it to your Render backend service as `DATABASE_URL` environment variable

---

## Database Schema

Your backend will automatically create the following table on first run:

### `users` Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(120) NOT NULL,
    avatar BYTEA NOT NULL
);
```

The table is created automatically by SQLAlchemy when your app starts (see `db.create_all()` in `app.py`).

---

## Verify Database Connection

### Check Render Logs
1. Go to your backend service on Render
2. Click on **Logs** tab
3. Look for these messages:
   ```
   Database tables created successfully
   DATABASE_URL set: True
   ```

### Test Database Connection Locally (Optional)

If you want to test the database connection locally:

1. Get your database URL from Render
2. Create a `.env` file in `bible_chatbot_BE/` directory:
   ```bash
   DATABASE_URL=postgresql://user:password@host:port/database
   API_KEY=your_bible_api_key
   FRONTEND_URL=http://localhost:3000
   ```

3. Run your Flask app locally:
   ```bash
   cd bible_chatbot_BE/backend
   python app.py
   ```

4. Test user creation:
   ```bash
   curl -X POST http://localhost:4000/api/users \
     -F "username=testuser" \
     -F "email=test@example.com" \
     -F "password=testpass123"
   ```

---

## Environment Variables Summary

Your Render backend service should have these environment variables:

```
DATABASE_URL=postgresql://user:password@host:port/database
API_KEY=your_bible_api_key_here
FRONTEND_URL=https://bible-chatbot-fe.vercel.app
PORT=4000
```

---

## Troubleshooting

### "WARNING: DATABASE_URL not set"
- Verify the environment variable is named exactly `DATABASE_URL`
- Check for typos in the connection string
- Redeploy your service after adding the variable

### "Failed to initialize database"
- Check Render logs for specific error messages
- Verify the database is running and accessible
- Ensure `psycopg2-binary` is in your `requirements.txt` (already included)

### Connection Timeout
- If using Render PostgreSQL, use the **Internal Database URL** (not External)
- Ensure your backend and database are in the same region

### SSL Connection Issues
If you get SSL errors, you may need to modify the connection string:
```python
# In app.py, after line 30, add:
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
if database_url and "?" not in database_url:
    database_url += "?sslmode=require"
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
```

---

## Next Steps

1. ✅ Create PostgreSQL database on Render
2. ✅ Copy the Internal Database URL
3. ✅ Add `DATABASE_URL` to your backend environment variables
4. ✅ Wait for automatic redeploy
5. ✅ Check logs to verify database connection
6. ✅ Test user signup on your frontend!

Your database will be ready to use once the backend redeploys successfully.
