import { useNavigate, useLocation } from 'react-router-dom';
import { Heart } from 'lucide-react';
import { LoginForm } from '../components/auth';
import { useAuthStore } from '../stores/authStore';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuthStore();

  // Куди перенаправити після входу
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/emotions';

  const handleLogin = async (email: string, password: string) => {
    await login(email, password);
    const profile = useAuthStore.getState().profile;
    if (profile && !profile.survey_completed) {
      navigate('/survey', { replace: true });
    } else {
      navigate(from, { replace: true });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-accent-50/30
                    dark:from-gray-950 dark:via-gray-900 dark:to-gray-950
                    flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo / Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Heart className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-600">Вхід</h1>
          <p className="text-sm text-gray-500 mt-1">
            Раді бачити вас знову 💙
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
          <LoginForm
            onSubmit={handleLogin}
            onGoToRegister={() => navigate('/register')}
          />
        </div>
      </div>
    </div>
  );
}

