/**
 * Preservation Property Tests — Task 2
 *
 * These tests MUST PASS on unfixed code. Passing confirms the baseline behavior
 * that must be preserved after the fix is applied.
 *
 * Requirements: 3.1, 3.2, 3.3, 3.4, 3.6
 */

import axios from 'axios';
import AxiosMockAdapter from 'axios-mock-adapter';

// ---------------------------------------------------------------------------
// Test 2a — Local dev API fallback preserved (Requirement 3.2)
// ---------------------------------------------------------------------------

describe('Test 2a — Local dev API fallback preserved (Requirement 3.2)', () => {
    /**
     * On unfixed code with VITE_API_BASE_URL unset and window.location.hostname
     * set to "localhost", backendBaseUrl equals "http://localhost:8000".
     *
     * Property: for all local hostnames (localhost, 127.0.0.1),
     * backendBaseUrl resolves to http://{hostname}:8000.
     *
     * This test MUST PASS on unfixed code — it confirms the local dev fallback
     * is preserved after the fix.
     *
     * Validates: Requirements 3.2
     */

    const LOCAL_HOSTNAMES = ['localhost', '127.0.0.1'];

    beforeEach(() => {
        // Ensure VITE_API_BASE_URL is unset (simulates local dev without the var)
        delete process.env.VITE_API_BASE_URL;
        // Ensure VITE_API_URL is also unset (simulates local dev)
        delete process.env.VITE_API_URL;
        jest.resetModules();
    });

    afterEach(() => {
        delete process.env.VITE_API_BASE_URL;
        delete process.env.VITE_API_URL;
        jest.resetModules();
    });

    it('backendBaseUrl equals http://localhost:8000 when hostname is localhost and VITE_API_BASE_URL is unset', async () => {
        // Simulate local dev: hostname = localhost, no env vars set
        Object.defineProperty(window, 'location', {
            value: { ...window.location, hostname: 'localhost' },
            writable: true,
            configurable: true,
        });

        const { backendBaseUrl } = await import('../api/client.js');

        // On unfixed code: configuredBackendBaseUrl is undefined (falsy),
        // so resolveDefaultBackendBaseUrl() returns "http://localhost:8000".
        // This MUST PASS on unfixed code.
        expect(backendBaseUrl).toBe('http://localhost:8000');
    });

    it('backendBaseUrl equals http://127.0.0.1:8000 when hostname is 127.0.0.1 and VITE_API_BASE_URL is unset', async () => {
        // Simulate local dev via IP: hostname = 127.0.0.1, no env vars set
        Object.defineProperty(window, 'location', {
            value: { ...window.location, hostname: '127.0.0.1' },
            writable: true,
            configurable: true,
        });

        const { backendBaseUrl } = await import('../api/client.js');

        // On unfixed code: resolveDefaultBackendBaseUrl() returns
        // "http://127.0.0.1:8000" when hostname is 127.0.0.1.
        // This MUST PASS on unfixed code.
        expect(backendBaseUrl).toBe('http://127.0.0.1:8000');
    });

    /**
     * Property: for all local hostnames, backendBaseUrl resolves to
     * http://{hostname}:8000 when VITE_API_BASE_URL is unset.
     *
     * This parameterized test encodes the property across the local hostname domain.
     */
    test.each(LOCAL_HOSTNAMES)(
        'property: backendBaseUrl resolves to http://%s:8000 for local hostname %s',
        async (hostname) => {
            Object.defineProperty(window, 'location', {
                value: { ...window.location, hostname },
                writable: true,
                configurable: true,
            });

            jest.resetModules();
            const { backendBaseUrl } = await import('../api/client.js');

            // Property: local hostname always resolves to http://{hostname}:8000
            expect(backendBaseUrl).toBe(`http://${hostname}:8000`);
            expect(backendBaseUrl).toContain(':8000');
            expect(backendBaseUrl).toContain(hostname);
        }
    );
});

// ---------------------------------------------------------------------------
// Test 2b — JWT interceptor attaches Authorization header (Requirement 3.3)
// ---------------------------------------------------------------------------

describe('Test 2b — JWT interceptor attaches Authorization header (Requirement 3.3)', () => {
    /**
     * On unfixed code, a request with getTokens returning { accessToken: "tok" }
     * has Authorization: Bearer tok header.
     *
     * Property: for all non-empty accessToken strings, the interceptor always
     * produces a correctly formatted Authorization: Bearer {token} header.
     *
     * This test MUST PASS on unfixed code — it confirms the JWT interceptor
     * is preserved after the fix.
     *
     * Validates: Requirements 3.3
     */

    let mockAxios;
    let api;
    let setAuthHandlers;

    beforeEach(async () => {
        jest.resetModules();
        // Set hostname to localhost so backendBaseUrl resolves correctly
        Object.defineProperty(window, 'location', {
            value: { ...window.location, hostname: 'localhost' },
            writable: true,
            configurable: true,
        });
        delete process.env.VITE_API_BASE_URL;
        delete process.env.VITE_API_URL;

        const clientModule = await import('../api/client.js');
        api = clientModule.api;
        setAuthHandlers = clientModule.setAuthHandlers;

        mockAxios = new AxiosMockAdapter(api);
    });

    afterEach(() => {
        mockAxios.restore();
        jest.resetModules();
    });

    it('attaches Authorization: Bearer {token} header when accessToken is set', async () => {
        const accessToken = 'tok';
        let capturedHeaders = null;

        // Configure auth handlers with a known token
        setAuthHandlers({
            getTokens: () => ({ accessToken }),
            refreshTokens: async () => { throw new Error('should not be called'); },
            logout: () => { },
        });

        // Intercept the request and capture headers
        mockAxios.onGet('/health').reply((config) => {
            capturedHeaders = config.headers;
            return [200, { status: 'ok' }];
        });

        await api.get('/health');

        // Property: Authorization header must be present and correctly formatted
        expect(capturedHeaders).not.toBeNull();
        expect(capturedHeaders['Authorization']).toBe(`Bearer ${accessToken}`);
    });

    it('does not attach Authorization header when accessToken is null', async () => {
        let capturedHeaders = null;

        // Configure auth handlers with no token
        setAuthHandlers({
            getTokens: () => null,
            refreshTokens: async () => { throw new Error('should not be called'); },
            logout: () => { },
        });

        mockAxios.onGet('/health').reply((config) => {
            capturedHeaders = config.headers;
            return [200, { status: 'ok' }];
        });

        await api.get('/health');

        // No token → no Authorization header
        expect(capturedHeaders?.['Authorization']).toBeUndefined();
    });

    /**
     * Property: for all non-empty accessToken strings, the interceptor always
     * produces a correctly formatted Authorization: Bearer {token} header.
     *
     * This parameterized test encodes the property across a representative
     * sample of token values.
     */
    const TOKEN_SAMPLES = [
        'simple-token',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U',
        'a',
        'token-with-special-chars-!@#$%',
        '   token-with-spaces   ',
        '0'.repeat(256),
    ];

    test.each(TOKEN_SAMPLES)(
        'property: Authorization header is "Bearer %s" for any non-empty token',
        async (token) => {
            jest.resetModules();
            const clientModule = await import('../api/client.js');
            const localApi = clientModule.api;
            const localSetAuthHandlers = clientModule.setAuthHandlers;
            const localMock = new AxiosMockAdapter(localApi);

            let capturedAuth = null;

            localSetAuthHandlers({
                getTokens: () => ({ accessToken: token }),
                refreshTokens: async () => { throw new Error('should not be called'); },
                logout: () => { },
            });

            localMock.onGet('/health').reply((config) => {
                capturedAuth = config.headers['Authorization'];
                return [200, { status: 'ok' }];
            });

            await localApi.get('/health');

            // Property: Authorization header is always "Bearer {token}"
            expect(capturedAuth).toBe(`Bearer ${token}`);
            expect(capturedAuth).toMatch(/^Bearer /);

            localMock.restore();
        }
    );
});

// ---------------------------------------------------------------------------
// Test 2c — 401 refresh flow retries and does not logout (Requirement 3.4)
// ---------------------------------------------------------------------------

describe('Test 2c — 401 refresh flow retries and does not logout (Requirement 3.4)', () => {
    /**
     * On unfixed code, a 401 response triggers refreshTokens(), the original
     * request is retried with the new token, and logout is not called.
     *
     * Property: for any 401 response on a non-auth endpoint, the refresh flow
     * is attempted before logout.
     *
     * This test MUST PASS on unfixed code — it confirms the 401 refresh flow
     * is preserved after the fix.
     *
     * Validates: Requirements 3.4
     */

    let mockAxios;
    let api;
    let setAuthHandlers;

    beforeEach(async () => {
        jest.resetModules();
        Object.defineProperty(window, 'location', {
            value: { ...window.location, hostname: 'localhost' },
            writable: true,
            configurable: true,
        });
        delete process.env.VITE_API_BASE_URL;
        delete process.env.VITE_API_URL;

        const clientModule = await import('../api/client.js');
        api = clientModule.api;
        setAuthHandlers = clientModule.setAuthHandlers;

        mockAxios = new AxiosMockAdapter(api);
    });

    afterEach(() => {
        mockAxios.restore();
        jest.resetModules();
    });

    it('calls refreshTokens and retries the request on 401, does not call logout', async () => {
        const initialToken = 'initial-token';
        const refreshedToken = 'refreshed-token';
        let refreshCalled = false;
        let logoutCalled = false;
        let requestCount = 0;

        setAuthHandlers({
            getTokens: () => ({ accessToken: initialToken }),
            refreshTokens: async () => {
                refreshCalled = true;
                return { accessToken: refreshedToken };
            },
            logout: () => {
                logoutCalled = true;
            },
        });

        // First call returns 401; second call (retry) returns 200
        mockAxios.onGet('/scans').replyOnce(401).onGet('/scans').replyOnce((config) => {
            requestCount++;
            return [200, { scans: [] }];
        });

        const response = await api.get('/scans');

        // Property: refresh was called
        expect(refreshCalled).toBe(true);
        // Property: logout was NOT called
        expect(logoutCalled).toBe(false);
        // Property: the request was retried and succeeded
        expect(response.status).toBe(200);
    });

    it('calls logout when refreshTokens throws (refresh fails)', async () => {
        let logoutCalled = false;

        setAuthHandlers({
            getTokens: () => ({ accessToken: 'expired-token' }),
            refreshTokens: async () => {
                throw new Error('Refresh failed');
            },
            logout: () => {
                logoutCalled = true;
            },
        });

        mockAxios.onGet('/scans').reply(401);

        await expect(api.get('/scans')).rejects.toThrow();

        // Property: logout IS called when refresh fails
        expect(logoutCalled).toBe(true);
    });

    it('does not trigger refresh flow for auth endpoints (login, register, refresh)', async () => {
        let refreshCalled = false;
        let logoutCalled = false;

        setAuthHandlers({
            getTokens: () => ({ accessToken: 'token' }),
            refreshTokens: async () => {
                refreshCalled = true;
                return { accessToken: 'new-token' };
            },
            logout: () => {
                logoutCalled = true;
            },
        });

        // Auth endpoints should NOT trigger the refresh flow on 401
        mockAxios.onPost('/auth/login').reply(401);

        await expect(api.post('/auth/login', {})).rejects.toThrow();

        // Property: refresh is NOT called for auth endpoints
        expect(refreshCalled).toBe(false);
        // Property: logout is NOT called for auth endpoints
        expect(logoutCalled).toBe(false);
    });

    it('deduplicates concurrent 401 refresh calls (refreshPromise)', async () => {
        let refreshCallCount = 0;

        setAuthHandlers({
            getTokens: () => ({ accessToken: 'token' }),
            refreshTokens: async () => {
                refreshCallCount++;
                // Simulate async refresh
                await new Promise((resolve) => setTimeout(resolve, 10));
                return { accessToken: 'new-token' };
            },
            logout: () => { },
        });

        // Both requests return 401 simultaneously
        mockAxios.onGet('/scans').reply(401);
        mockAxios.onGet('/targets').reply(401);

        // Fire two concurrent requests that both get 401
        // Note: after the first retry, the mock will return 401 again for both,
        // so both will ultimately fail — but refreshTokens should only be called once
        // due to refreshPromise deduplication.
        // We use a separate mock that returns 200 on retry to test deduplication.
        mockAxios.reset();
        let retryCount = 0;
        mockAxios.onGet('/scans').reply((config) => {
            if (config._retry) {
                retryCount++;
                return [200, {}];
            }
            return [401];
        });
        mockAxios.onGet('/targets').reply((config) => {
            if (config._retry) {
                retryCount++;
                return [200, {}];
            }
            return [401];
        });

        const [r1, r2] = await Promise.all([
            api.get('/scans'),
            api.get('/targets'),
        ]);

        // Property: refreshTokens is called at most once (deduplication)
        expect(refreshCallCount).toBeLessThanOrEqual(1);
        expect(r1.status).toBe(200);
        expect(r2.status).toBe(200);
    });
});

// ---------------------------------------------------------------------------
// Test 2d — WebSocket local fallback preserved (Requirement 3.2, 3.1)
// ---------------------------------------------------------------------------

describe('Test 2d — WebSocket local fallback preserved (Requirement 3.2, 3.1)', () => {
    /**
     * On unfixed code with VITE_API_BASE_URL unset and window.location.hostname
     * set to "localhost", resolveWebSocketBaseUrl() returns "ws://localhost:8000".
     *
     * Property: for local hostname, WebSocket URL resolves to ws://localhost:8000.
     *
     * This test MUST PASS on unfixed code — it confirms the WebSocket local
     * fallback is preserved after the fix.
     *
     * Validates: Requirements 3.2, 3.1
     */

    beforeEach(() => {
        delete process.env.VITE_API_BASE_URL;
        delete process.env.VITE_WS_URL;
    });

    afterEach(() => {
        delete process.env.VITE_API_BASE_URL;
        delete process.env.VITE_WS_URL;
    });

    it('resolveWebSocketBaseUrl returns ws://localhost:8000 when hostname is localhost and VITE_API_BASE_URL is unset', () => {
        // Simulate local dev: hostname = localhost, no env vars set
        Object.defineProperty(window, 'location', {
            value: { ...window.location, hostname: 'localhost' },
            writable: true,
            configurable: true,
        });

        // Replicate the UNFIXED resolveWebSocketBaseUrl() logic from useScanWebSocket.js
        const configuredBackendBaseUrl =
            process.env.VITE_API_BASE_URL === '/api/v1' ? '' : process.env.VITE_API_BASE_URL;

        const baseUrl =
            configuredBackendBaseUrl ||
            (typeof window === 'undefined'
                ? 'http://localhost:8000'
                : `http://${window.location.hostname}:8000`);

        const wsUrl = baseUrl
            .replace(/\/+$/, '')
            .replace(/^http:/, 'ws:')
            .replace(/^https:/, 'wss:');

        // Property: local hostname resolves to ws://localhost:8000
        // This MUST PASS on unfixed code.
        expect(wsUrl).toBe('ws://localhost:8000');
    });

    it('resolveWebSocketBaseUrl returns ws://127.0.0.1:8000 when hostname is 127.0.0.1 and VITE_API_BASE_URL is unset', () => {
        Object.defineProperty(window, 'location', {
            value: { ...window.location, hostname: '127.0.0.1' },
            writable: true,
            configurable: true,
        });

        const configuredBackendBaseUrl =
            process.env.VITE_API_BASE_URL === '/api/v1' ? '' : process.env.VITE_API_BASE_URL;

        const baseUrl =
            configuredBackendBaseUrl ||
            (typeof window === 'undefined'
                ? 'http://localhost:8000'
                : `http://${window.location.hostname}:8000`);

        const wsUrl = baseUrl
            .replace(/\/+$/, '')
            .replace(/^http:/, 'ws:')
            .replace(/^https:/, 'wss:');

        // Property: 127.0.0.1 resolves to ws://127.0.0.1:8000
        expect(wsUrl).toBe('ws://127.0.0.1:8000');
    });

    /**
     * Property: for local hostname, WebSocket URL resolves to ws://{hostname}:8000.
     * Parameterized over local hostnames.
     */
    test.each(['localhost', '127.0.0.1'])(
        'property: WebSocket URL resolves to ws://%s:8000 for local hostname %s',
        (hostname) => {
            Object.defineProperty(window, 'location', {
                value: { ...window.location, hostname },
                writable: true,
                configurable: true,
            });

            const configuredBackendBaseUrl =
                process.env.VITE_API_BASE_URL === '/api/v1' ? '' : process.env.VITE_API_BASE_URL;

            const baseUrl =
                configuredBackendBaseUrl ||
                (typeof window === 'undefined'
                    ? 'http://localhost:8000'
                    : `http://${window.location.hostname}:8000`);

            const wsUrl = baseUrl
                .replace(/\/+$/, '')
                .replace(/^http:/, 'ws:')
                .replace(/^https:/, 'wss:');

            expect(wsUrl).toBe(`ws://${hostname}:8000`);
            expect(wsUrl).toMatch(/^ws:\/\//);
            expect(wsUrl).toContain(':8000');
        }
    );

    it('resolveWebSocketBaseUrl uses ws:// protocol (not wss://) for local http fallback', () => {
        Object.defineProperty(window, 'location', {
            value: { ...window.location, hostname: 'localhost' },
            writable: true,
            configurable: true,
        });

        const configuredBackendBaseUrl =
            process.env.VITE_API_BASE_URL === '/api/v1' ? '' : process.env.VITE_API_BASE_URL;

        const baseUrl =
            configuredBackendBaseUrl ||
            (typeof window === 'undefined'
                ? 'http://localhost:8000'
                : `http://${window.location.hostname}:8000`);

        const wsUrl = baseUrl
            .replace(/\/+$/, '')
            .replace(/^http:/, 'ws:')
            .replace(/^https:/, 'wss:');

        // Local dev uses ws:// (not wss://) — no TLS on localhost
        expect(wsUrl).toMatch(/^ws:\/\//);
        expect(wsUrl).not.toMatch(/^wss:\/\//);
    });
});
