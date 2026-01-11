import { useState, useEffect, useCallback } from 'react';
import type { ApiResponse } from '../api/client';

interface UseQueryOptions<T> {
  enabled?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: string) => void;
}

interface UseQueryResult<T> {
  data: T | undefined;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useQuery<T>(
  queryFn: () => Promise<ApiResponse<T>>,
  deps: unknown[] = [],
  options: UseQueryOptions<T> = {}
): UseQueryResult<T> {
  const { enabled = true, onSuccess, onError } = options;
  const [data, setData] = useState<T | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!enabled) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await queryFn();
      
      if (response.success && response.data) {
        setData(response.data);
        onSuccess?.(response.data);
      } else {
        const errorMsg = response.error || 'Failed to fetch data';
        setError(errorMsg);
        onError?.(errorMsg);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      onError?.(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [enabled, queryFn, onSuccess, onError]);

  useEffect(() => {
    fetchData();
  }, [...deps, enabled]);

  return { data, isLoading, error, refetch: fetchData };
}

interface UseMutationOptions<T, V> {
  onSuccess?: (data: T, variables: V) => void;
  onError?: (error: string, variables: V) => void;
}

interface UseMutationResult<T, V> {
  data: T | undefined;
  isLoading: boolean;
  error: string | null;
  mutate: (variables: V) => Promise<void>;
  reset: () => void;
}

export function useMutation<T, V>(
  mutationFn: (variables: V) => Promise<ApiResponse<T>>,
  options: UseMutationOptions<T, V> = {}
): UseMutationResult<T, V> {
  const { onSuccess, onError } = options;
  const [data, setData] = useState<T | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mutate = useCallback(async (variables: V) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await mutationFn(variables);
      
      if (response.success && response.data) {
        setData(response.data);
        onSuccess?.(response.data, variables);
      } else {
        const errorMsg = response.error || 'Mutation failed';
        setError(errorMsg);
        onError?.(errorMsg, variables);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      onError?.(errorMsg, variables);
    } finally {
      setIsLoading(false);
    }
  }, [mutationFn, onSuccess, onError]);

  const reset = useCallback(() => {
    setData(undefined);
    setError(null);
  }, []);

  return { data, isLoading, error, mutate, reset };
}
