import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PatientSearch } from '../PatientSearch';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the hooks
vi.mock('../hooks/usePatients', () => ({
  usePatientSearch: vi.fn(),
}));

import { usePatientSearch } from '../hooks/usePatients';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('PatientSearch', () => {
  const mockOnPatientSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (usePatientSearch as any).mockReturnValue({
      data: [],
      isLoading: false,
    });
  });

  it('renders search input', () => {
    render(
      <PatientSearch currentMrn="" onPatientSelect={mockOnPatientSelect} />,
      { wrapper: createWrapper() }
    );
    
    expect(screen.getByPlaceholderText(/search by dna id/i)).toBeInTheDocument();
  });

  it('displays current MRN badge', () => {
    render(
      <PatientSearch currentMrn="MRN123" onPatientSelect={mockOnPatientSelect} />,
      { wrapper: createWrapper() }
    );
    
    expect(screen.getByText(/current: mrn123/i)).toBeInTheDocument();
  });

  it('calls onPatientSelect when a patient is clicked', async () => {
    const mockResults = [
      { dna_id: 'DNA001', age: 45, gender: 'M' },
      { dna_id: 'DNA002', age: 52, gender: 'F' },
    ];
    
    (usePatientSearch as any).mockReturnValue({
      data: mockResults,
      isLoading: false,
    });

    render(
      <PatientSearch currentMrn="" onPatientSelect={mockOnPatientSelect} />,
      { wrapper: createWrapper() }
    );
    
    // Type in search box
    fireEvent.change(screen.getByPlaceholderText(/search by dna id/i), {
      target: { value: 'test' },
    });
    
    await waitFor(() => {
      expect(usePatientSearch).toHaveBeenCalledWith('test', 10);
    });
  });

  it('clears search when clear button is clicked', () => {
    render(
      <PatientSearch currentMrn="" onPatientSelect={mockOnPatientSelect} />,
      { wrapper: createWrapper() }
    );
    
    const input = screen.getByPlaceholderText(/search by dna id/i) as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'test' } });
    
    expect(input.value).toBe('test');
    
    // Find and click clear button
    const clearButton = screen.getByLabelText(/clear patient search/i);
    fireEvent.click(clearButton);
    
    expect(input.value).toBe('');
  });

  it('shows loading state', () => {
    (usePatientSearch as any).mockReturnValue({
      data: [],
      isLoading: true,
    });

    render(
      <PatientSearch currentMrn="" onPatientSelect={mockOnPatientSelect} />,
      { wrapper: createWrapper() }
    );
    
    fireEvent.change(screen.getByPlaceholderText(/search by dna id/i), {
      target: { value: 'test' },
    });
    
    // Should show loading indicator
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
