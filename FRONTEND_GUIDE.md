# Frontend Implementation Guide

## 📁 Project Structure

```
frontend/
├── src/
│   ├── App.jsx                 # Main app component
│   ├── main.jsx               # Entry point
│   ├── App.css                # Global styles
│   │
│   ├── pages/                 # Page components
│   │   ├── LoginPage.jsx      # Login page
│   │   ├── RegisterPage.jsx   # Registration page
│   │   ├── Dashboard.jsx      # Main dashboard
│   │   ├── CandidateDashboard.jsx  # Candidate-specific
│   │   └── RecruiterDashboard.jsx  # Recruiter-specific
│   │
│   ├── components/            # Reusable components
│   │   ├── Header.jsx         # Navigation header
│   │   └── PrivateRoute.jsx   # Route protection
│   │
│   ├── services/              # API services
│   │   ├── api.js             # Axios instance
│   │   ├── authService.js     # Auth endpoints
│   │   ├── candidateService.js
│   │   ├── recruiterService.js
│   │   ├── resumeService.js
│   │   └── subscriptionService.js
│   │
│   ├── context/               # React Context
│   │   └── AuthContext.jsx    # Auth state management
│   │
│   ├── hooks/                 # Custom hooks (expandable)
│   │   └── (To be added)
│   │
│   └── index.css              # Global CSS
│
├── package.json               # Dependencies
├── vite.config.js            # Vite configuration
├── tailwind.config.js        # Tailwind configuration
├── postcss.config.js         # PostCSS configuration
├── index.html                # HTML template
├── .env                      # Environment variables
└── .env.example              # Example env file
```

## 🎨 Component Hierarchy

```
App
├── AuthProvider
│   ├── Header
│   └── Routes
│       ├── PublicRoute
│       │   ├── LoginPage
│       │   └── RegisterPage
│       └── PrivateRoute
│           └── Dashboard
│               ├── CandidateDashboard
│               │   ├── ProfileTab
│               │   ├── ExperienceTab
│               │   ├── EducationTab
│               │   └── ResumesTab
│               └── RecruiterDashboard
│                   ├── SearchCandidates
│                   ├── CandidateCard
│                   ├── CandidateDetailModal
│                   └── EmailModal
```

## 🔄 State Management

### AuthContext
Manages global authentication state:

```javascript
{
  user: {
    id,
    email,
    first_name,
    last_name,
    role,
    subscription_type,
    is_active
  },
  login,        // (email, password) => Promise
  register,     // (data) => Promise
  logout,       // () => void
  loading,      // boolean
  error         // string | null
}
```

### React Query
Manages server state for data fetching:
- Automatic caching
- Background refetching
- Error handling
- Loading states

## 🔧 Styling

### Tailwind CSS
Utility-first CSS framework:
- No component classes
- Responsive design
- Dark mode ready
- Custom theme extension

### Responsive Breakpoints
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

## 📱 Key Features Implementation

### 1. Authentication Flow
```javascript
// pages/LoginPage.jsx
- Email/password form
- Error handling
- Loading state
- Redirect on success
```

### 2. Candidate Dashboard
```javascript
// pages/CandidateDashboard.jsx
- Profile overview with stats
- Tab navigation
- Resume upload with validation
- Experience/Education management
- Upgrade modal for PRO features
```

### 3. Recruiter Dashboard
```javascript
// pages/RecruiterDashboard.jsx
- Search form with filters
- Candidate card grid
- Pagination
- Modal for detailed view
- Email composition modal
```

### 4. Resume Upload
```javascript
// ResumesTab component
- File input validation
- Progress feedback
- Parsing status display
- Error handling
```

## 🔐 Security Considerations

### Frontend Security
1. **Token Storage**
   - localStorage for JWT token
   - Consider sessionStorage for stricter security

2. **CORS**
   - Configured in backend
   - Handles cross-origin requests

3. **Input Validation**
   - Pydantic schemas on backend
   - Frontend pre-validation with HTML5

4. **HTTPS**
   - Required in production
   - Update API endpoints

## 🚀 Performance Optimizations

### Current
- Lazy loading of pages with React Router
- Component memoization opportunities
- Efficient re-renders with hooks

### Future Enhancements
- Code splitting with `@vitejs/plugin-react`
- Image optimization
- Virtual scrolling for large lists
- Service worker for offline support

## 🧪 Testing Frontend

### Unit Tests (Recommended additions)
```bash
npm install -D @testing-library/react @testing-library/jest-dom vitest
```

### Example Test
```javascript
import { render, screen } from '@testing-library/react';
import { LoginPage } from './LoginPage';

test('renders login form', () => {
  render(<LoginPage />);
  expect(screen.getByText('Email')).toBeInTheDocument();
});
```

### E2E Tests (Future)
```bash
npm install -D cypress
```

Use Cypress for full user workflows.

## 📦 Build and Deployment

### Development
```bash
npm run dev
```
Runs on http://localhost:5173 with hot module reload

### Production Build
```bash
npm run build
```
Creates optimized build in `dist/`

### Preview Build
```bash
npm run preview
```
Serves production build locally

### Deployment Steps
1. Build: `npm run build`
2. Deploy `dist/` folder to:
   - Vercel
   - Netlify
   - AWS S3 + CloudFront
   - Azure Static Web Apps
   - Any static hosting

## 🔌 API Integration

### Service File Pattern
```javascript
// services/candidateService.js
export default {
  getProfile: () => client.get('/candidates/me'),
  addExperience: (data) => client.post('/candidates/experience', data),
  // ... more methods
};
```

### Usage in Components
```javascript
const { data } = useQuery({
  queryKey: ['profile'],
  queryFn: () => candidateService.getProfile()
});
```

## 🎯 Developer Tips

### Hot Module Reloading
Changes to JSX/CSS automatically reload without losing state

### React DevTools
Install browser extension for debugging component tree:
```
React Developer Tools (Chrome/Firefox)
```

### Debugging API Calls
Access Network tab in browser DevTools to inspect:
- Request/response headers
- Authorization token
- Request/response body
- Response status

### Environment Variables
Define in `.env`:
```
VITE_API_URL=http://localhost:8000/api
```

Access in code:
```javascript
const API_URL = import.meta.env.VITE_API_URL;
```

## 📝 Component Development Guidelines

### Naming Conventions
- Components: PascalCase (e.g., `LoginPage.jsx`)
- Functions: camelCase
- Constants: UPPER_SNAKE_CASE

### Component Template
```javascript
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export const MyComponent = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  
  useEffect(() => {
    // Side effects
  }, []);
  
  return (
    <div className="...">
      {/* JSX */}
    </div>
  );
};
```

### Props Destructuring
```javascript
export const Card = ({ title, description, onAction }) => {
  return (
    <div>
      <h2>{title}</h2>
      <p>{description}</p>
      <button onClick={onAction}>Action</button>
    </div>
  );
};
```

## 🔄 Common Patterns

### Form Handling
```javascript
const [formData, setFormData] = useState({
  email: '',
  password: ''
});

const handleChange = (e) => {
  const { name, value } = e.target;
  setFormData(prev => ({ ...prev, [name]: value }));
};

const handleSubmit = async (e) => {
  e.preventDefault();
  // API call
};
```

### Conditional Rendering
```javascript
{user && <Component />}
{loading ? <Loader /> : <Content />}
{items.length > 0 ? <List /> : <EmptyState />}
```

### Error Handling
```javascript
try {
  await service.method();
} catch (err) {
  setError(err.response?.data?.error?.message || 'Error occurred');
}
```

## 📚 Useful Libraries

Currently included:
- `react`: UI framework
- `react-router-dom`: Routing
- `axios`: HTTP client
- `@tanstack/react-query`: State management
- `tailwindcss`: Styling

Optional additions:
- `react-hook-form`: Form management
- `zod`: Schema validation
- `zustand`: State management alternative
- `framer-motion`: Animations

---

**Happy coding! 🚀**
