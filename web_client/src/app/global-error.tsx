'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Global application error:', error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="flex h-screen w-full flex-col items-center justify-center bg-gray-50">
          <div className="mx-auto max-w-md px-4 text-center">
            <h1 className="text-3xl font-bold tracking-tight text-red-600 mb-4">Something went wrong!</h1>
            <p className="mb-8 text-gray-600">
              {error.message || 'An unexpected error occurred. Please try again.'}
            </p>
            <div className="flex flex-col space-y-2 sm:flex-row sm:space-x-2 sm:space-y-0 justify-center">
              <Button onClick={() => window.location.href = '/'} variant="outline">
                Go Home
              </Button>
              <Button onClick={() => typeof reset === 'function' ? reset() : window.location.reload()}>
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
