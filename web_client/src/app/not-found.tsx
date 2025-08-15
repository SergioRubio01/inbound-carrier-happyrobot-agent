/**
 * @file: not-found.tsx
 * @description: Custom 404 Not Found page component for the application.
 */
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Mountain } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex flex-col min-h-[100dvh]">
      <main className="flex-1 flex flex-col items-center justify-center text-center px-6 py-12">
        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl">
          Page Not Found
        </h1>
        <p className="mt-4 text-lg text-muted-foreground max-w-[600px] md:text-xl">
          Oops! It seems you've ventured into uncharted territory. Let's get you back on track.
        </p>
        <div className="mt-8">
          <DynamicMessage />
        </div>
        <Link href="/" className="mt-8">
          <Button>Return Home</Button>
        </Link>
      </main>
    </div>
  );
}

function DynamicMessage() {
  const messages = [
    'Did you take a wrong turn at Albuquerque?',
    "This page is playing hide and seek. And it's winning.",
    'Looks like this page is on a coffee break.',
    'Houston, we have a problem. This page is lost in space.',
    'Whoops! Our intern must have spilled coffee on the server again.',
  ];

  const randomMessage = messages[Math.floor(Math.random() * messages.length)];

  return <p className="text-xl font-semibold text-primary animate-bounce">{randomMessage}</p>;
}
