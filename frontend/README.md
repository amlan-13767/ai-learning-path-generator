# AI Learning Path Generator - Frontend

Modern React frontend for the AI Learning Path Generator with real-time progress tracking and beautiful glassmorphic UI.

## 🚀 Features

- **Modern React + Vite** - Lightning-fast development and builds
- **TailwindCSS + shadcn/ui** - Beautiful, accessible components
- **Real-time Progress Tracking** - Live updates as your learning path is generated
- **Glassmorphic Design** - Stunning visual effects with backdrop blur
- **Job Market Insights** - See salary ranges, open positions, and related careers
- **Responsive Design** - Works perfectly on desktop, tablet, and mobile
- **Export Functionality** - Download your learning path as JSON

## 📦 Tech Stack

- React 18
- Vite 5
- TailwindCSS 3
- shadcn/ui components
- Axios for API calls
- Lucide React for icons

## 🛠️ Local Development

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running (see `/backend` folder)

### Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```
   VITE_API_URL=http://localhost:5000
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   ```
   http://localhost:3000
   ```

## 🏗️ Build for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` folder.

## 🚀 Deploy to Vercel

### Quick Deploy (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add Phase 2 frontend"
   git push origin main
   ```

2. **Deploy on Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repo
   - Set root directory to `frontend`
   - Add environment variable:
     ```
     VITE_API_URL=https://ai-learning-path-api.onrender.com
     ```
   - Click "Deploy"

### Manual Deploy

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel --prod
```

## 📁 Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── ui/         # shadcn/ui components
│   │   ├── LearningPathForm.jsx
│   │   ├── ProgressTracker.jsx
│   │   └── LearningPathResult.jsx
│   ├── lib/            # Utilities
│   │   ├── api.js      # API client
│   │   └── utils.js    # Helper functions
│   ├── App.jsx         # Main app component
│   ├── main.jsx        # Entry point
│   └── index.css       # Global styles
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── vercel.json         # Vercel configuration
```

## 🎨 Components

### LearningPathForm
Input form for learning path parameters:
- Topic
- Expertise level
- Duration
- Time commitment
- Goals

### ProgressTracker
Real-time progress tracking with:
- Progress bar
- Status messages
- Stage indicators
- Estimated time

### LearningPathResult
Displays the generated learning path with:
- Overview stats
- Job market insights
- Schedule information
- Expandable milestones
- Learning resources
- Export functionality

## 🔧 Configuration

### API URL
Set in `.env` file:
```
VITE_API_URL=https://your-api-url.com
```

### Styling
- Customize colors in `tailwind.config.js`
- Modify glassmorphic effects in `src/index.css`
- Component styles use Tailwind utility classes

## 📝 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://ai-learning-path-api.onrender.com` |

## 🧪 Testing Locally with Backend

1. Start backend API:
   ```bash
   cd backend
   python app.py
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open http://localhost:3000

The frontend will proxy `/api` requests to the backend automatically.

## 🐛 Troubleshooting

**API connection errors:**
- Check that `VITE_API_URL` is set correctly
- Verify backend is running and accessible
- Check browser console for CORS errors

**Build errors:**
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node version: `node --version` (should be 18+)

**Styling issues:**
- Run: `npm run build` to regenerate Tailwind CSS
- Check for conflicting CSS classes

## 📚 Learn More

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [TailwindCSS](https://tailwindcss.com)
- [shadcn/ui](https://ui.shadcn.com)
- [Vercel Deployment](https://vercel.com/docs)

## 🎉 Success Criteria

Frontend is complete when:
- ✅ Form submits and queues tasks
- ✅ Progress tracker shows real-time updates
- ✅ Results display with all data
- ✅ Responsive on all screen sizes
- ✅ Deployed to Vercel
- ✅ Connected to production API

---

**Built with ❤️ using React + Vite**
