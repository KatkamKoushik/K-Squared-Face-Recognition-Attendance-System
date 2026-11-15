"use client";

import React, { useEffect, useState, useRef } from "react";
import { Sun, Moon, Monitor, Check } from "lucide-react";

export type Theme = "light" | "dark" | "system";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const [theme, setTheme] = useState<Theme>("system");
  const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">("light");
  const [mounted, setMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    const stored = (localStorage.getItem("theme") as Theme) || "system";
    setTheme(stored);

    const mql = window.matchMedia("(prefers-color-scheme: dark)");

    const applyTheme = (currentTheme: Theme) => {
      const isDark =
        currentTheme === "dark" ||
        (currentTheme === "system" && mql.matches);

      if (isDark) {
        document.documentElement.classList.add("dark");
        document.documentElement.style.colorScheme = "dark";
        setResolvedTheme("dark");
      } else {
        document.documentElement.classList.remove("dark");
        document.documentElement.style.colorScheme = "light";
        setResolvedTheme("light");
      }
    };

    applyTheme(stored);

    const handleSystemChange = () => {
      const activeStored = (localStorage.getItem("theme") as Theme) || "system";
      if (activeStored === "system") {
        applyTheme("system");
      }
    };

    mql.addEventListener("change", handleSystemChange);
    return () => mql.removeEventListener("change", handleSystemChange);
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  const selectTheme = (newTheme: Theme) => {
    setTheme(newTheme);
    setIsOpen(false);

    if (newTheme === "system") {
      localStorage.removeItem("theme");
      const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      if (systemDark) {
        document.documentElement.classList.add("dark");
        document.documentElement.style.colorScheme = "dark";
        setResolvedTheme("dark");
      } else {
        document.documentElement.classList.remove("dark");
        document.documentElement.style.colorScheme = "light";
        setResolvedTheme("light");
      }
    } else {
      localStorage.setItem("theme", newTheme);
      if (newTheme === "dark") {
        document.documentElement.classList.add("dark");
        document.documentElement.style.colorScheme = "dark";
        setResolvedTheme("dark");
      } else {
        document.documentElement.classList.remove("dark");
        document.documentElement.style.colorScheme = "light";
        setResolvedTheme("light");
      }
    }
  };

  const handleQuickToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    const next = resolvedTheme === "dark" ? "light" : "dark";
    selectTheme(next);
  };

  if (!mounted) {
    return (
      <div className={`w-9 h-9 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-800 animate-pulse ${className}`} />
    );
  }

  return (
    <div className={`relative inline-block text-left ${className}`} ref={dropdownRef}>
      <div className="flex items-center rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-2xs">
        <button
          type="button"
          onClick={handleQuickToggle}
          title={resolvedTheme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
          aria-label={resolvedTheme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
          className="p-2 rounded-l-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors cursor-pointer"
        >
          {resolvedTheme === "dark" ? (
            <Moon className="w-4 h-4 text-amber-400" />
          ) : (
            <Sun className="w-4 h-4 text-amber-600" />
          )}
        </button>

        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          title="Select Theme: Light, Dark, or System"
          aria-label="Theme menu"
          className="px-1.5 py-2 border-l border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 text-[11px] font-semibold text-slate-500 dark:text-slate-400 rounded-r-lg transition-colors cursor-pointer flex items-center space-x-1"
        >
          <span className="capitalize">{theme === "system" ? "Auto" : theme}</span>
          <svg className="w-3 h-3 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-36 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-lg py-1.5 z-50 animate-in fade-in zoom-in-95 duration-100">
          <button
            type="button"
            onClick={() => selectTheme("light")}
            className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium transition-colors cursor-pointer ${
              theme === "light"
                ? "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-semibold"
                : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/60"
            }`}
          >
            <div className="flex items-center space-x-2">
              <Sun className="w-3.5 h-3.5 text-amber-600" />
              <span>Light</span>
            </div>
            {theme === "light" && <Check className="w-3.5 h-3.5 text-emerald-600" />}
          </button>

          <button
            type="button"
            onClick={() => selectTheme("dark")}
            className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium transition-colors cursor-pointer ${
              theme === "dark"
                ? "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-semibold"
                : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/60"
            }`}
          >
            <div className="flex items-center space-x-2">
              <Moon className="w-3.5 h-3.5 text-amber-400" />
              <span>Dark</span>
            </div>
            {theme === "dark" && <Check className="w-3.5 h-3.5 text-emerald-600" />}
          </button>

          <button
            type="button"
            onClick={() => selectTheme("system")}
            className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium transition-colors cursor-pointer ${
              theme === "system"
                ? "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white font-semibold"
                : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/60"
            }`}
          >
            <div className="flex items-center space-x-2">
              <Monitor className="w-3.5 h-3.5 text-blue-500" />
              <span>System</span>
            </div>
            {theme === "system" && <Check className="w-3.5 h-3.5 text-emerald-600" />}
          </button>
        </div>
      )}
    </div>
  );
}
