import { useState } from 'react';
import { Eye, EyeOff, Loader2, Mail, Lock, User } from 'lucide-react';

interface RegisterFormProps {
  onSubmit: (email: string, password: string, nickname: string) => Promise<void>;
  onGoToLogin: () => void;
}

export default function RegisterForm({ onSubmit, onGoToLogin }: RegisterFormProps) {
  const [nickname, setNickname] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!nickname.trim() || !email.trim() || !password.trim()) {
      setError('Заповніть усі поля');
      return;
    }

    if (nickname.trim().length < 2) {
      setError('Нікнейм має бути щонайменше 2 символи');
      return;
    }

    if (password.length < 8) {
      setError('Пароль має бути щонайменше 8 символів');
      return;
    }

    if (password !== confirmPassword) {
      setError('Паролі не збігаються');
      return;
    }

    setLoading(true);
    try {
      await onSubmit(email.trim(), password, nickname.trim());
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } };
        if (axiosErr.response?.status === 409) {
          setError('Користувач з таким email вже існує');
        } else if (axiosErr.response?.data?.detail) {
          setError(axiosErr.response.data.detail);
        } else {
          setError('Помилка реєстрації. Спробуйте пізніше.');
        }
      } else {
        setError('Помилка з\'єднання з сервером');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Nickname */}
      <div>
        <label htmlFor="nickname" className="block text-sm font-medium text-gray-700 mb-1.5">
          Нікнейм
        </label>
        <div className="relative">
          <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-gray-400" />
          <input
            id="nickname"
            type="text"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            placeholder="Як до вас звертатися?"
            autoComplete="username"
            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500
                       transition placeholder:text-gray-400"
          />
        </div>
      </div>

      {/* Email */}
      <div>
        <label htmlFor="reg-email" className="block text-sm font-medium text-gray-700 mb-1.5">
          Електронна пошта
        </label>
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-gray-400" />
          <input
            id="reg-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
            autoComplete="email"
            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500
                       transition placeholder:text-gray-400"
          />
        </div>
      </div>

      {/* Password */}
      <div>
        <label htmlFor="reg-password" className="block text-sm font-medium text-gray-700 mb-1.5">
          Пароль
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-gray-400" />
          <input
            id="reg-password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Мінімум 8 символів"
            autoComplete="new-password"
            className="w-full pl-10 pr-10 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500
                       transition placeholder:text-gray-400"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Confirm password */}
      <div>
        <label htmlFor="reg-confirm" className="block text-sm font-medium text-gray-700 mb-1.5">
          Підтвердіть пароль
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-gray-400" />
          <input
            id="reg-confirm"
            type={showPassword ? 'text' : 'password'}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Повторіть пароль"
            autoComplete="new-password"
            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500
                       transition placeholder:text-gray-400"
          />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
          {error}
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={loading}
        className="w-full py-2.5 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-300
                   text-white font-medium rounded-xl text-sm transition-colors
                   flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Реєстрація...
          </>
        ) : (
          'Створити акаунт'
        )}
      </button>

      {/* Login link */}
      <p className="text-center text-sm text-gray-500">
        Вже є акаунт?{' '}
        <button
          type="button"
          onClick={onGoToLogin}
          className="text-primary-600 hover:text-primary-700 font-medium"
        >
          Увійти
        </button>
      </p>

      {/* Legal links */}
      <p className="text-center text-xs text-gray-400 leading-relaxed">
        Реєструючись, ви погоджуєтесь з{' '}
        <a href="/terms" className="underline hover:text-gray-600">Умовами використання</a>
        {' '}та{' '}
        <a href="/privacy" className="underline hover:text-gray-600">Політикою конфіденційності</a>.
      </p>
    </form>
  );
}

