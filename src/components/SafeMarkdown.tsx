import React, { useMemo } from 'react';
import { cn } from './ui/utils';

interface SafeMarkdownProps {
  content: string;
  className?: string;
  allowedTags?: string[];
}

// Simple HTML sanitizer - removes dangerous tags and attributes
function sanitizeHtml(html: string, allowedTags: string[] = SAFE_TAGS): string {
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');

  function cleanNode(node: Node): Node | null {
    if (node.nodeType === Node.TEXT_NODE) {
      return node.cloneNode();
    }

    if (node.nodeType === Node.ELEMENT_NODE) {
      const element = node as HTMLElement;
      const tagName = element.tagName.toLowerCase();

      // Remove disallowed tags
      if (!allowedTags.includes(tagName)) {
        // For disallowed tags, keep their text content
        const fragment = document.createDocumentFragment();
        element.childNodes.forEach(child => {
          const cleaned = cleanNode(child);
          if (cleaned) fragment.appendChild(cleaned);
        });
        return fragment;
      }

      // Create clean element
      const cleanElement = document.createElement(tagName);

      // Only allow safe attributes
      const safeAttributes = SAFE_ATTRIBUTES[tagName] || [];
      safeAttributes.forEach(attr => {
        if (element.hasAttribute(attr)) {
          const value = element.getAttribute(attr);
          if (value && !isDangerousValue(value)) {
            cleanElement.setAttribute(attr, value);
          }
        }
      });

      // Recursively clean children
      element.childNodes.forEach(child => {
        const cleaned = cleanNode(child);
        if (cleaned) cleanElement.appendChild(cleaned);
      });

      return cleanElement;
    }

    return null;
  }

  const body = doc.body;
  const fragment = document.createDocumentFragment();

  Array.from(body.childNodes).forEach(node => {
    const cleaned = cleanNode(node);
    if (cleaned) fragment.appendChild(cleaned);
  });

  const tempDiv = document.createElement('div');
  tempDiv.appendChild(fragment);
  return tempDiv.innerHTML;
}

function isDangerousValue(value: string): boolean {
  const dangerous = [
    'javascript:',
    'data:text/html',
    'vbscript:',
    'onerror=',
    'onload=',
    'onclick=',
    'onmouseover=',
  ];
  const lowerValue = value.toLowerCase();
  return dangerous.some(d => lowerValue.includes(d));
}

const SAFE_TAGS = [
  'p', 'br', 'hr',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'strong', 'b', 'em', 'i', 'u', 's', 'del', 'ins',
  'code', 'pre', 'blockquote',
  'ul', 'ol', 'li',
  'a',
  'img',
  'table', 'thead', 'tbody', 'tr', 'th', 'td',
  'div', 'span',
  'sup', 'sub',
];

const SAFE_ATTRIBUTES: Record<string, string[]> = {
  a: ['href', 'title', 'target'],
  img: ['src', 'alt', 'title', 'width', 'height'],
  table: ['border', 'cellpadding', 'cellspacing'],
  th: ['colspan', 'rowspan'],
  td: ['colspan', 'rowspan'],
  div: ['class'],
  span: ['class'],
  pre: ['class'],
  code: ['class'],
};

// Parse markdown to safe HTML
function parseMarkdownToHtml(text: string): string {
  let html = text
    // Escape HTML entities first
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Headers
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    // Bold and italic
    .replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/_(.*?)_/g, '<em>$1</em>')
    // Code blocks
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    // Images
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />')
    // Lists
    .replace(/^\s*[-*+]\s+(.*$)/gim, '<li>$1</li>')
    // Blockquotes
    .replace(/^>\s+(.*$)/gim, '<blockquote>$1</blockquote>')
    // Line breaks
    .replace(/\n/g, '<br />');

  // Wrap consecutive list items in ul
  html = html.replace(/(<li>.*<\/li>)(<br \/>)?(<li>.*<\/li>)/g, '$1$3');
  html = html.replace(/(<li>.*<\/li>)+/g, '<ul>$&</ul>');

  return html;
}

export function SafeMarkdown({ content, className, allowedTags }: SafeMarkdownProps) {
  const sanitizedHtml = useMemo(() => {
    // First parse markdown, then sanitize
    const html = parseMarkdownToHtml(content);
    return sanitizeHtml(html, allowedTags);
  }, [content, allowedTags]);

  return (
    <span
      className={cn('whitespace-pre-wrap', className)}
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
    />
  );
}

// Pure text renderer (no HTML at all)
export function SafeText({ content, className }: { content: string; className?: string }) {
  const text = useMemo(() => {
    return content
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1 ($2)')
      .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '[Image: $1]');
  }, [content]);

  return <span className={cn('whitespace-pre-wrap', className)}>{text}</span>;
}

export default SafeMarkdown;
