import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { PrivateRoute } from './components/auth';
import { AppLayout } from './components/layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import SurveyPage from './pages/SurveyPage';
import EmotionDiaryPage from './pages/EmotionDiaryPage';
import ChatPage from './pages/ChatPage';
import BreathingPage from './pages/BreathingPage';
import ProfilePage from './pages/ProfilePage';
import AdminDashboard from './pages/AdminDashboard';
import NotFoundPage from './pages/NotFoundPage';
import PrivacyPolicyPage from './pages/PrivacyPolicyPage';
import TermsOfServicePage from './pages/TermsOfServicePage';
import { Loader2 } from 'lucide-react';

function App() {
  const { initialized, isAuthenticated, loadUser, loadProfile } = useAuthStore();

  // При старті — перевіряємо чи є збережений токен
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      loadUser().then(() => {
        const { isAuthenticated } = useAuthStore.getState();
        if (isAuthenticated) {
          loadProfile();
        }
      });
    } else {
      // Немає токена — позначаємо як ініціалізовано
      useAuthStore.setState({ initialized: true });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Поки ініціалізується — глобальний лоадер
  if (!initialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-primary-50/30">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
          <p className="text-sm text-gray-500">Завантаження...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      {/* ── Публічні маршрути (без Layout) ── */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/chat" replace /> : <LoginPage />}
      />
      <Route
        path="/register"
        element={isAuthenticated ? <Navigate to="/chat" replace /> : <RegisterPage />}
      />
      <Route path="/privacy" element={<PrivacyPolicyPage />} />
      <Route path="/terms" element={<TermsOfServicePage />} />

      {/* Survey — авторизований, але БЕЗ Layout (окрема сторінка) */}
      <Route
        path="/survey"
        element={
          <PrivateRoute requireSurvey={false}>
            <SurveyPage />
          </PrivateRoute>
        }
      />

      {/* ── Захищені маршрути з Layout ── */}
      <Route
        path="/chat"
        element={
          <PrivateRoute>
            <AppLayout hideHeader>
              <ChatPage />
            </AppLayout>
          </PrivateRoute>
        }
      />
      <Route
        path="/emotions"
        element={
          <PrivateRoute>
            <AppLayout>
              <EmotionDiaryPage />
            </AppLayout>
          </PrivateRoute>
        }
      />
      <Route
        path="/breathing"
        element={
          <PrivateRoute>
            <AppLayout>
              <BreathingPage />
            </AppLayout>
          </PrivateRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <PrivateRoute adminOnly>
            <AppLayout>
              <AdminDashboard />
            </AppLayout>
          </PrivateRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <PrivateRoute>
            <AppLayout>
              <ProfilePage />
            </AppLayout>
          </PrivateRoute>
        }
      />

      {/* ── 404 ── */}
      <Route path="/404" element={<NotFoundPage />} />
      <Route path="*" element={isAuthenticated ? <NotFoundPage /> : <Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;

