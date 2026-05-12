/**
 * Bug Condition Exploration Tests - Task 1
 *
 * Regression tests for production deployment env handling.
 *
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.6
 */

// ---------------------------------------------------------------------------
// Test 1a -- API client falls back to Vercel hostname:8000 (Defect 1)
// ---------------------------------------------------------------------------

describe('Test 1a -- API client falls back to Vercel hostname:8000 (Defect 1)', () => {
    /**
     * On unfixed code, when VITE_API_BASE_URL is unset and window.location.hostname
     * is the Vercel domain, backendBaseUrl resolves to
     * "http://reconx-elite-frontend.vercel.app:8000" -- an unreachable address.
     *
     * This test MUST FAIL on unfixed code -- failure confirms Defect 1 exists.
     * After the fix, backendBaseUrl will read VITE_API_URL instead.
     *
     * Validates: Requirements 1.1, 1.2
     */

    const VERCEL_HOSTNAME = 'reconx-elite-frontend.vercel.app';
    const RAILWAY_URL = 'https://reconx-elite-backend.up.railway.app';

    let originalHostname;

    beforeEach(() => {
        // Save and override window.location.hostname to simulate Vercel deployment
        originalHostname = window.location.hostname;
        Object.defineProperty(window, 'location', {
            value: { ...window.location, hostname: VERCEL_HOSTNAME },
            writable: true,
            configurable: true,
        });

        delete process.env.VITE_API_BASE_URL;
        process.env.VITE_API_URL = RAILWAY_URL;

        // Reset module registry so client.js re-evaluates with the new env
        jest.resetModules();
    });

    afterEach(() => {
        Object.defineProperty(window, 'location', {
            value: { ...window.location, hostname: originalHostname },
            writable: true,
            configurable: true,
        });
        delete process.env.VITE_API_URL;
        delete process.env.VITE_API_BASE_URL;
        jest.resetModules();
    });

    it('backendBaseUrl should equal the Railway URL, not the Vercel hostname:8000', async () => {
        // Re-import client.js after env manipulation so module-level code re-runs
        const { backendBaseUrl } = await import('../api/client.js');

        // On unfixed code: backendBaseUrl = "http://reconx-elite-frontend.vercel.app:8000"
        // because the code reads VITE_API_BASE_URL (unset -> "") and falls back to
        // resolveDefaultBackendBaseUrl() which returns http://${window.location.hostname}:8000.
        //
        // COUNTEREXAMPLE: backendBaseUrl contains Vercel hostname instead of Railway URL.
        //
        // This assertion FAILS on unfixed code (confirming Defect 1).
        // After the fix, backendBaseUrl will equal RAILWAY_URL.
        expect(backendBaseUrl).toBe(RAILWAY_URL);
        expect(backendBaseUrl).not.toContain(VERCEL_HOSTNAME);
        expect(backendBaseUrl).not.toContain(':8000');
    });
});

// ---------------------------------------------------------------------------
// Test 1d -- WebSocket hook falls back to Vercel hostname:8000 (Defect 5)
// ---------------------------------------------------------------------------

describe('Test 1d -- WebSocket hook falls back to Vercel hostname:8000 (Defect 5)', () => {
    /**
     * On unfixed code, when VITE_API_BASE_URL is unset and window.location.hostname
     * is the Vercel domain, the WebSocket URL resolves to
     * "ws://reconx-elite-frontend.vercel.app:8000" -- an unreachable address.
     *
     * The unfixed useScanWebSocket.js reads VITE_API_BASE_URL (not VITE_WS_URL) and
     * falls back to window.location.hostname:8000 when unset.
     *
     * This test MUST FAIL on unfixed code -- failure confirms Defect 5 exists.
     * After the fix, the hook will read VITE_WS_URL instead.
     *
     * Validates: Requirements 1.6
     */

    const VERCEL_HOSTNAME = 'reconx-elite-frontend.vercel.app';
    const RAILWAY_WS_URL = 'wss://reconx-elite-backend.up.railway.app';

    let originalHostname;

    beforeEach(() => {
        // Save and override window.location.hostname to simulate Vercel deployment
        originalHostname = window.location.hostname;
        Object.defineProperty(window, 'location', {
            value: { ...window.location, hostname: VERCEL_HOSTNAME },
            writable: true,
            configurable: true,
        });

        delete process.env.VITE_API_URL;
        delete process.env.VITE_API_BASE_URL;
        process.env.VITE_WS_URL = RAILWAY_WS_URL;

        // Reset module registry so useScanWebSocket.js re-evaluates with the new env
        jest.resetModules();
    });

    afterEach(() => {
        Object.defineProperty(window, 'location', {
            value: { ...window.location, hostname: originalHostname },
            writable: true,
            configurable: true,
        });
        delete process.env.VITE_WS_URL;
        jest.resetModules();
    });

    it('WebSocket URL should use VITE_WS_URL (Railway wss://), not fall back to ws://Vercel-hostname:8000', async () => {
        // The unfixed resolveWebSocketBaseUrl() logic in useScanWebSocket.js:
        //
        //   const configuredBackendBaseUrl =
        //     process.env.VITE_API_BASE_URL === '/api/v1' ? '' : process.env.VITE_API_BASE_URL;
        //
        //   function resolveWebSocketBaseUrl() {
        //     const baseUrl = configuredBackendBaseUrl ||
        //       (typeof window === 'undefined' ? 'http://localhost:8000' : `http://${window.location.hostname}:8000`);
        //     return baseUrl.replace(/\/+$/, '').replace(/^http:/, 'ws:').replace(/^https:/, 'wss:');
        //   }
        //
        // With VITE_API_BASE_URL unset and hostname = VERCEL_HOSTNAME:
        //   configuredBackendBaseUrl = undefined (falsy)
        //   baseUrl = "http://reconx-elite-frontend.vercel.app:8000"
        //   result  = "ws://reconx-elite-frontend.vercel.app:8000"  <- WRONG
        //
        // The FIXED behavior reads VITE_WS_URL:
        //   result = "wss://reconx-elite-backend.up.railway.app"    <- CORRECT

        const { WS_BASE_URL } = await import('../config/api.js');

        expect(WS_BASE_URL).toBe(RAILWAY_WS_URL);
        expect(WS_BASE_URL).not.toContain(VERCEL_HOSTNAME);
        expect(WS_BASE_URL).not.toContain(':8000');
    });
});
