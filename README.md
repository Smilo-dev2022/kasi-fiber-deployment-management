# FIBER PON Tracker App

A comprehensive web application for training and tracking Project Managers and Site Managers on FiberTime sites. The app tracks PONs (Passive Optical Networks), tasks, CAC checks, stringing, photos, SMMEs, stock, and invoicing with evidence enforcement and auto-status computation.

## Features

- **User Management**: Authentication for Project Managers and Site Managers
- **PON Tracking**: Complete PON lifecycle management with progress tracking
- **Task Management**: Task assignment, tracking, and status management
- **Evidence Enforcement**: Photo upload requirements for task completion
- **Auto-Status Computation**: Automatic progress calculation based on task completion
- **Report Export**: CSV export functionality for PON and task data
- **Dashboard**: Real-time statistics and overview
- **Role-based Access**: Different permissions for different user roles

## Technology Stack

- **Backend**: FastAPI (Python) primary API, plus legacy Node.js (server/) optional
- **Frontend**: React.js with Material-UI
- **Database**: PostgreSQL via SQLAlchemy
- **Authentication**: Role header `X-Role` for FastAPI; JWT on legacy Node
- **File Upload**: S3-compatible storage for photos
- **Styling**: Material-UI components

## Project Structure

```
├── server/                    # Backend API
│   ├── config/               # Database configuration
│   ├── models/               # MongoDB models
│   ├── routes/               # API routes
│   ├── middleware/           # Authentication middleware
│   └── index.js              # Server entry point
├── client/                   # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── contexts/         # React contexts
│   │   └── App.js            # Main app component
│   └── public/               # Static files
└── uploads/                  # Photo uploads directory
```

## Installation & Setup

### Prerequisites
- Node.js (v14 or higher)
- MongoDB (local or cloud instance)
- npm or yarn

### FastAPI Backend Setup
1. Create and export environment variables as needed:
   - `DATABASE_URL` (PostgreSQL)
   - `CORS_ALLOWLIST` (comma-separated origins)
   - `MAX_UPLOAD_MB` (default 10)
   - `HOURS_EXIF_WINDOW` (default 24)
   - `NMS_WHITELIST_IPS` and `NMS_WEBHOOK_SECRET`
   - `S3_ENDPOINT`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`
2. Install Python deps and run:
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Frontend Setup
1. Navigate to client directory:
   ```bash
   cd client
   npm install
   ```

2. Start the React development server:
   ```bash
   npm start
   ```

### Full Development Mode
Run FastAPI and client separately; Node server optional.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/user` - Get current user

### PON Management
- `GET /api/pons` - Get PONs (filtered by user role)
- `POST /api/pons` - Create new PON
- `PUT /api/pons/:id` - Update PON
- `GET /api/pons/:id` - Get PON details
- `PUT /api/pons/:id/progress` - Update PON progress

### Task Management
- `GET /api/tasks` - Get tasks (filtered by user role)
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/:id/status` - Update task status

### Photo Evidence
- `POST /api/photos/upload/:taskId` - Upload photo evidence
- `GET /api/photos/task/:taskId` - Get task photos

### Reports
- `GET /api/reports/dashboard` - Dashboard statistics
- `GET /api/reports/pons` - PON report data
- `GET /api/reports/export/pons` - Export PON data as CSV

## User Roles

### Project Manager
- Create and manage PONs
- Assign tasks to Site Managers
- View all PONs under their management
- Access reports and analytics

### Site Manager
- View assigned PONs and tasks
- Update task status
- Upload photo evidence
- Complete tasks with evidence requirements

## Usage

### Getting Started
1. Register a new account (Project Manager or Site Manager)
2. Project Managers can create PONs and assign tasks
3. Site Managers can view and complete assigned tasks
4. Upload photo evidence for tasks that require it
5. Monitor progress through the dashboard
6. Export reports for documentation

### Photo Evidence
- Tasks can require photo evidence for completion
- Photos are automatically linked to tasks
- Tasks with evidence requirements cannot be marked complete without photos
- Evidence tracking helps ensure quality control

### Auto-Status Computation
- PON progress is automatically calculated based on task completion
- PON status updates automatically (planned → in_progress → completed)
- Real-time dashboard updates reflect current progress

## Development

### Adding New Features
1. Create database models in `server/models/`
2. Add API routes in `server/routes/`
3. Create React components in `client/src/components/`
4. Update navigation and routing as needed

### Testing
- Backend: Test API endpoints using tools like Postman
- Frontend: Use browser developer tools and React Developer Tools
- Build: Run `npm run build` to test production build

## Deployment

### Production Build
```bash
# Build client
cd client
npm run build

# The built files will be served by the Express server
cd ..
npm start
```

### Environment Variables
Ensure production environment variables are set:
- `NODE_ENV=production`
- `MONGODB_URI` (production database)
- `JWT_SECRET` (strong secret key)

## Future Enhancements

Planned features for upcoming releases:
- [ ] CAC (Central Access Control) checks module
- [ ] Stringing operations tracking
- [ ] SMME (Small, Medium & Micro Enterprises) management
- [ ] Stock management system
- [ ] Invoicing system
- [ ] Advanced reporting with charts
- [ ] Mobile app support
- [ ] Real-time notifications
- [ ] GPS integration for location tracking
- [ ] Advanced photo organization and tagging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details
