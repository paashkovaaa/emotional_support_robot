import { useState } from 'react';
import { Eye, EyeOff, Loader2, Mail, Lock } from 'lucide-react';

interface LoginFormProps {
  onSubmit: (email: string, password: string) => Promise<void>;
  onGoToRegister: () => void;
}

export default function LoginForm({ onSubmit, onGoToRegister }: LoginFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password.trim()) {
      setError('Заповніть усі поля');
      return;
    }

    setLoading(true);
    try {
      await onSubmit(email.trim(), password);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } };
        if (axiosErr.response?.status === 401 || axiosErr.response?.status === 400) {
          setError('Невірний email або пароль');
        } else if (axiosErr.response?.data?.detail) {
          setError(axiosErr.response.data.detail);
        } else {
          setError('Помилка входу. Спробуйте пізніше.');
        }
      } else {
        setError('Помилка з\'єднання з сервером');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Email */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
          Електронна пошта
        </label>
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-gray-400" />
          <input
            id="email"
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
        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1.5">
          Пароль
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-gray-400" />
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
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
            Вхід...
          </>
        ) : (
          'Увійти'
        )}
      </button>

      {/* Register link */}
      <p className="text-center text-sm text-gray-500">
        Немає акаунту?{' '}
        <button
          type="button"
          onClick={onGoToRegister}
          className="text-primary-600 hover:text-primary-700 font-medium"
        >
          Зареєструватися
        </button>
      </p>
    </form>
  );
}

