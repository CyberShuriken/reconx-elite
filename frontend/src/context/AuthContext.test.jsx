import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import * as client from "../api/client";
import { AuthProvider, useAuth } from "./AuthContext";

jest.mock("../utils/jwt", () => ({
  decodeJwt: () => ({ role: "user", sub: "42" }),
}));

function Harness() {
  const { login, logout, isAuthenticated, user } = useAuth();
  return (
    <div>
      <span data-testid="auth">{isAuthenticated ? "in" : "out"}</span>
      <span data-testid="uid">{user?.id ?? ""}</span>
      <button type="button" onClick={() => login({ access_token: "a", refresh_token: "r" })}>
        login
      </button>
      <button type="button" onClick={() => logout()}>
        logout
      </button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.spyOn(client.api, "post").mockResolvedValue({
      data: { access_token: "newa", refresh_token: "newr" },
    });
  });

  it("login stores tokens and exposes user id from jwt", async () => {
    render(
      <AuthProvider>
        <Harness />
      </AuthProvider>,
    );
    fireEvent.click(screen.getByText("login"));
    await waitFor(() => {
      expect(screen.getByTestId("auth").textContent).toBe("in");
    });
    expect(screen.getByTestId("uid").textContent).toBe("42");
    const stored = JSON.parse(localStorage.getItem("reconx_auth"));
    expect(stored.accessToken).toBe("a");
    expect(stored.refreshToken).toBe("r");
  });

  it("logout clears storage", async () => {
    render(
      <AuthProvider>
        <Harness />
      </AuthProvider>,
    );
    fireEvent.click(screen.getByText("login"));
    await waitFor(() => expect(screen.getByTestId("auth").textContent).toBe("in"));
    fireEvent.click(screen.getByText("logout"));
    await waitFor(() => expect(screen.getByTestId("auth").textContent).toBe("out"));
    expect(localStorage.getItem("reconx_auth")).toBeNull();
  });
});
