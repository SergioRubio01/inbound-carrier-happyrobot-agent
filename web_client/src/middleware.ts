/**
 * @file middleware.ts
 * @description Next.js middleware for authentication, redirects, and cookie management.
 * @author HappyRobot Team
 * @created 2025-05-20
 * @lastModified 2025-05-20
 *
 * Modification History:
 * - 2025-05-20: Enhanced clean logout to remove refresh_token and user_info_present cookies.
 *
 * Dependencies:
 * - next/server
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Get the current path and URL
  const { pathname } = request.nextUrl;
  const url = request.nextUrl.clone();

  // Check for token in cookies (not localStorage which isn't available in middleware)
  const token = request.cookies.get('access_token')?.value;

  // Get all cookies for debugging
  const allCookies = request.cookies.getAll();

  // Define path categories
  const isAuthPage = pathname.startsWith('/login') || pathname.startsWith('/register');
  const isDashboardPage = pathname.startsWith('/dashboard');
  const isAdminPage = pathname.startsWith('/admin');
  const isSystemPage = pathname.startsWith('/system');
  const isOAuthCallback = pathname.startsWith('/api/auth/callback');
  const isOnboardingPage = pathname.startsWith('/onboarding');
  const isSettingsPage = pathname.startsWith('/settings');

  // Check for clean logout
  const isCleanLogout = url.searchParams.has('clean');

  // Expanded list of public paths
  const isPublicPage =
    pathname === '/' ||
    pathname.startsWith('/api/') ||
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/debug') ||
    pathname.startsWith('/verify-email') ||
    pathname.startsWith('/test-auth') ||
    pathname.startsWith('/oauth-debug') ||
    isOAuthCallback ||
    pathname.endsWith('.svg') ||
    pathname.endsWith('.png') ||
    pathname.endsWith('.jpg') ||
    pathname.endsWith('.jpeg') ||
    pathname.endsWith('.ico') ||
    pathname.endsWith('.css') ||
    pathname.endsWith('.js');

  // Check if URL has a token parameter (for redirects from OAuth)
  const hasTokenParam = url.searchParams.has('token');
  const tokenFromParam = hasTokenParam ? url.searchParams.get('token') : null;

  // Check for OAuth provider information
  const oauthProvider = url.searchParams.get('provider');

  // Log detailed information about the request
  console.log(`Middleware: Processing ${pathname}`, {
    hasToken: !!token,
    tokenLength: token ? token.length : 0,
    tokenFirstChars: token ? token.substring(0, 10) + '...' : 'None',
    hasTokenParam,
    tokenParamLength: tokenFromParam ? tokenFromParam.length : 0,
    isAuthPage,
    isDashboardPage,
    isAdminPage,
    isSystemPage,
    isPublicPage,
    isOAuthCallback,
    isCleanLogout,
    oauthProvider,
    cookies: allCookies.map((c) => ({
      name: c.name,
      valueLength: c.value.length,
    })),
  });

  // Allow access to public pages and API routes without token checks
  if (isPublicPage) {
    console.log(`Middleware: Allowing access to public page ${pathname}`);
    return NextResponse.next();
  }

  // Handle OAuth callback - always allow and pass provider information
  if (isOAuthCallback) {
    console.log(`Middleware: OAuth callback detected for provider: ${oauthProvider}`);
    const response = NextResponse.next();
    if (oauthProvider) {
      response.cookies.set('oauth_provider', oauthProvider, {
        path: '/',
        maxAge: 60 * 5, // 5 minutes, just enough to complete the flow
        httpOnly: false,
      });
    }
    return response;
  }

  // Handle clean logout - always allow access to login page during clean logout
  if (isCleanLogout && isAuthPage) {
    console.log(`Middleware: Clean logout detected, allowing access to ${pathname}`);

    const response = NextResponse.next();

    response.cookies.delete('access_token');
    response.cookies.delete('refresh_token');
    response.cookies.delete('user_info_present');
    response.cookies.delete('oauth_provider');

    return response;
  }

  // If we have a token parameter but no cookie token, let the page handle setting the token
  if (hasTokenParam && !token && (isDashboardPage || isSystemPage || isOnboardingPage)) {
    console.log(`Middleware: Allowing access to ${pathname} with token parameter`);
    return NextResponse.next();
  }

  // If trying to access protected pages without a token and no token in URL params
  if ((isDashboardPage || isAdminPage || isSystemPage || isOnboardingPage || isSettingsPage) && !token && !hasTokenParam) {
    console.log(`Middleware: Redirecting from ${pathname} to /login (no token)`);
    url.pathname = '/login';
    url.searchParams.delete('clean'); // Remove clean parameter if present
    return NextResponse.redirect(url);
  }

  // If accessing auth pages with a token, redirect to onboarding for new users
  // or dashboard for existing users, but only if we're not in the middle of setting a token
  // and not during a clean logout
  if (isAuthPage && token && !hasTokenParam && !isCleanLogout) {
    // Check if user has completed onboarding
    const onboardingCompleted = request.cookies.get('onboarding_completed')?.value === 'true';

    if (!onboardingCompleted) {
      console.log(
        `Middleware: Redirecting from ${pathname} to /onboarding (new user)`
      );
      url.pathname = '/onboarding';
    } else {
      console.log(`Middleware: Redirecting from ${pathname} to /dashboard (existing user)`);
      url.pathname = '/dashboard';
    }
    url.searchParams.delete('clean'); // Remove clean parameter if present
    return NextResponse.redirect(url);
  }

  // Prevent direct access to dashboard if onboarding is not complete
  // System users accessing admin pages should bypass onboarding requirements
  if (isDashboardPage && !isAdminPage && token && !hasTokenParam) {
    const onboardingCompleted = request.cookies.get('onboarding_completed')?.value === 'true';

    if (!onboardingCompleted) {
      console.log(
        `Middleware: Redirecting from ${pathname} to /onboarding (onboarding not complete)`
      );
      url.pathname = '/onboarding';
      return NextResponse.redirect(url);
    }
  }

  // For all other cases, proceed normally
  return NextResponse.next();
}

export const config = {
  matcher: [
    // Match all routes except static files, api routes, and _next
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
