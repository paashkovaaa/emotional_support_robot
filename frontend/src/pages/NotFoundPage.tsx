import { useNavigate } from 'react-router-dom';
import { Home, ArrowLeft, Heart } from 'lucide-react';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-primary-50/30 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        {/* Big 404 */}
        <div className="relative mb-6">
          <p className="text-[120px] sm:text-[150px] font-extrabold text-gray-100 leading-none select-none">
            404
          </p>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center animate-pulse">
              <Heart className="w-10 h-10 text-primary-500" />
            </div>
          </div>
        </div>

        {/* Message */}
        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          Сторінку не знайдено
        </h1>
        <p className="text-sm text-gray-500 leading-relaxed mb-8">
          Вибачте, але ця сторінка не існує або була переміщена.
          Давайте повернемось до чогось корисного! 💚
        </p>

        {/* Actions */}
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 px-5 py-2.5 bg-gray-100 hover:bg-gray-200
                       text-gray-700 font-medium rounded-xl text-sm transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Назад
          </button>
          <button
            onClick={() => navigate('/chat')}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary-600 hover:bg-primary-700
                       text-white font-medium rounded-xl text-sm transition-colors"
          >
            <Home className="w-4 h-4" />
            На головну
          </button>
        </div>
      </div>
    </div>
  );
}

