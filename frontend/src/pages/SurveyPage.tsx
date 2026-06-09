import { useNavigate } from 'react-router-dom';
import { Heart } from 'lucide-react';
import toast from 'react-hot-toast';
import { SurveyWizard } from '../components/auth';
import { useAuthStore } from '../stores/authStore';
import type { SurveyRequest } from '../types';

export default function SurveyPage() {
  const navigate = useNavigate();
  const { profile, completeSurvey } = useAuthStore();

  const nickname = profile?.nickname || 'друже';

  const handleComplete = async (data: SurveyRequest) => {
    try {
      await completeSurvey(data);
      toast.success('Чудово! Тепер ми можемо почати 🎉');
      navigate('/emotions', { replace: true });
    } catch {
      toast.error('Не вдалося зберегти відповіді. Спробуйте ще раз.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-accent-50/30
                    flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="text-center mb-6">
          <div className="w-14 h-14 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <Heart className="w-7 h-7 text-primary-600" />
          </div>
          <p className="text-xs text-gray-400 uppercase tracking-wider font-medium">
            Emotional Support Bot
          </p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
          <SurveyWizard nickname={nickname} onComplete={handleComplete} />
        </div>
      </div>
    </div>
  );
}

