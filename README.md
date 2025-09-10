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

- **Backend**: Node.js with Express.js
- **Frontend**: React.js with Material-UI
- **Database**: MongoDB (configurable)
- **Authentication**: JWT tokens
- **File Upload**: Multer for photo evidence
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

### Backend Setup
1. Install dependencies:
   ```bash
   npm install
   ```

2. Create environment file:
   ```bash
   cp .env.example .env
   ```

3. Configure environment variables in `.env`:
   - `MONGODB_URI`: Your MongoDB connection string
   - `JWT_SECRET`: Secret key for JWT tokens
   - `PORT`: Server port (default: 5000)

4. Start the server:
   ```bash
   npm start
   # or for development with auto-reload:
   npm run server
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
Run both backend and frontend simultaneously:
```bash
npm run dev
```

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

### Multi-tenant & White-label (FastAPI + Postgres)
- Isolation enforced via PostgreSQL RLS using `app.tenant_id`
- Resolve tenant via `X-Tenant-Id` header or mapped domain (`tenant_domains`)
- Themes, feature flags, audit logs, metering counters per tenant

Run DB migrations (requires Postgres):
```bash
alembic upgrade head
```

Headers to include on API requests:
- `X-Tenant-Id: <tenant-uuid>`
- `X-Role: ADMIN|PM|SITE|SMME`

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
