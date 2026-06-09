import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { Loader2 } from 'lucide-react';

interface PrivateRouteProps {
  children: React.ReactNode;
  /** Вимагати роль admin */
  adminOnly?: boolean;
  /** Вимагати завершене опитування */
  requireSurvey?: boolean;
}

/**
 * Компонент-обгортка для захищених маршрутів.
 *
 * - Перенаправляє на /login якщо не авторизований
 * - Перенаправляє на /survey якщо опитування не завершено
 * - Перенаправляє на /emotions якщо не admin (для admin-only)
 */
export default function PrivateRoute({
  children,
  adminOnly = false,
  requireSurvey = true,
}: PrivateRouteProps) {
  const { isAuthenticated, user, profile, initialized, loading } = useAuthStore();
  const location = useLocation();

  // Ще не завантажено — показуємо лоадер
  if (!initialized || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-primary-50/30">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
          <p className="text-sm text-gray-500">Завантаження...</p>
        </div>
      </div>
    );
  }

  // Не авторизований — на логін
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Admin-only маршрут
  if (adminOnly && user?.role !== 'admin') {
    return <Navigate to="/emotions" replace />;
  }

  // Опитування не завершено — перенаправляємо (але не на сторінці survey)
  if (
    requireSurvey &&
    profile &&
    !profile.survey_completed &&
    location.pathname !== '/survey'
  ) {
    return <Navigate to="/survey" replace />;
  }

  return <>{children}</>;
}

