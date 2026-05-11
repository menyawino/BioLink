import { useEffect, useCallback, useRef } from 'react';

export interface KeyboardShortcut {
  key: string;
  modifiers?: {
    ctrl?: boolean;
    alt?: boolean;
    shift?: boolean;
    meta?: boolean;
  };
  description: string;
  action: () => void;
  preventDefault?: boolean;
  // Scope restricts the shortcut to specific elements or contexts
  scope?: 'global' | 'input' | 'table';
}

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]) {
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const target = event.target as HTMLElement;
    const isInputElement = target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable;

    for (const shortcut of shortcutsRef.current) {
      // Skip global shortcuts when typing in inputs (unless explicitly allowed)
      if (isInputElement && shortcut.scope !== 'input') {
        continue;
      }

      const modifiers = shortcut.modifiers || {};
      const matchesKey = event.key.toLowerCase() === shortcut.key.toLowerCase();
      const matchesCtrl = !!modifiers.ctrl === event.ctrlKey;
      const matchesAlt = !!modifiers.alt === event.altKey;
      const matchesShift = !!modifiers.shift === event.shiftKey;
      const matchesMeta = !!modifiers.meta === event.metaKey;

      if (matchesKey && matchesCtrl && matchesAlt && matchesShift && matchesMeta) {
        if (shortcut.preventDefault !== false) {
          event.preventDefault();
        }
        shortcut.action();
        break;
      }
    }
  }, []);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

// Predefined shortcuts for BioLink
export function getAppShortcuts(
  navigateTo: (view: string) => void,
  actions: {
    toggleTheme?: () => void;
    toggleSidebar?: () => void;
    openSearch?: () => void;
    openChat?: () => void;
    openSettings?: () => void;
    openHelp?: () => void;
    logout?: () => void;
    goBack?: () => void;
  }
): KeyboardShortcut[] {
  return [
    {
      key: 'k',
      modifiers: { ctrl: true },
      description: 'Open search',
      action: () => actions.openSearch?.(),
      scope: 'global',
    },
    {
      key: 'k',
      modifiers: { meta: true },
      description: 'Open search (Mac)',
      action: () => actions.openSearch?.(),
      scope: 'global',
    },
    {
      key: '/',
      description: 'Focus search',
      action: () => actions.openSearch?.(),
      scope: 'global',
    },
    {
      key: 'b',
      modifiers: { ctrl: true },
      description: 'Toggle sidebar',
      action: () => actions.toggleSidebar?.(),
      scope: 'global',
    },
    {
      key: 'b',
      modifiers: { meta: true },
      description: 'Toggle sidebar (Mac)',
      action: () => actions.toggleSidebar?.(),
      scope: 'global',
    },
    {
      key: 'd',
      modifiers: { ctrl: true, shift: true },
      description: 'Toggle dark mode',
      action: () => actions.toggleTheme?.(),
      scope: 'global',
    },
    {
      key: '1',
      modifiers: { alt: true },
      description: 'Go to Welcome',
      action: () => navigateTo('welcome'),
      scope: 'global',
    },
    {
      key: '2',
      modifiers: { alt: true },
      description: 'Go to Patient Registry',
      action: () => navigateTo('registry'),
      scope: 'global',
    },
    {
      key: '3',
      modifiers: { alt: true },
      description: 'Go to Cohort Builder',
      action: () => navigateTo('cohort'),
      scope: 'global',
    },
    {
      key: '4',
      modifiers: { alt: true },
      description: 'Go to Analytics',
      action: () => navigateTo('analytics'),
      scope: 'global',
    },
    {
      key: '5',
      modifiers: { alt: true },
      description: 'Go to Chart Builder',
      action: () => navigateTo('charts'),
      scope: 'global',
    },
    {
      key: '6',
      modifiers: { alt: true },
      description: 'Go to Data Dictionary',
      action: () => navigateTo('dictionary'),
      scope: 'global',
    },
    {
      key: 'c',
      modifiers: { ctrl: true, shift: true },
      description: 'Open AI Chat',
      action: () => actions.openChat?.(),
      scope: 'global',
    },
    {
      key: ',',
      modifiers: { ctrl: true },
      description: 'Open Settings',
      action: () => actions.openSettings?.(),
      scope: 'global',
    },
    {
      key: '?',
      modifiers: { shift: true },
      description: 'Show keyboard shortcuts help',
      action: () => actions.openHelp?.(),
      scope: 'global',
    },
    {
      key: 'Escape',
      description: 'Close modal / Go back',
      action: () => actions.goBack?.(),
      scope: 'global',
      preventDefault: false,
    },
  ];
}

// Table-specific shortcuts
export function getTableShortcuts(
  actions: {
    selectAll?: () => void;
    selectNone?: () => void;
    exportSelected?: () => void;
    refresh?: () => void;
    nextPage?: () => void;
    prevPage?: () => void;
  }
): KeyboardShortcut[] {
  return [
    {
      key: 'a',
      modifiers: { ctrl: true },
      description: 'Select all rows',
      action: () => actions.selectAll?.(),
      scope: 'table',
    },
    {
      key: 'e',
      modifiers: { ctrl: true },
      description: 'Export selected',
      action: () => actions.exportSelected?.(),
      scope: 'table',
    },
    {
      key: 'r',
      modifiers: { ctrl: true },
      description: 'Refresh data',
      action: () => actions.refresh?.(),
      scope: 'table',
    },
    {
      key: 'ArrowRight',
      modifiers: { ctrl: true },
      description: 'Next page',
      action: () => actions.nextPage?.(),
      scope: 'table',
    },
    {
      key: 'ArrowLeft',
      modifiers: { ctrl: true },
      description: 'Previous page',
      action: () => actions.prevPage?.(),
      scope: 'table',
    },
  ];
}
