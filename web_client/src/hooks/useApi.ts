/**
 * @file: useApi.ts
 * @description: Custom React hooks for handling API requests with loading, error, and success states
 */

import { useState, useEffect, useCallback } from 'react';
import apiClient from '@/lib/apiClient';
import { toast } from 'sonner';

interface UseApiOptions {
  errorMessage?: string;
  successMessage?: string;
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
  automaticErrorHandling?: boolean;
  deps?: any[];
}

// Generic hook for API calls with loading and error states
export function useApi<T = any>(
  apiCallFn: (apiClient: typeof apiClient) => Promise<T>,
  options: UseApiOptions = {}
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const {
    errorMessage = 'An error occurred while fetching data',
    successMessage,
    onSuccess,
    onError,
    automaticErrorHandling = true,
    deps = [],
  } = options;

  const execute = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setIsSuccess(false);

    try {
      const result = await apiCallFn(apiClient);
      setData(result);
      setIsSuccess(true);

      if (successMessage) {
        toast.success(successMessage);
      }

      if (onSuccess) {
        onSuccess(result);
      }

      return result;
    } catch (err: any) {
      setError(err);

      if (automaticErrorHandling) {
        // Error handling is already done in the API client
        // but we can add custom error handling here if needed
      }

      if (onError) {
        onError(err);
      }

      return null;
    } finally {
      setIsLoading(false);
    }
  }, [apiCallFn, ...deps]);

  return {
    data,
    isLoading,
    error,
    isSuccess,
    execute,
    reset: useCallback(() => {
      setData(null);
      setError(null);
      setIsLoading(false);
      setIsSuccess(false);
    }, []),
  };
}

// For GET requests that should run on component mount
export function useApiGet<T = any>(url: string, config = {}, options: UseApiOptions = {}) {
  const { execute, ...rest } = useApi<T>((apiClient) => apiClient.get(url, config), {
    ...options,
    deps: [url, JSON.stringify(config), ...(options.deps || [])],
  });

  useEffect(() => {
    execute();
  }, [execute]);

  return { ...rest, refetch: execute };
}

export default useApi;
