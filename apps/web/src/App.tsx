import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from "@/components/ui/toaster";
import { AuthProvider } from '@/contexts/AuthContext';
import Navigation from '@/components/Navigation';
import Index from '@/pages/Index';
import ChatInterface from '@/pages/ChatInterface';
import DocumentEditor from '@/pages/DocumentEditor';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import NotFound from '@/pages/NotFound';
import AdminDashboard from '@/pages/admin/AdminDashboard';
import DocumentManagementPage from '@/pages/admin/DocumentManagementPage';
import UserManagementPage from '@/pages/admin/UserManagementPage';
import type { FC } from 'react';

const App: FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="App min-h-screen bg-background">
          <Navigation />
          <main>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/chat" element={<ChatInterface />} />
              <Route path="/editor" element={<DocumentEditor />} />
              <Route path="/editor/:documentId" element={<DocumentEditor />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/admin/documents" element={<DocumentManagementPage />} />
              <Route path="/admin/users" element={<UserManagementPage />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          <Toaster />
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;
