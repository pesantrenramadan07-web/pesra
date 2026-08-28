import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { PeriodProvider } from "@/context/PeriodContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import Layout from "@/components/Layout";

import Login from "@/pages/Login";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";
import Dashboard from "@/pages/Dashboard";
import Periods from "@/pages/Periods";
import Schools from "@/pages/Schools";
import Teachers from "@/pages/Teachers";
import DailyBoard from "@/pages/DailyBoard";
import Officers from "@/pages/Officers";
import Vehicles from "@/pages/Vehicles";
import Users from "@/pages/Users";
import Roles from "@/pages/Roles";
import Audit from "@/pages/Audit";
import Roster from "@/pages/Roster";
import Placeholder from "@/pages/Placeholder";
import {
  Route as RouteIcon, CalendarDays, Truck, CircleParking,
  UserCheck, ClipboardCheck, Images, FileBarChart2, Star,
} from "lucide-react";

const P = (title, icon, perm) => (
  <ProtectedRoute perm={perm}><Placeholder title={title} icon={icon} /></ProtectedRoute>
);

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <PeriodProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />

            <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/periode" element={<ProtectedRoute perm="PERIOD_VIEW"><Periods /></ProtectedRoute>} />
              <Route path="/sekolah" element={<ProtectedRoute perm="SCHOOL_VIEW"><Schools /></ProtectedRoute>} />
              <Route path="/pengajar" element={<ProtectedRoute perm="TEACHER_VIEW"><Teachers /></ProtectedRoute>} />
              <Route path="/dewan-harian" element={<ProtectedRoute perm="DH_VIEW"><DailyBoard /></ProtectedRoute>} />
              <Route path="/petugas" element={<ProtectedRoute perm="OFFICER_VIEW"><Officers /></ProtectedRoute>} />
              <Route path="/armada" element={<ProtectedRoute perm="VEHICLE_VIEW"><Vehicles /></ProtectedRoute>} />

              <Route path="/roster" element={<ProtectedRoute perm="ROSTER_VIEW"><Roster /></ProtectedRoute>} />
              <Route path="/penugasan" element={P("Penugasan", RouteIcon, "ASSIGNMENT_VIEW")} />
              <Route path="/jadwal" element={P("Jadwal", CalendarDays, "SCHEDULE_VIEW")} />
              <Route path="/pemberangkatan" element={P("Pemberangkatan", Truck, "DEPARTURE_VIEW")} />
              <Route path="/penjemputan" element={P("Penjemputan", CircleParking, "PICKUP_VIEW")} />
              <Route path="/kehadiran" element={P("Kehadiran Pengajar", UserCheck, "ATTENDANCE_VIEW")} />
              <Route path="/monitoring" element={P("Monitoring", ClipboardCheck, "MONITORING_VIEW")} />
              <Route path="/dokumentasi" element={P("Dokumentasi", Images, "DOCUMENTATION_VIEW")} />
              <Route path="/evaluasi-program" element={P("Evaluasi Program", FileBarChart2, "EVALUATION_VIEW")} />
              <Route path="/penilaian-pengajar" element={P("Penilaian Pengajar", Star, "EVALUATION_VIEW")} />
              <Route path="/laporan" element={P("Laporan & Rekap", FileBarChart2, "REPORT_VIEW")} />

              <Route path="/users" element={<ProtectedRoute perm="USER_MANAGE"><Users /></ProtectedRoute>} />
              <Route path="/roles" element={<ProtectedRoute perm="ROLE_MANAGE"><Roles /></ProtectedRoute>} />
              <Route path="/audit" element={<ProtectedRoute perm="AUDIT_VIEW"><Audit /></ProtectedRoute>} />
            </Route>
          </Routes>
        </PeriodProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
