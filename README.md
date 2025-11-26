# 📚 Conversation Vault

A local web application for importing, storing, browsing, and managing conversation history from multiple LLM providers (OpenAI/ChatGPT and Anthropic/Claude).

## Features

- **Multi-Provider Support**: Import conversations from OpenAI and Anthropic (extensible architecture for more providers)
- **Secure Storage**: All data stored locally in PostgreSQL with encrypted API keys
- **Rich Browsing**: Search, filter, and organize conversations by provider, project, date, and content
- **Project Organization**: Group related conversations into projects
- **Export Functionality**: Export conversations to Markdown format
- **Artifact Tracking**: Track attachments, files, and artifacts associated with conversations
- **Import Jobs**: Background job system for importing large conversation histories

## Requirements

- **Python 3.10+**
- **PostgreSQL** (any recent version)
- **Ubuntu/Linux** (or similar Unix-like OS)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd conversation-vault
```

### 2. Run Setup

The setup script will:
- Create a Python virtual environment
- Install all dependencies
- Configure your database connection
- Generate encryption keys
- Run database migrations

```bash
./setup.sh
```

Follow the prompts to configure your PostgreSQL connection.

### 3. Start the Server

```bash
./run.sh
```

Or manually:

```bash
source venv/bin/activate
cd backend
python -m app.main
```

### 4. Open Your Browser

Navigate to: **http://localhost:7025**

## Project Structure

```
conversation-vault/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── models/           # SQLAlchemy models
│   │   ├── providers/        # Provider adapters
│   │   ├── services/         # Business logic
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database setup
│   │   └── main.py           # FastAPI application
│   └── alembic/              # Database migrations
├── frontend/
│   ├── static/               # CSS and JavaScript
│   └── templates/            # HTML templates
├── .env                      # Environment configuration (created by setup)
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── setup.sh                  # Setup script
└── run.sh                    # Convenience run script
```

## Configuration

### Environment Variables

Configuration is stored in `.env` (created during setup):

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/conversation_vault

# Server
HOST=127.0.0.1
PORT=7025

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-fernet-key

# Environment
ENV=development
```

### Database Setup

If you need to manually create the database:

```bash
createdb -U your_username conversation_vault
```

Then run migrations:

```bash
source venv/bin/activate
cd backend
alembic upgrade head
```

## Usage Guide

### 1. Configure API Keys

1. Navigate to the **API Keys** tab
2. Click **+ New API Key**
3. Select your provider (OpenAI or Anthropic)
4. Enter a label and your API key
5. Click **Save**

**Note**: API keys are encrypted at rest using Fernet encryption.

### 2. Create Projects (Optional)

Organize your conversations by creating projects:

1. Go to the **Projects** tab
2. Click **+ New Project**
3. Enter a name and optional description
4. Click **Create**

### 3. Import Conversations

**Important**: As of January 2025, neither OpenAI nor Anthropic provides a direct API to export conversation history. The import functionality is prepared for:
- Future API support
- File-based imports from exported conversations
- Manual conversation entry

To attempt an import:

1. Go to the **Import** tab
2. Click **+ New Import**
3. Select provider and API key
4. Click **Start Import**

### 4. Browse Conversations

1. Use the **Conversations** tab to browse all imported conversations
2. Filter by:
   - Search text (searches titles and message content)
   - Provider
   - Project
3. Click any conversation to view details

### 5. Export to Markdown

1. Open a conversation detail view
2. Click **📥 Export to Markdown**
3. A `.md` file will be downloaded with the full conversation

## API Documentation

Once the server is running, visit **http://localhost:7025/docs** for interactive API documentation (Swagger UI).

### Key Endpoints

- `GET /api/providers` - List available providers
- `GET /api/conversations` - List conversations (with filters)
- `GET /api/conversations/{id}` - Get conversation details
- `POST /api/api-keys` - Add new API key
- `POST /api/projects` - Create project
- `POST /api/import-jobs` - Start import job

## Development

### Running in Development Mode

The application runs in development mode by default (set in `.env`):

```env
ENV=development
```

This enables:
- Auto-reload on code changes
- CORS for frontend development
- Detailed error messages

### Database Migrations

Create a new migration after model changes:

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Adding New Providers

To add support for a new LLM provider:

1. Create a new adapter in `backend/app/providers/` implementing `ConversationProviderAdapter`
2. Register it in `backend/app/providers/registry.py`
3. Add provider metadata to the database seed data

## Architecture

### Provider Adapter Pattern

Each provider implements a common interface:

```python
class ConversationProviderAdapter(ABC):
    async def list_conversations(api_key, options) -> List[ProviderConversationSummary]
    async def fetch_conversation(api_key, conversation_id) -> ProviderConversationDetail
    async def fetch_artifacts(api_key, conversation_detail) -> List[ProviderArtifact]
```

This allows the core system to work with any provider without knowing implementation details.

### Data Model

- **providers** - LLM providers (OpenAI, Anthropic, etc.)
- **api_keys** - Encrypted API keys for each provider
- **conversations** - Imported conversation threads
- **messages** - Individual messages within conversations
- **artifacts** - Attachments and files
- **projects** - User-defined conversation groupings
- **import_jobs** - Background import job tracking
- **conversation_edits** - Curated/edited versions (v1.1+)

## Security Considerations

- **Local Only**: Server binds to `127.0.0.1` by default
- **Encrypted Keys**: API keys encrypted using Fernet (symmetric encryption)
- **No Cloud**: All data stays on your local machine
- **PostgreSQL**: Use strong database credentials
- **HTTPS**: For production, run behind nginx with SSL

## Troubleshooting

### Database Connection Errors

Check your `.env` file has the correct PostgreSQL credentials:

```bash
psql -U your_username -d conversation_vault -c "SELECT 1;"
```

### Port Already in Use

Change the port in `.env`:

```env
PORT=8080
```

### Import Jobs Not Working

Current implementation requires provider APIs that don't yet exist. Check:
- API key is active
- Provider adapter implementation
- Background task logs in console

## Roadmap

### v1.0 (Current)
- ✅ Basic conversation import framework
- ✅ Conversation browsing and search
- ✅ Project organization
- ✅ Markdown export
- ✅ API key management

### v1.1 (Planned)
- [ ] File-based import for OpenAI/Anthropic exports
- [ ] Conversation editing and curation
- [ ] Enhanced search (full-text indexing)
- [ ] Bulk operations
- [ ] Advanced filtering

### v1.2 (Future)
- [ ] Semantic search with embeddings
- [ ] Conversation analytics
- [ ] Multi-user support
- [ ] More provider integrations

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - see LICENSE file for details

## Support

For issues or questions, please open an issue on GitHub.

---

**Built with**: FastAPI, PostgreSQL, SQLAlchemy, Vanilla JavaScript
