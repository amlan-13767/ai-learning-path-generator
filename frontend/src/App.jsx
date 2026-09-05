import { useEffect, useState } from 'react';
import {
  ArrowRight, BarChart3, BookOpen, Briefcase, Check, ChevronRight,
  HelpCircle, Clock3, Compass, LayoutDashboard, Menu, MessageSquare, Plus,
  Send, Sparkles, Target, X, Zap,
} from 'lucide-react';
import LearningPathForm from './components/LearningPathForm';
import ProgressTracker from './components/ProgressTracker';
import LearningPathResult from './components/LearningPathResult';
import { askQuestion, checkTaskStatus, generateLearningPath, getTaskResult, getUserPaths, loginRequired } from './lib/api';
import { linkHandler, navigate, usePathname } from './lib/navigation';
import { useAuth } from './auth/AuthContext';
import { AuthLoading, ForgotPasswordPage, LoginPage, RegisterPage, UnauthorizedPage } from './pages/AuthPages';

const navigation = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'build', label: 'Build a path', icon: Sparkles },
  { id: 'paths', label: 'My paths', icon: BookOpen },
  { id: 'career', label: 'Career signals', icon: Briefcase },
  { id: 'tutor', label: 'AI tutor', icon: MessageSquare },
];

function App() {
  const { user, loading: authLoading, logout } = useAuth();
  const pathname = usePathname();
  const isAuthPage = ['/login', '/register', '/forgot-password'].includes(pathname);
  const protectedRoute = pathname === '/dashboard' || pathname === '/my-paths' || pathname === '/profile' || pathname.startsWith('/path/');
  const [activeView, setActiveView] = useState(pathToView(pathname));
  const [stage, setStage] = useState('form');
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => { setActiveView(pathToView(pathname)); }, [pathname]);

  useEffect(() => {
    if (!user) return;
    getUserPaths().then((paths) => {
      if (paths.paths?.[0]?.path) setResult(paths.paths[0].path);
    }).catch((pathError) => { if (!loginRequired(pathError)) console.error('Unable to restore saved paths:', pathError); });
  }, [user]);

  useEffect(() => {
    if (!taskId || stage !== 'processing') return undefined;
    const pollInterval = setInterval(async () => {
      try {
        const statusData = await checkTaskStatus(taskId);
        setTaskStatus(statusData.status);
        if (statusData.status === 'finished') {
          clearInterval(pollInterval);
          setResult(await getTaskResult(taskId));
          setStage('result');
          setActiveView('paths');
        } else if (statusData.status === 'failed') {
          clearInterval(pollInterval);
          setError(statusData.error || 'Task failed. Please try again.');
          setStage('error');
        }
      } catch (pollError) {
        clearInterval(pollInterval);
        if (loginRequired(pollError)) { navigate('/login?next=/build'); return; }
        console.error('Error polling status:', pollError);
        setError('Failed to check task status. Please try again.');
        setStage('error');
      }
    }, 3000);
    return () => clearInterval(pollInterval);
  }, [taskId, stage]);

  const handleSubmit = async (formData) => {
    if (!user) {
      // Stay inside React. This previously did a full-page navigation to the
      // Flask origin, which is what surfaced the old purple UI.
      navigate('/login?next=/build');
      return;
    }
    setError(null); setStage('processing'); setActiveView('build');
    try {
      const response = await generateLearningPath(formData);
      setTaskId(response.task_id); setTaskStatus(response.status);
    } catch (submissionError) {
      console.error('Error generating learning path:', submissionError);
      if (loginRequired(submissionError)) {
        navigate('/login?next=/build');
        return;
      }
      const backendMessage = submissionError.response?.data?.error;
      const message = !submissionError.response
        ? 'Cannot reach the API. Start the Flask backend and try again.'
        : backendMessage || 'The backend could not queue this path. Check Redis and the worker, then try again.';
      setError(message);
      setStage('error');
    }
  };

  const startNewPath = () => { setStage('form'); setTaskId(null); setTaskStatus(null); setResult(null); setError(null); setActiveView('build'); };
  const selectView = (view) => { setActiveView(view); setMobileNavOpen(false); navigate(viewToPath(view)); if (view === 'build' && stage === 'result') setStage('form'); };

  if (authLoading && !isAuthPage) return <AuthLoading />;
  if (pathname === '/login') return <LoginPage />;
  if (pathname === '/register') return <RegisterPage />;
  if (pathname === '/forgot-password') return <ForgotPasswordPage />;
  if (protectedRoute && !user) return <UnauthorizedPage />;
  return <div className="app-shell">
    <div className="ambient ambient-one" /><div className="ambient ambient-two" />
    <aside className={`sidebar ${mobileNavOpen ? 'sidebar-open' : ''}`}>
      <div className="brand-lockup"><div className="brand-mark"><Sparkles size={17} /></div><span>learn<span className="accent-text">/ai</span></span></div>
      <div className="workspace-label">Your workspace</div>
      <nav className="side-nav" aria-label="Primary navigation">{navigation.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${activeView === id ? 'nav-item-active' : ''}`} onClick={() => selectView(id)}><Icon size={17} /><span>{label}</span>{id === 'tutor' && <span className="nav-pulse" />}</button>)}</nav>
      <div className="sidebar-bottom">{user ? <button className="support-link" onClick={async () => { await logout(); navigate('/login'); }}><HelpCircle size={16} /> Sign out</button> : <><a className="support-link" href="/login" onClick={linkHandler('/login')}><HelpCircle size={16} /> Sign in</a><a className="support-link" href="/register" onClick={linkHandler('/register')}><Plus size={16} /> Create account</a></>}<div className="profile-chip"><div className="avatar">{user?.username?.[0]?.toUpperCase() || 'G'}</div><div><strong>{user?.display_name || user?.username || 'Guest learner'}</strong><span>{user ? user.email : 'Sign in to save progress'}</span></div></div></div>
    </aside>
    <main className="main-panel">
      <header className="topbar"><button className="mobile-menu icon-button" aria-label="Open navigation" onClick={() => setMobileNavOpen(true)}><Menu size={19} /></button><div className="breadcrumbs"><span>Workspace</span><ChevronRight size={14} /><strong>{navigation.find((item) => item.id === activeView)?.label}</strong></div><div className="topbar-actions"><button className="icon-button" aria-label="Help"><HelpCircle size={17} /></button><button className="topbar-avatar">G</button></div>{mobileNavOpen && <button className="mobile-close icon-button" aria-label="Close navigation" onClick={() => setMobileNavOpen(false)}><X size={19} /></button>}</header>
      <div className="content-wrap">
        {activeView === 'overview' && <Overview result={result} onBuild={() => selectView('build')} onOpenPath={() => selectView('paths')} />}
        {activeView === 'build' && <BuildView stage={stage} taskStatus={taskStatus} error={error} result={result} onSubmit={handleSubmit} onReset={startNewPath} />}
        {activeView === 'paths' && <PathsView result={result} onBuild={() => selectView('build')} onReset={startNewPath} />}
        {activeView === 'career' && <CareerView result={result} onBuild={() => selectView('build')} />}
        {activeView === 'tutor' && <TutorView result={result} />}
      </div>
    </main>
  </div>;
}

function Overview({ result, onBuild, onOpenPath }) {
  return <><section className="welcome-row"><div><p className="eyebrow">SATURDAY, SEPTEMBER 5</p><h1>Make your next skill <em>inevitable.</em></h1><p className="lede">A focused learning system that turns ambitious goals into a path you can actually follow.</p></div><button className="button button-primary" onClick={onBuild}>Build a learning path <ArrowRight size={17} /></button></section>
    <section className="hero-grid"><div className="hero-card glass-panel"><div className="hero-copy"><span className="status-kicker"><span className="live-dot" /> AI learning studio</span><h2>Learn with a plan<br /><span>made for you.</span></h2><p>Tell us where you want to go. We will map the concepts, practice, and momentum to get you there.</p><button className="button button-light" onClick={onBuild}>Start from a goal <ArrowRight size={16} /></button></div><RoadmapPreview /></div><div className="signal-card glass-panel"><div className="card-heading"><span>YOUR SIGNALS</span><BarChart3 size={16} /></div><div className="signal-score">{result ? '0' : '--'}<small>/ 100</small></div><p>Readiness score</p><div className="signal-bars"><span /><span /><span /><span /><span /></div><div className="signal-foot"><span>Build your first path</span><button onClick={onBuild}><ArrowRight size={16} /></button></div></div></section>
    <section className="section-heading"><div><p className="eyebrow">AT A GLANCE</p><h2>Your learning cockpit</h2></div><button className="text-button" onClick={onOpenPath}>View all paths <ArrowRight size={15} /></button></section><section className="metric-grid"><Metric icon={Zap} label="Current streak" value={result ? '1 day' : '0 days'} detail="Start a focused session" /><Metric icon={Clock3} label="Learning hours" value={result ? `${result.total_hours || 0}h` : '0h'} detail="Tracked across your paths" /><Metric icon={Target} label="Paths in motion" value={result ? '1' : '0'} detail={result ? result.topic : 'Your next chapter starts here'} accent /></section><div className="quiet-note"><Compass size={17} /><span>Every path is generated around your time, level, and destination. No generic curricula.</span></div></>;
}

function RoadmapPreview() { return <div className="roadmap-preview"><div className="preview-window"><div className="preview-top"><span /><span /><span /><small>PATH PREVIEW</small></div><div className="preview-title">From curious to capable <Sparkles size={14} /></div>{['Foundations', 'Applied practice', 'Build in public'].map((label, index) => <div className={`preview-node ${index === 1 ? 'preview-current' : ''}`} key={label}><div className="node-marker">{index === 0 ? <Check size={13} /> : index + 1}</div><div><strong>{label}</strong><small>{index === 1 ? 'Current focus' : `${index + 2} guided sessions`}</small></div></div>)}</div></div>; }
function Metric({ icon: Icon, label, value, detail, accent }) { return <div className={`metric-card glass-panel ${accent ? 'metric-accent' : ''}`}><div className="metric-icon"><Icon size={17} /></div><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>; }

function BuildView({ stage, taskStatus, error, result, onSubmit, onReset }) { return <section className="view-stack"><div className="page-intro"><div><p className="eyebrow">PATH BUILDER</p><h1>Design your next chapter.</h1><p>Five minutes of context gives the AI enough signal to build something personal.</p></div><div className="step-count"><span className="active-step">01</span><span> / 01</span><small>PATH BRIEF</small></div></div>{stage === 'form' && <LearningPathForm onSubmit={onSubmit} isLoading={false} />}{stage === 'processing' && <ProgressTracker status={taskStatus} error={null} />}{stage === 'result' && result && <LearningPathResult data={result} onReset={onReset} />}{stage === 'error' && <div className="error-panel glass-panel"><HelpCircle size={26} /><h2>We hit a pause.</h2><p>{error}</p><button className="button button-primary" onClick={onReset}>Try again <ArrowRight size={16} /></button></div>}</section>; }
function PathsView({ result, onBuild, onReset }) { if (!result) return <EmptyView eyebrow="MY PATHS" title="Your roadmap library is empty." copy="Build a path and it will live here, ready whenever you are." action="Build your first path" onClick={onBuild} />; return <section className="view-stack"><div className="page-intro"><div><p className="eyebrow">MY PATHS</p><h1>Your learning roadmap.</h1><p>One clear direction is better than ten open tabs.</p></div><button className="button button-primary" onClick={onReset}><Plus size={17} /> New path</button></div><LearningPathResult data={result} onReset={onReset} /></section>; }
function CareerView({ result, onBuild }) { const market = result?.job_market_data; if (!result) return <EmptyView eyebrow="CAREER SIGNALS" title="Turn a goal into career momentum." copy="Generate a path to see demand, related roles, and the skills that will move the needle." action="Explore a path" onClick={onBuild} />; return <section className="view-stack"><div className="page-intro"><div><p className="eyebrow">CAREER SIGNALS</p><h1>Where your skills can go.</h1><p>Market context connected to your {result.topic} path.</p></div></div><div className="career-grid"><div className="career-main glass-panel"><div className="card-heading"><span>CAREER TARGET</span><Briefcase size={16} /></div><h2>{result.title || `${result.topic} specialist`}</h2><p>{result.description}</p><div className="career-stats"><div><span>Demand</span><strong>{market?.demand_score || '--'}<small>/100</small></strong></div><div><span>Open positions</span><strong>{market?.open_positions || 'Researching'}</strong></div><div><span>Salary range</span><strong>{market?.average_salary || 'Researching'}</strong></div></div></div><div className="skill-gap glass-panel"><div className="card-heading"><span>SKILLS IN YOUR PATH</span><Target size={16} /></div>{(result.milestones || []).flatMap((item) => item.skills_gained || []).slice(0, 6).map((skill) => <div className="skill-row" key={skill}><span>{skill}</span><i /></div>)}</div></div></section>; }

function TutorView({ result }) { const [question, setQuestion] = useState(''); const [answer, setAnswer] = useState(''); const [loading, setLoading] = useState(false); const submit = async (event) => { event.preventDefault(); if (!question.trim() || !result?.id) return; setLoading(true); try { const response = await askQuestion(question, result.id); setAnswer(response?.data?.answer || response?.message || 'No answer returned.'); } catch { setAnswer('Sign in and save this path to use the contextual AI tutor.'); } finally { setLoading(false); } }; return <section className="view-stack tutor-page"><div className="page-intro"><div><p className="eyebrow">AI TUTOR</p><h1>A second brain for your path.</h1><p>Ask questions in context. Get unstuck without losing your thread.</p></div><div className="tutor-orb"><Sparkles size={20} /></div></div><div className="tutor-panel glass-panel"><div className="tutor-header"><div className="assistant-avatar"><Sparkles size={18} /></div><div><strong>Path companion</strong><span>{result ? `Context: ${result.topic}` : 'Generate a path to unlock context'}</span></div><span className="online-label"><span className="live-dot" /> online</span></div><div className="chat-space">{answer ? <div className="answer-bubble"><span>AI TUTOR</span><p>{answer}</p></div> : <div className="chat-empty"><MessageSquare size={24} /><p>What are you working through?</p><small>Try asking about a concept, a resource, or your next step.</small></div>}</div><form className="chat-form" onSubmit={submit}><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={result ? 'Ask about your learning path...' : 'Generate a path first to ask questions'} disabled={!result || loading} /><button aria-label="Send question" disabled={!result || loading}><Send size={17} /></button></form></div></section>; }
function EmptyView({ eyebrow, title, copy, action, onClick }) { return <section className="empty-view glass-panel"><div className="empty-icon"><Sparkles size={22} /></div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{copy}</p><button className="button button-primary" onClick={onClick}>{action} <ArrowRight size={16} /></button></section>; }

export default App;

function pathToView(pathname) {
  if (pathname === '/my-paths' || pathname.startsWith('/path/')) return 'paths';
  if (pathname === '/career') return 'career';
  if (pathname === '/tutor') return 'tutor';
  if (pathname === '/build') return 'build';
  return 'overview';
}

function viewToPath(view) {
  return view === 'overview' ? '/dashboard' : `/${view === 'paths' ? 'my-paths' : view}`;
}