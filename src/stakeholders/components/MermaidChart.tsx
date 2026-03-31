import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  themeVariables: {
    fontFamily: 'ui-sans-serif, system-ui, sans-serif',
    primaryColor: '#f5f5f5',
    primaryTextColor: '#030213',
    primaryBorderColor: '#cbced4',
    lineColor: '#717182',
    secondaryColor: '#ffffff',
    tertiaryColor: '#ffffff'
  },
  flowchart: { curve: 'linear' },
  sequence: { showSequenceNumbers: false }
});

interface MermaidChartProps {
  chart: string;
  name: string;
}

export function MermaidChart({ chart, name }: MermaidChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isMounted = true;
    const renderChart = async () => {
      if (containerRef.current) {
        try {
          const { svg } = await mermaid.render(`mermaid-${name.replace(/[^a-zA-Z0-9]/g, '')}`, chart);
          if (isMounted && containerRef.current) {
            containerRef.current.innerHTML = svg;
          }
        } catch (e) {
          console.error(`Mermaid render failed for ${name}`, e);
          if (isMounted && containerRef.current) {
             containerRef.current.innerHTML = '<div class="text-red-500">Failed to render chart</div>';
          }
        }
      }
    };
    renderChart();
    return () => { isMounted = false; };
  }, [chart, name]);

  return (
    <div 
      ref={containerRef} 
      className="mermaid-wrapper flex items-center justify-center bg-white p-8 rounded-lg border border-slate-200 shadow-sm w-full overflow-x-auto mx-auto my-4 transition-all hover:shadow-md max-w-5xl"
      style={{ minHeight: '300px' }}
    />
  );
}
