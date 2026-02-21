import React, { useState } from 'react';

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
  };

  return (
    <button onClick={toggleTheme} className="theme-toggle">
      {isDark ? '☀️ Light Mode' : '🌙 Dark Mode'}
    </button>
  );
}
