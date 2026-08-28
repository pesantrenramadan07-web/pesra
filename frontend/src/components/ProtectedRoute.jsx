import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { LoadingState } from "@/components/PageState";

export default function ProtectedRoute({ children, perm }) {
  const { user, loading, can } = useAuth();
  if (loading || user === null) {
    return <div className="min-h-screen flex items-center justify-center"><LoadingState label="Memeriksa sesi..." /></div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  if (perm && !can(perm)) return <Navigate to="/" replace />;
  return children;
}
