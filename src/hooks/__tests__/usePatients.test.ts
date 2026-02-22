import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { usePatient, usePatients } from '../usePatients';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

// Mock the API client
vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

import { apiClient } from '../../api/client';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('usePatients', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches patients list successfully', async () => {
    const mockPatients = [
      { dna_id: 'TEST001', age: 45, gender: 'M' },
      { dna_id: 'TEST002', age: 52, gender: 'F' },
    ];

    (apiClient.get as any).mockResolvedValueOnce({ data: mockPatients });

    const { result } = renderHook(() => usePatients({ limit: 10 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockPatients);
  });

  it('handles error state', async () => {
    (apiClient.get as any).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => usePatients({ limit: 10 }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
  });
});

describe('usePatient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches single patient by ID', async () => {
    const mockPatient = {
      dna_id: 'TEST001',
      age: 45,
      gender: 'M',
      medical: { diabetes_mellitus: false },
    };

    (apiClient.get as any).mockResolvedValueOnce({ data: mockPatient });

    const { result } = renderHook(() => usePatient('TEST001'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockPatient);
    expect(apiClient.get).toHaveBeenCalledWith('/patients/TEST001');
  });
});
