# 🎨 GLASSMORPHIC CSS REFERENCE

Complete stylesheet for the glassmorphic sci-fi design system.

---

## Complete CSS for `web_app/static/css/glassmorphic.css`

```css
/* ==========================================================================
   GLASSMORPHIC SCI-FI DESIGN SYSTEM
   Complete stylesheet for AI Learning Path Generator redesign
   ========================================================================== */

/* Import Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ==========================================================================
   CSS CUSTOM PROPERTIES
   ========================================================================== */

:root {
    /* Background Colors */
    --bg-primary: #0a0e27;
    --bg-secondary: #13172e;
    --bg-tertiary: #1a1f3a;
    
    /* Glass Effect */
    --glass-bg: rgba(255, 255, 255, 0.05);
    --glass-bg-hover: rgba(255, 255, 255, 0.08);
    --glass-border: rgba(255, 255, 255, 0.1);
    --glass-blur: 20px;
    
    /* Neon Colors */
    --neon-cyan: #00f3ff;
    --neon-purple: #bf00ff;
    --neon-pink: #ff0099;
    --neon-green: #00ff88;
    
    /* Text Colors */
    --text-primary: #ffffff;
    --text-secondary: rgba(255, 255, 255, 0.7);
    --text-muted: rgba(255, 255, 255, 0.4);
    
    /* Status Colors */
    --status-success: #00ff88;
    --status-warning: #ffb800;
    --status-error: #ff0051;
    
    /* Grid */
    --grid-color: rgba(0, 243, 255, 0.1);
    
    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-2xl: 3rem;
    
    /* Border Radius */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;
    --radius-full: 9999px;
}

/* ==========================================================================
   BASE STYLES
   ========================================================================== */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

h1, h2, h3, h4, h5, h6 {
    font-weight: 700;
    line-height: 1.2;
}

a {
    text-decoration: none;
    color: inherit;
}

button {
    font-family: inherit;
    cursor: pointer;
    border: none;
    background: none;
}

/* ==========================================================================
   GLASS COMPONENTS
   ========================================================================== */

/* Glass Card */
.glass-card {
    background: var(--glass-bg);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
    background: var(--glass-bg-hover);
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

.glass-card-no-hover {
    background: var(--glass-bg);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* Glass Nav */
.glass-nav {
    background: var(--glass-bg);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border-bottom: 1px solid var(--glass-border);
    position: sticky;
    top: 0;
    z-index: 50;
}

/* Glass Input */
.glass-input {
    background: var(--glass-bg);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    color: var(--text-primary);
    font-size: 1rem;
    width: 100%;
    transition: all 0.3s ease;
}

.glass-input:focus {
    outline: none;
    border-color: var(--neon-cyan);
    box-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
}

.glass-input::placeholder {
    color: var(--text-muted);
}

/* Glass Select */
.glass-select {
    background: var(--glass-bg);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    color: var(--text-primary);
    font-size: 1rem;
    width: 100%;
    cursor: pointer;
    transition: all 0.3s ease;
}

.glass-select:focus {
    outline: none;
    border-color: var(--neon-cyan);
    box-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
}

/* ==========================================================================
   NEON BUTTONS
   ========================================================================== */

/* Primary Neon Button */
.neon-btn {
    background: transparent;
    border: 2px solid var(--neon-cyan);
    color: var(--neon-cyan);
    padding: 12px 32px;
    border-radius: var(--radius-sm);
    font-weight: 600;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    box-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
}

.neon-btn:hover {
    background: var(--neon-cyan);
    color: var(--bg-primary);
    box-shadow: 0 0 40px rgba(0, 243, 255, 0.6);
    transform: translateY(-2px);
}

.neon-btn:active {
    transform: translateY(0);
}

/* Purple Neon Button */
.neon-btn-purple {
    border-color: var(--neon-purple);
    color: var(--neon-purple);
    box-shadow: 0 0 20px rgba(191, 0, 255, 0.3);
}

.neon-btn-purple:hover {
    background: var(--neon-purple);
    color: var(--bg-primary);
    box-shadow: 0 0 40px rgba(191, 0, 255, 0.6);
}

/* Pink Neon Button */
.neon-btn-pink {
    border-color: var(--neon-pink);
    color: var(--neon-pink);
    box-shadow: 0 0 20px rgba(255, 0, 153, 0.3);
}

.neon-btn-pink:hover {
    background: var(--neon-pink);
    color: var(--bg-primary);
    box-shadow: 0 0 40px rgba(255, 0, 153, 0.6);
}

/* Small Neon Buttons */
.neon-btn-sm {
    padding: 8px 20px;
    font-size: 0.75rem;
    border: 2px solid var(--neon-cyan);
    color: var(--neon-cyan);
    background: transparent;
    border-radius: var(--radius-sm);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.3);
    transition: all 0.3s ease;
}

.neon-btn-sm:hover {
    background: var(--neon-cyan);
    color: var(--bg-primary);
    box-shadow: 0 0 25px rgba(0, 243, 255, 0.5);
}

.neon-btn-sm-purple {
    padding: 8px 20px;
    font-size: 0.75rem;
    border: 2px solid var(--neon-purple);
    color: var(--neon-purple);
    background: transparent;
    border-radius: var(--radius-sm);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 0 15px rgba(191, 0, 255, 0.3);
    transition: all 0.3s ease;
}

.neon-btn-sm-purple:hover {
    background: var(--neon-purple);
    color: var(--bg-primary);
    box-shadow: 0 0 25px rgba(191, 0, 255, 0.5);
}

/* ==========================================================================
   BACKGROUNDS
   ========================================================================== */

/* Grid Background */
.grid-background {
    background-color: var(--bg-primary);
    background-image: 
        linear-gradient(var(--grid-color) 1px, transparent 1px),
        linear-gradient(90deg, var(--grid-color) 1px, transparent 1px);
    background-size: 50px 50px;
    background-position: center center;
    position: relative;
}

.grid-background::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 50% 50%, transparent 0%, var(--bg-primary) 100%);
    pointer-events: none;
}

/* Section Backgrounds */
.bg-primary {
    background-color: var(--bg-primary);
}

.bg-secondary {
    background-color: var(--bg-secondary);
}

.bg-tertiary {
    background-color: var(--bg-tertiary);
}

/* ==========================================================================
   TEXT UTILITIES
   ========================================================================== */

.text-neon-cyan { color: var(--neon-cyan); }
.text-neon-purple { color: var(--neon-purple); }
.text-neon-pink { color: var(--neon-pink); }
.text-neon-green { color: var(--neon-green); }
.text-primary { color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.text-muted { color: var(--text-muted); }

/* ==========================================================================
   EFFECTS
   ========================================================================== */

/* Neon Glow Shadow */
.shadow-neon {
    box-shadow: 0 0 20px rgba(0, 243, 255, 0.5);
}

.shadow-neon-purple {
    box-shadow: 0 0 20px rgba(191, 0, 255, 0.5);
}

.shadow-neon-pink {
    box-shadow: 0 0 20px rgba(255, 0, 153, 0.5);
}

/* Gradient Text */
.gradient-text {
    background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ==========================================================================
   ANIMATIONS
   ========================================================================== */

/* Float Animation */
@keyframes float {
    0%, 100% {
        transform: translateY(0px);
    }
    50% {
        transform: translateY(-20px);
    }
}

.float-animation {
    animation: float 6s ease-in-out infinite;
}

/* Pulse Animation */
@keyframes pulse-glow {
    0%, 100% {
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
    }
    50% {
        box-shadow: 0 0 40px rgba(0, 243, 255, 0.6);
    }
}

.pulse-glow {
    animation: pulse-glow 2s ease-in-out infinite;
}

/* Fade In */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in {
    animation: fadeIn 0.6s ease-out forwards;
}

/* Slide In Right */
@keyframes slideInRight {
    from {
        transform: translateX(100%);
    }
    to {
        transform: translateX(0);
    }
}

.slide-in-right {
    animation: slideInRight 0.3s ease-out;
}

/* Spin (for loading) */
@keyframes spin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

.spin {
    animation: spin 1s linear infinite;
}

/* ==========================================================================
   PROGRESS BARS
   ========================================================================== */

.progress-bar-container {
    width: 100%;
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-full);
    overflow: hidden;
    position: relative;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple));
    border-radius: var(--radius-full);
    box-shadow: 0 0 20px rgba(0, 243, 255, 0.5);
    transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ==========================================================================
   TIMELINE
   ========================================================================== */

.timeline-line {
    position: absolute;
    left: 2rem;
    top: 0;
    bottom: 0;
    width: 2px;
    background: linear-gradient(180deg, var(--neon-cyan), var(--neon-purple), var(--neon-pink));
    opacity: 0.6;
}

.timeline-node {
    position: absolute;
    left: 1.5rem;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 2px solid var(--neon-cyan);
    background: var(--bg-primary);
    box-shadow: 0 0 15px rgba(0, 243, 255, 0.5);
    z-index: 10;
}

/* ==========================================================================
   PARTICLES
   ========================================================================== */

.particle {
    position: absolute;
    width: 4px;
    height: 4px;
    background: var(--neon-cyan);
    border-radius: 50%;
    opacity: 0.6;
    pointer-events: none;
}

@keyframes float-particle {
    0%, 100% {
        transform: translate(0, 0) scale(1);
        opacity: 0.3;
    }
    50% {
        transform: translate(100px, -100px) scale(1.5);
        opacity: 0.8;
    }
}

.particle-animated {
    animation: float-particle 20s ease-in-out infinite;
}

/* ==========================================================================
   RESPONSIVE
   ========================================================================== */

@media (max-width: 768px) {
    .glass-card {
        border-radius: var(--radius-md);
    }
    
    .neon-btn {
        padding: 10px 24px;
        font-size: 0.75rem;
    }
    
    .grid-background {
        background-size: 30px 30px;
    }
}

/* ==========================================================================
   UTILITY CLASSES
   ========================================================================== */

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}

.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.w-full { width: 100%; }
.h-full { height: 100%; }

.flex { display: flex; }
.inline-flex { display: inline-flex; }
.grid { display: grid; }

.items-center { align-items: center; }
.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }

.gap-2 { gap: 0.5rem; }
.gap-4 { gap: 1rem; }
.gap-6 { gap: 1.5rem; }
.gap-8 { gap: 2rem; }

.p-4 { padding: 1rem; }
.p-6 { padding: 1.5rem; }
.p-8 { padding: 2rem; }

.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-6 { margin-bottom: 1.5rem; }
.mb-8 { margin-bottom: 2rem; }
.mb-12 { margin-bottom: 3rem; }

.mt-4 { margin-top: 1rem; }
.mt-6 { margin-top: 1.5rem; }
.mt-8 { margin-top: 2rem; }

.rounded { border-radius: var(--radius-sm); }
.rounded-lg { border-radius: var(--radius-lg); }
.rounded-full { border-radius: var(--radius-full); }

.transition { transition: all 0.3s ease; }
.cursor-pointer { cursor: pointer; }

/* ==========================================================================
   END OF STYLESHEET
   ========================================================================== */
```

---

## Usage Examples

### Glass Card with Content
```html
<div class="glass-card p-6">
    <h3 class="text-white mb-4">Card Title</h3>
    <p class="text-secondary">Card content goes here</p>
</div>
```

### Neon Button
```html
<button class="neon-btn">Click Me</button>
<button class="neon-btn-purple">Purple Button</button>
```

### Glass Input Form
```html
<input type="text" class="glass-input" placeholder="Enter text...">
<select class="glass-select">
    <option>Option 1</option>
</select>
```

### Grid Background Section
```html
<section class="grid-background min-h-screen">
    <div class="container">
        <!-- Content -->
    </div>
</section>
```

### Timeline
```html
<div class="relative">
    <div class="timeline-line"></div>
    <div class="timeline-node" style="top: 0;"></div>
    <div class="glass-card p-6 ml-20">
        <h4>Milestone 1</h4>
    </div>
</div>
```

---

**This CSS file is production-ready and optimized for performance!**
