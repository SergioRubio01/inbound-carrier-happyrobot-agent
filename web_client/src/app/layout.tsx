/**
 * @file: layout.tsx
 * @description: Root layout component that provides theme, language, and global styling for the entire application
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import '../styles/dark-mode.css';
import '../styles/light-mode.css';
import { ThemeProvider } from '@/lib/theme-provider';
import { LanguageProvider } from '@/lib/language-provider';
import { QueryProvider } from '@/lib/query-provider';
import { cn } from '@/lib/utils';
import { Toaster } from '@/components/ui/toaster';
import { UserProvider } from '@/contexts/UserContext';
import { I18nProvider } from '@/contexts/I18nContext';
import 'reactflow/dist/style.css';

// Import polyfill for Promise.withResolvers
import '@/lib/polyfills/promise-with-resolvers.js';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'HappyRobot',
  description: 'AI-Powered Document Processing System',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={cn(
          inter.className,
          'min-h-screen antialiased',
          'bg-background text-foreground',
          'transition-colors duration-300',
          'font-medium tracking-tight'
        )}
      >
        <ThemeProvider>
          <QueryProvider>
            <I18nProvider>
              <UserProvider>
                <LanguageProvider>
                  <div className="relative flex min-h-screen flex-col">
                    {children}
                    <Toaster />
                  </div>
                </LanguageProvider>
              </UserProvider>
            </I18nProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
