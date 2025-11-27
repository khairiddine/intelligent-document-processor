# Document Processing API Backend

FastAPI backend with Supabase database and AG-UI Protocol for agent-user interactions.

## Features

- ✅ User Authentication (Supabase Auth)
- ✅ Document Upload & Storage (Supabase Storage)
- ✅ AI Document Classification (CrewAI + Azure OpenAI)
- ✅ Invoice/Receipt/PO Data Extraction (Azure Document Intelligence)
- ✅ AG-UI Protocol (Agent-User Interaction Standard)
- ✅ Phoenix Tracing & Monitoring
- ✅ RESTful API with automatic docs

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Supabase

1. Create Supabase account: https://supabase.com
2. Create new project
3. Run SQL in Supabase SQL Editor:
   ```bash
   # Copy content from database_schema.sql
   ```
4. Create Storage bucket named `documents` (private)
5. Get API keys from Settings -> API

### 3. Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your values:
# - SUPABASE_URL
# - SUPABASE_KEY
# - SUPABASE_SERVICE_KEY
# - JWT_SECRET
# - Azure credentials
# - Phoenix credentials
```

### 4. Run Server

```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API will be available at: http://localhost:8000

## API Documentation

Interactive API docs: http://localhost:8000/docs

### Endpoints

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

#### Documents
- `POST /documents/upload` - Upload document
- `POST /documents/process` - Process uploaded document (with AG-UI)
- `GET /documents/history` - Get processing history
- `GET /documents/{id}/result` - Get extraction result
- `GET /documents/{id}/agui-history` - Get AG-UI interaction history

## AG-UI Protocol Flow

1. **Upload**: User uploads document
2. **Classification Announcement**: Agent announces it will classify
3. **Classification Result**: Agent announces classification (asks approval if auto_approve=false)
4. **Extraction Announcement**: Agent announces it will extract data
5. **Validation**: Agent validates extracted fields
6. **Completion**: Agent announces success/failure

All interactions are logged and can be retrieved via `/agui-history` endpoint.

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # Supabase client
│   ├── api/
│   │   ├── auth.py          # Auth endpoints
│   │   └── documents.py     # Document endpoints
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── services/
│   │   ├── auth.py          # Auth logic
│   │   └── document_processing.py  # Processing logic
│   └── agui/
│       └── protocol.py      # AG-UI implementation
├── requirements.txt
├── .env.example
└── database_schema.sql      # Supabase schema
```

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Upload document
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@invoice.pdf"

# Process document
curl -X POST http://localhost:8000/documents/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_id":"DOC_ID"}'
```

## Deployment

See deployment guide for:
- Railway
- Render
- Azure App Service
- AWS Lambda

## Phoenix Monitoring

All API calls and document processing are traced in Phoenix.
View traces at: https://app.phoenix.arize.com

## License

MIT
