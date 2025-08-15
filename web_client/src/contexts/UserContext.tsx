/**
 * @file: UserContext.tsx
 * @description: User context for managing user state and authentication
 */

'use client';

import * as React from 'react';

interface User {
  id: string;
  email: string;
  name: string;
  role?: string;
}

interface UserContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
}

const UserContext = React.createContext<UserContextType | undefined>(undefined);

interface UserProviderProps {
  children: React.ReactNode;
}

export function UserProvider({ children }: UserProviderProps) {
  const [user, setUser] = React.useState<User | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  const isAuthenticated = user !== null;

  const login = React.useCallback((user: User) => {
    setUser(user);
    setIsLoading(false);
  }, []);

  const logout = React.useCallback(() => {
    setUser(null);
    setIsLoading(false);
  }, []);

  const updateUser = React.useCallback((updates: Partial<User>) => {
    setUser(current => current ? { ...current, ...updates } : null);
  }, []);

  // Initialize user state (in a real app, this would check for stored auth)
  React.useEffect(() => {
    // For POC purposes, we'll just set loading to false
    // In a real app, you'd check localStorage, cookies, or make an API call
    setIsLoading(false);
  }, []);

  const value = React.useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated,
      login,
      logout,
      updateUser,
    }),
    [user, isLoading, isAuthenticated, login, logout, updateUser]
  );

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = React.useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
