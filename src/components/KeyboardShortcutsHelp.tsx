import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Badge } from './ui/badge';
import { Keyboard } from 'lucide-react';
import { getAppShortcuts } from '../hooks/useKeyboardShortcuts';

interface KeyboardShortcutsHelpProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function KeyboardShortcutsHelp({ open, onOpenChange }: KeyboardShortcutsHelpProps) {
  // Get shortcuts with no-op actions for display
  const shortcuts = getAppShortcuts(() => {}, {});

  const formatKey = (shortcut: typeof shortcuts[0]) => {
    const parts: string[] = [];
    if (shortcut.modifiers?.ctrl) parts.push('Ctrl');
    if (shortcut.modifiers?.alt) parts.push('Alt');
    if (shortcut.modifiers?.shift) parts.push('Shift');
    if (shortcut.modifiers?.meta) parts.push('⌘');
    parts.push(shortcut.key);
    return parts.join(' + ');
  };

  const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
    const group = shortcut.scope || 'global';
    if (!acc[group]) acc[group] = [];
    acc[group].push(shortcut);
    return acc;
  }, {} as Record<string, typeof shortcuts>);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Keyboard Shortcuts
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {Object.entries(groupedShortcuts).map(([group, items]) => (
            <div key={group}>
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                {group === 'global' ? 'Global' : group}
              </h3>
              <div className="space-y-2">
                {items.map((shortcut, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <span className="text-sm text-foreground">
                      {shortcut.description}
                    </span>
                    <div className="flex items-center gap-1">
                      {formatKey(shortcut).split(' + ').map((part, i) => (
                        <React.Fragment key={i}>
                          {i > 0 && <span className="text-muted-foreground mx-1">+</span>}
                          <Badge variant="secondary" className="font-mono text-xs">
                            {part}
                          </Badge>
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t text-xs text-muted-foreground">
          Press <Badge variant="outline" className="font-mono text-xs">?</Badge> to show this dialog from anywhere.
        </div>
      </DialogContent>
    </Dialog>
  );
}
