/**
 * @file: I18nContext.tsx
 * @description: Internationalization context for language management
 */

'use client';

import * as React from 'react';

interface I18nContextType {
  locale: string;
  setLocale: (locale: string) => void;
  t: (key: string, defaultValue?: string) => string;
  formatDate: (date: Date) => string;
  formatCurrency: (amount: number, currency?: string) => string;
}

const I18nContext = React.createContext<I18nContextType | undefined>(undefined);

interface I18nProviderProps {
  children: React.ReactNode;
  defaultLocale?: string;
}

export function I18nProvider({ children, defaultLocale = 'en' }: I18nProviderProps) {
  const [locale, setLocale] = React.useState(defaultLocale);

  // Simple translation function for POC
  const t = React.useCallback((key: string, defaultValue?: string) => {
    // In a real app, this would use proper i18n library
    return defaultValue || key;
  }, []);

  // Simple date formatting
  const formatDate = React.useCallback((date: Date) => {
    return new Intl.DateTimeFormat(locale).format(date);
  }, [locale]);

  // Simple currency formatting
  const formatCurrency = React.useCallback((amount: number, currency = 'USD') => {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
    }).format(amount);
  }, [locale]);

  const value = React.useMemo(
    () => ({
      locale,
      setLocale,
      t,
      formatDate,
      formatCurrency,
    }),
    [locale, setLocale, t, formatDate, formatCurrency]
  );

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = React.useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}
