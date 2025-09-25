# Voice Agent Dashboard

A full-stack application for managing voice agents and testing calls with Retell AI integration. The system consists of a React frontend for user interaction and a FastAPI backend for API integration and data management.

## 🎯 Overview

This application enables users to:
- **Configure AI Voice Agents** with custom prompts and conversation logic
- **Start Test Calls** using web-based voice communication
- **Monitor Call Status** and fetch results in real-time
- **View Call Transcripts** and analysis data
- **Manage Call Records** with database synchronization

## 🏗️ Architecture

```
Voice Agent Dashboard/
├── Frontend/              # React web application
│   └── my-react-app/     # Voice agent dashboard UI
├── Backend/              # FastAPI service
│   ├── services/         # Business logic layer
│   ├── models.py         # Data models
│   ├── main.py          # API endpoints
│   └── database/        # Schema and migrations
└── README.md            # This file
```

## ✨ Features

### Frontend (React)
- **Agent Configuration Interface** - Create custom prompts and conversation logic
- **Call Management Dashboard** - Start calls and monitor status
- **Manual Call Lookup** - Search and sync existing calls (collapsible panel)
- **Interactive Call Results** - Transcript viewer and analysis display
- **Web Call Interface** - Browser-based voice calling with Retell AI SDK
- **Pakistani Phone Formatting** - Automatic +92 country code handling
- **Responsive Design** - Clean, professional UI with animations

### Backend (FastAPI)
- **Retell AI Integration** - Complete API integration for agents and calls
- **Web Call Management** - Create and manage browser-based voice calls
- **Database Operations** - Supabase PostgreSQL with real-time features
- **Webhook Processing** - Handle Retell AI call events automatically
- **Call Synchronization** - Import calls from Retell AI to local database
- **Comprehensive Logging** - Detailed error handling and request tracking

## 🚀 Getting Started

### Prerequisites
- **Node.js** 16+ and npm
- **Python** 3.8+ and pip
- **Supabase** account and project
- **Retell AI** account with API key

### Quick Setup

1. **Clone and navigate to project**
   ```bash
   cd "D:\Practice\Retell AI"
   ```

2. **Set up Backend**
   ```bash
   cd Backend

   # Create .env file
   echo "RETELL_API_KEY=your_retell_api_key_here" > .env
   echo "RETELL_WEBHOOK_SECRET=your_webhook_secret" >> .env
   echo "SUPABASE_URL=https://your-project.supabase.co" >> .env
   echo "SUPABASE_KEY=your_supabase_anon_key" >> .env

   # Install dependencies
   pip install -r requirements.txt

   # Start backend server
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Set up Database**
   ```sql
   -- In Supabase SQL Editor, run:
   -- 1. Execute: supabase_schema.sql
   -- 2. Execute: migration_update_call_records.sql
   ```

4. **Set up Frontend**
   ```bash
   cd "../Frontend/my-react-app"

   # Install dependencies
   npm install

   # Start development server
   npm start
   ```

5. **Access Application**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs

## 📡 API Endpoints

### Call Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/call/start` | Start new test call |
| `GET` | `/api/call/{call_id}/status` | Get call status |
| `GET` | `/api/calls/{call_id}` | Get call details |
| `POST` | `/api/call/{call_id}/sync` | Sync call from Retell AI |

### Agent Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agent/create` | Create new agent |
| `GET` | `/api/agents` | List all agents |
| `GET` | `/api/agent/{agent_id}` | Get agent details |

### System Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/test/retell-config` | Test configuration |
| `POST` | `/webhook/retell` | Retell AI webhooks |

## 💾 Database Schema

### Core Tables
- **call_records** - Call history, transcripts, and metadata
- **conversation_prompts** - Agent prompt templates
- **agent_prompts** - Agent-prompt relationships
- **retell_agents** - Created agent tracking
- **retell_llms** - Created LLM tracking

### Key Features
- **Automatic timestamps** with triggers
- **JSONB storage** for call analysis
- **Foreign key relationships** for data integrity
- **Comprehensive indexes** for performance
- **Useful views** for reporting

## 🔧 Configuration

### Environment Variables (.env)
```env
# Retell AI Configuration
RETELL_API_KEY=your_retell_api_key_here
RETELL_WEBHOOK_SECRET=your_webhook_secret_here
RETELL_FROM_NUMBER=+1234567890

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
```

### Frontend API Configuration
Update API endpoints in React components if using different URLs:
```javascript
// Default: http://localhost:8000
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

## 🔄 Application Flow

1. **Agent Configuration**
   - User creates custom prompt and conversation logic
   - Frontend stores configuration in state

2. **Call Initiation**
   - User enters driver information (name, phone, load number)
   - System automatically formats Pakistani phone numbers
   - Frontend sends request to backend API

3. **Backend Processing**
   - Creates LLM with custom prompt
   - Creates agent with voice configuration
   - Initiates web call with Retell AI
   - Returns call ID and access token

4. **Web Call Connection**
   - User can connect via browser using access token
   - Real-time voice communication through Retell AI SDK
   - Call status updates automatically

5. **Results Processing**
   - Call completion triggers webhook events
   - Backend processes transcripts and analysis
   - Frontend displays structured results
   - Data stored in database for future reference

## 📱 Component Details

### Frontend Components

#### AgentConfig.js
- **Purpose**: Configure voice agent behavior
- **Features**: Prompt editing, logic definition, preview

#### CallTrigger.js
- **Purpose**: Manage call initiation and monitoring
- **Features**:
  - Driver information form with phone formatting
  - Start test call functionality
  - Manual call ID lookup (collapsible panel)
  - Call status monitoring and sync

#### CallResults.js
- **Purpose**: Display call outcomes and analysis
- **Features**:
  - Key information grid
  - Interactive transcript viewer
  - Access token management (show/hide)
  - Web call interface integration

#### WebCallInterface.js
- **Purpose**: Browser-based voice calling
- **Features**:
  - Retell AI SDK integration
  - Real-time connection status
  - Microphone access management
  - Debug information panel

### Backend Services

#### retell_service.py
- **Purpose**: Retell AI API integration
- **Features**: Agent creation, call management, error handling

#### transcript_processor.py
- **Purpose**: Call data processing and storage
- **Features**: Transcript parsing, database operations, datetime handling

#### prompt_interpreter.py
- **Purpose**: Prompt and conversation management
- **Features**: Template processing, agent-prompt relationships

## 🎨 UI/UX Features

### Design System
- **Professional color palette** (blue, green, yellow themes)
- **Card-based layout** with clear visual hierarchy
- **Responsive design** for different screen sizes
- **Smooth animations** for state transitions

### User Experience
- **Collapsible panels** to reduce visual clutter
- **Loading states** for all async operations
- **Status indicators** with color coding
- **Error handling** with user-friendly messages
- **Form validation** and auto-formatting

### Accessibility
- **Semantic HTML** structure
- **ARIA labels** for screen readers
- **Keyboard navigation** support
- **High contrast** color schemes

## 🔍 Special Features

### Pakistani Phone Number Support
- **Auto-formatting**: `03001234567` → `+923001234567`
- **E.164 compliance** for international calling
- **Multiple input formats** supported

### Call Synchronization
- **Manual sync** from Retell AI to local database
- **Automatic fallback** to Retell AI when call not found locally
- **Status updates** with real-time monitoring

### Web Call Integration
- **Browser-based calling** without phone infrastructure
- **SDK auto-loading** with error recovery
- **Debug information** for troubleshooting
- **Real-time status** updates

## 🛠️ Development

### Frontend Development
```bash
cd Frontend/my-react-app
npm start          # Development server
npm run build      # Production build
npm test          # Run tests
```

### Backend Development
```bash
cd Backend
uvicorn main:app --reload    # Development server with auto-reload
python -m pytest           # Run tests (if configured)
```

### Database Migrations
1. Create migration SQL file
2. Test on development database
3. Update models.py accordingly
4. Document changes

## 🚀 Deployment

### Production Checklist
- [ ] Set production environment variables
- [ ] Configure CORS for specific domains
- [ ] Set up SSL certificates
- [ ] Configure reverse proxy (nginx)
- [ ] Set up monitoring and logging
- [ ] Configure database backups
- [ ] Test webhook endpoints

### Docker Deployment
```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Frontend Dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
EXPOSE 80
```

## 🐛 Troubleshooting

### Common Issues

#### API Connection Errors
- **Check**: Backend server running on port 8000
- **Verify**: CORS configuration allows frontend domain
- **Review**: Network connectivity and firewall settings

#### Web Call Not Working
- **Ensure**: Microphone permissions granted in browser
- **Check**: Browser console for SDK loading errors
- **Verify**: Valid access token from backend

#### Call Status Not Updating
- **Confirm**: Network connectivity stable
- **Verify**: Call ID format and existence
- **Try**: Manual sync from Retell AI

#### Database Connection Issues
- **Check**: Supabase URL and key configuration
- **Verify**: Database permissions and network access
- **Review**: Connection pool settings

### Debug Tools
- **Browser Console**: Error messages and network requests
- **API Documentation**: Interactive testing at `/docs`
- **Database Dashboard**: Supabase real-time monitoring
- **Component Debug Panels**: SDK status and browser info

## 📊 Monitoring

### Health Checks
- **Backend Health**: `GET /health`
- **Configuration Test**: `GET /api/test/retell-config`
- **Connection Test**: `GET /api/test/retell-connection`

### Logging Strategy
- **Request/Response** logging for Retell AI calls
- **Error tracking** with full stack traces
- **Database operations** logging
- **Performance metrics** monitoring

## 🤝 Contributing

1. **Follow Framework Conventions**
   - React hooks and functional components
   - FastAPI async/await patterns
   - Python type hints and Pydantic models

2. **Code Quality Standards**
   - Comprehensive error handling
   - User-friendly error messages
   - Consistent styling and formatting
   - Proper state management

3. **Documentation Requirements**
   - Update API documentation for new endpoints
   - Add component documentation for UI changes
   - Include troubleshooting guides for new features
   - Update this README for architectural changes

## 📄 License

This project is for internal use and demonstration purposes.

---

## Quick Reference

### Start Development
```bash
# Terminal 1 - Backend
cd Backend && uvicorn main:app --reload

# Terminal 2 - Frontend
cd Frontend/my-react-app && npm start
```

### Access Points
- **Application**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Key Technologies
- **Frontend**: React 18, CSS3, Retell AI Web SDK
- **Backend**: FastAPI, Pydantic, httpx
- **Database**: Supabase PostgreSQL
- **Integration**: Retell AI Voice Platform