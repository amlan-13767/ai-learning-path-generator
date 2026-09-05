import { useEffect, useState } from 'react';

/**
 * Navigate inside the React application.
 *
 * Every user-facing route lives in this SPA. Nothing here may ever point at the
 * Flask origin: Flask is an API and its HTML pages no longer exist.
 *
 * @param {string} to - An app-relative path, e.g. '/dashboard'.
 * @param {{replace?: boolean}} [options]
 */
export function navigate(to, { replace = false } = {}) {
  if (!to.startsWith('/')) {
    throw new Error(`navigate() only accepts app-relative paths, received: ${to}`);
  }
  if (window.location.pathname === to && !replace) return;
  if (replace) window.history.replaceState({}, '', to);
  else window.history.pushState({}, '', to);
  // pushState/replaceState do not fire popstate, so tell subscribers ourselves.
  window.dispatchEvent(new PopStateEvent('popstate'));
}

/** Current pathname, kept in sync with pushState and the browser back button. */
export function usePathname() {
  const [pathname, setPathname] = useState(() => window.location.pathname);
  useEffect(() => {
    const sync = () => setPathname(window.location.pathname);
    window.addEventListener('popstate', sync);
    return () => window.removeEventListener('popstate', sync);
  }, []);
  return pathname;
}

/**
 * onClick handler for in-app anchors. Keeps the href for accessibility and
 * middle-click, but avoids a full page reload on a normal left click.
 */
export function linkHandler(to) {
  return (event) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
    event.preventDefault();
    navigate(to);
  };
}
