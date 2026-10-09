import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, loadSession, saveSession, setUnauthorizedHandler, type Session } from "./api";

interface Ctx {
  session: Session | null;
  login: (email: string, password: string, role?: string) => Promise<void>;
  register: (name: string, email: string, password: string, phone?: string) => Promise<void>;
  logout: () => void;
}
const AuthContext = createContext<Ctx>(null as unknown as Ctx);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(loadSession());

  const logout = useCallback(() => { saveSession(null); setSession(null); }, []);
  useEffect(() => { setUnauthorizedHandler(logout); }, [logout]);

  const finish = (r: { access_token: string; role: string; name: string }) => {
    const s = { token: r.access_token, role: r.role, name: r.name };
    saveSession(s); setSession(s);
  };
  const login = async (email: string, password: string, role?: string) =>
    finish(await api("/auth/login", { json: { email, password, role: role ?? null } }));
  const register = async (name: string, email: string, password: string, phone?: string) =>
    finish(await api("/auth/register", { json: { name, email, password, phone: phone || null } }));

  return <AuthContext.Provider value={{ session, login, register, logout }}>{children}</AuthContext.Provider>;
}
