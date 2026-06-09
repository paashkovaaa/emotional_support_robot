import { useNavigate } from 'react-router-dom';
import { Heart } from 'lucide-react';
import { RegisterForm } from '../components/auth';
import { useAuthStore } from '../stores/authStore';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuthStore();

  const handleRegister = async (email: string, password: string, nickname: string) => {
    await register(email, password, nickname);
    // Після реєстрації + автологіну → на опитування
    navigate('/survey', { replace: true });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-accent-50/30
                    dark:from-gray-950 dark:via-gray-900 dark:to-gray-950
                    flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo / Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900/40 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Heart className="w-8 h-8 text-primary-600 dark:text-primary-400" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Реєстрація</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Створіть акаунт для емоційної підтримки 🌱
          </p>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 p-6">
          <RegisterForm
            onSubmit={handleRegister}
            onGoToLogin={() => navigate('/login')}
          />
        </div>
      </div>
    </div>
  );
}

