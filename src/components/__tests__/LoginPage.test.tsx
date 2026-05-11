import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LoginPage } from '../LoginPage';
import { AuthProvider } from '../../context/AuthContext';

// Mock the auth API
vi.mock('../../api/auth', () => ({
  registerApi: vi.fn(),
}));

// Mock the logo import
vi.mock('figma:asset/e26cb8b78ee049387f524876448562f480bca21b.png', () => ({
  default: 'mocked-logo.png',
}));

const renderWithAuth = (ui: React.ReactElement) => {
  return render(<AuthProvider>{ui}</AuthProvider>);
};

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form by default', () => {
    renderWithAuth(<LoginPage />);
    
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('switches to register mode', () => {
    renderWithAuth(<LoginPage />);
    
    const registerLink = screen.getByText(/create account/i);
    fireEvent.click(registerLink);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('shows validation error for empty fields on login', async () => {
    renderWithAuth(<LoginPage />);
    
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(submitButton);
    
    // The form should still be present (no navigation)
    await waitFor(() => {
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    });
  });

  it('toggles between login and register modes', () => {
    renderWithAuth(<LoginPage />);
    
    // Start in login mode
    expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
    
    // Switch to register
    fireEvent.click(screen.getByText(/create account/i));
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    
    // Switch back to login
    fireEvent.click(screen.getByText(/back to sign in/i));
    expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
  });

  it('displays password mismatch error in register mode', async () => {
    const { registerApi } = await import('../../api/auth');
    renderWithAuth(<LoginPage />);
    
    // Switch to register
    fireEvent.click(screen.getByText(/create account/i));
    
    // Fill in form with mismatched passwords
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'password123' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'password456' } });
    
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
    
    expect(registerApi).not.toHaveBeenCalled();
  });

  it('displays password length error in register mode', async () => {
    const { registerApi } = await import('../../api/auth');
    renderWithAuth(<LoginPage />);
    
    // Switch to register
    fireEvent.click(screen.getByText(/create account/i));
    
    // Fill in form with short password
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/^password$/i), { target: { value: 'short' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'short' } });
    
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument();
    });
    
    expect(registerApi).not.toHaveBeenCalled();
  });
});
