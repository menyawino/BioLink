import React, { Component, type ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
  componentName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log to console in development
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // In production, you would send to an error tracking service
    if (import.meta.env.PROD) {
      // TODO: Send to Application Insights or Sentry
      // appInsights.trackException({ exception: error, properties: { component: this.props.componentName } });
    }

    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    this.props.onReset?.();
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-background">
          <Card className="w-full max-w-lg shadow-lg">
            <CardHeader className="space-y-1">
              <div className="flex items-center gap-2 text-destructive">
                <AlertTriangle className="h-6 w-6" />
                <CardTitle className="text-xl">Something went wrong</CardTitle>
              </div>
              <p className="text-sm text-muted-foreground">
                {this.props.componentName
                  ? `An error occurred in the ${this.props.componentName} component.`
                  : 'An unexpected error occurred in the application.'}
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-md bg-muted p-4">
                <p className="text-sm font-medium text-foreground mb-1">Error:</p>
                <p className="text-sm text-muted-foreground font-mono break-all">
                  {this.state.error?.message || 'Unknown error'}
                </p>
                {import.meta.env.DEV && this.state.errorInfo && (
                  <details className="mt-2">
                    <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                      Stack trace
                    </summary>
                    <pre className="mt-2 text-xs text-muted-foreground overflow-auto max-h-48 p-2 bg-background rounded">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                <Button onClick={this.handleReset} variant="default" className="gap-2">
                  <RefreshCw className="h-4 w-4" />
                  Try Again
                </Button>
                <Button onClick={this.handleReload} variant="outline" className="gap-2">
                  <RefreshCw className="h-4 w-4" />
                  Reload Page
                </Button>
                <Button onClick={this.handleGoHome} variant="ghost" className="gap-2">
                  <Home className="h-4 w-4" />
                  Go Home
                </Button>
              </div>

              {import.meta.env.DEV && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Bug className="h-3 w-3" />
                  <span>Development mode: Check console for full error details</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook version for functional components
export function useErrorBoundary() {
  const [error, setError] = React.useState<Error | null>(null);

  const resetError = React.useCallback(() => {
    setError(null);
  }, []);

  const throwError = React.useCallback((err: Error) => {
    setError(err);
  }, []);

  if (error) {
    throw error;
  }

  return { resetError, throwError };
}
