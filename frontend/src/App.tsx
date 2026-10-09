import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactElement } from "react";
import { useAuth } from "./auth";
import Layout from "./components/Layout";
import Landing from "./pages/Landing";
import Guide from "./pages/Guide";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import NewComplaint from "./pages/NewComplaint";
import MyComplaints from "./pages/MyComplaints";
import Officer from "./pages/Officer";
import AdminQueue from "./pages/AdminQueue";
import AdminAnalytics from "./pages/AdminAnalytics";
import AdminSettings from "./pages/AdminSettings";

const HOME: Record<string, string> = { citizen: "/new", officer: "/officer", admin: "/admin/queue" };

function Guard({ role, children }: { role: string; children: ReactElement }) {
  const { session } = useAuth();
  if (!session) return <Navigate to="/login" replace />;
  if (session.role !== role) return <Navigate to={HOME[session.role] ?? "/login"} replace />;
  return children;
}

export default function App() {
  const { session } = useAuth();
  const toHome = session ? <Navigate to={HOME[session.role]} replace /> : null;
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={toHome ?? <Login mode="login" />} />
        <Route path="/register" element={toHome ?? <Login mode="register" />} />
        <Route path="/guide" element={<Guide />} />
        <Route path="/profile" element={session ? <Profile /> : <Navigate to="/login" replace />} />
        <Route path="/new" element={<Guard role="citizen"><NewComplaint /></Guard>} />
        <Route path="/mine" element={<Guard role="citizen"><MyComplaints /></Guard>} />
        <Route path="/officer" element={<Guard role="officer"><Officer /></Guard>} />
        <Route path="/admin/queue" element={<Guard role="admin"><AdminQueue /></Guard>} />
        <Route path="/admin/analytics" element={<Guard role="admin"><AdminAnalytics /></Guard>} />
        <Route path="/admin/settings" element={<Guard role="admin"><AdminSettings /></Guard>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
