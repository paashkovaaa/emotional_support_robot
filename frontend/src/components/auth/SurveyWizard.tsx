import { useState } from 'react';
import {
  MessageSquare,
  Heart,
  Brain,
  Loader2,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
import type { CommunicationStyle, SurveyRequest } from '../../types';

interface SurveyWizardProps {
  nickname: string;
  onComplete: (data: SurveyRequest) => Promise<void>;
}

const TOTAL_STEPS = 4;

/** Опції стилю спілкування */
const STYLE_OPTIONS: { value: CommunicationStyle; icon: React.ReactNode; title: string; description: string }[] = [
  {
    value: 'analytical',
    icon: <Brain className="w-6 h-6" />,
    title: 'Аналітичний',
    description: 'Структуровані відповіді, техніки, конкретні кроки та пояснення.',
  },
  {
    value: 'friendly',
    icon: <Heart className="w-6 h-6" />,
    title: 'Дружній',
    description: 'Тепле спілкування, підтримка, як розмова з близьким другом.',
  },
  {
    value: 'balanced',
    icon: <MessageSquare className="w-6 h-6" />,
    title: 'Збалансований',
    description: 'Поєднання теплоти та структурованості — підлаштується під настрій.',
  },
];

/** Опції сфери життя */
const LIFE_AREAS = [
  '💼 Робота та кар\'єра',
  '💕 Стосунки',
  '🏠 Сім\'я',
  '📚 Навчання',
  '🧘 Здоров\'я',
  '💰 Фінанси',
  '🎨 Самореалізація',
  '🤝 Соціальне життя',
];

export default function SurveyWizard({ nickname, onComplete }: SurveyWizardProps) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Дані форми
  const [communicationStyle, setCommunicationStyle] = useState<CommunicationStyle>('balanced');
  const [lifeArea, setLifeArea] = useState<string | null>(null);
  const [concern, setConcern] = useState('');
  const [worksWithPsychologist, setWorksWithPsychologist] = useState(false);

  const canGoNext = () => {
    if (step === 1) return true; // стиль завжди обраний
    if (step === 2) return true; // life_area опціонально
    if (step === 3) return true; // concern опціонально
    return true;
  };

  const handleNext = () => {
    if (step < TOTAL_STEPS) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await onComplete({
        communication_style: communicationStyle,
        life_area: lifeArea,
        concern: concern.trim() || null,
        works_with_psychologist: worksWithPsychologist,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-lg mx-auto">
      {/* Progress */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-500">Крок {step} з {TOTAL_STEPS}</span>
          <span className="text-sm text-gray-500">{Math.round((step / TOTAL_STEPS) * 100)}%</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${(step / TOTAL_STEPS) * 100}%` }}
          />
        </div>
      </div>

      {/* Step 1: Communication Style */}
      {step === 1 && (
        <div className="space-y-4">
          <div className="text-center mb-6">
            <h2 className="text-xl font-bold text-gray-800">
              Привіт, {nickname}! 👋
            </h2>
            <p className="text-sm text-gray-500 mt-2">
              Як тобі зручніше спілкуватися? Це допоможе мені підлаштуватися.
            </p>
          </div>

          <div className="space-y-3">
            {STYLE_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => setCommunicationStyle(option.value)}
                className={`w-full p-4 rounded-xl border-2 text-left transition-all
                  ${
                    communicationStyle === option.value
                      ? 'border-primary-500 bg-primary-50 shadow-sm'
                      : 'border-gray-100 bg-white hover:border-gray-200'
                  }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
                      ${
                        communicationStyle === option.value
                          ? 'bg-primary-100 text-primary-600'
                          : 'bg-gray-100 text-gray-400'
                      }`}
                  >
                    {option.icon}
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">{option.title}</p>
                    <p className="text-sm text-gray-500 mt-0.5">{option.description}</p>
                  </div>
                  {communicationStyle === option.value && (
                    <CheckCircle2 className="w-5 h-5 text-primary-500 flex-shrink-0 mt-0.5" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Life Area */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="text-center mb-6">
            <h2 className="text-xl font-bold text-gray-800">
              Яка сфера найважливіша? 🎯
            </h2>
            <p className="text-sm text-gray-500 mt-2">
              Обери сферу, в якій хочеш покращити свій стан. Можна пропустити.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {LIFE_AREAS.map((area) => (
              <button
                key={area}
                onClick={() => setLifeArea(lifeArea === area ? null : area)}
                className={`p-3 rounded-xl border-2 text-sm font-medium transition-all
                  ${
                    lifeArea === area
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-100 bg-white text-gray-600 hover:border-gray-200'
                  }`}
              >
                {area}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 3: Concern */}
      {step === 3 && (
        <div className="space-y-4">
          <div className="text-center mb-6">
            <h2 className="text-xl font-bold text-gray-800">
              Що тебе турбує? 💭
            </h2>
            <p className="text-sm text-gray-500 mt-2">
              Розкажи коротко, що б ти хотів(ла) обговорити. Це залишиться конфіденційним.
            </p>
          </div>

          <textarea
            value={concern}
            onChange={(e) => setConcern(e.target.value)}
            placeholder="Наприклад: тривога через роботу, складності у стосунках, втома..."
            rows={4}
            maxLength={1000}
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm resize-none
                       focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500
                       transition placeholder:text-gray-400"
          />
          <p className="text-xs text-gray-400 text-right">{concern.length}/1000</p>
        </div>
      )}

      {/* Step 4: Psychologist + Finish */}
      {step === 4 && (
        <div className="space-y-6">
          <div className="text-center mb-6">
            <h2 className="text-xl font-bold text-gray-800">
              Останнє питання 🌿
            </h2>
            <p className="text-sm text-gray-500 mt-2">
              Чи працюєш ти зараз з психологом або психотерапевтом?
            </p>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => setWorksWithPsychologist(true)}
              className={`w-full p-4 rounded-xl border-2 text-left transition-all
                ${
                  worksWithPsychologist
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-100 bg-white hover:border-gray-200'
                }`}
            >
              <p className="font-medium text-gray-800">✅ Так, працюю</p>
              <p className="text-sm text-gray-500 mt-1">
                Чудово! Я доповнюватиму ваші сесії між зустрічами.
              </p>
            </button>

            <button
              onClick={() => setWorksWithPsychologist(false)}
              className={`w-full p-4 rounded-xl border-2 text-left transition-all
                ${
                  !worksWithPsychologist
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-100 bg-white hover:border-gray-200'
                }`}
            >
              <p className="font-medium text-gray-800">❌ Ні, не працюю</p>
              <p className="text-sm text-gray-500 mt-1">
                Не проблема! Але пам'ятай, що я — допоміжний інструмент, не заміна терапії.
              </p>
            </button>
          </div>

          {/* Disclaimer */}
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <p className="text-sm text-amber-800 leading-relaxed">
              ⚠️ <strong>Важливо:</strong> Я — віртуальний помічник на основі ШІ.
              Я не ставлю діагнозів і не замінюю фахівця. У кризовій ситуації
              телефонуйте: <strong>103</strong> або <strong>7333</strong> (Лайфлайн Україна).
            </p>
          </div>
        </div>
      )}

      {/* Navigation buttons */}
      <div className="flex items-center justify-between mt-8">
        {step > 1 ? (
          <button
            onClick={handleBack}
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition"
          >
            <ChevronLeft className="w-4 h-4" />
            Назад
          </button>
        ) : (
          <div />
        )}

        {step < TOTAL_STEPS ? (
          <button
            onClick={handleNext}
            disabled={!canGoNext()}
            className="flex items-center gap-1.5 px-5 py-2.5 bg-primary-600 hover:bg-primary-700
                       disabled:bg-primary-300 text-white font-medium rounded-xl text-sm transition-colors"
          >
            Далі
            <ChevronRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 bg-primary-600 hover:bg-primary-700
                       disabled:bg-primary-300 text-white font-medium rounded-xl text-sm transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Збереження...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Почати спілкування
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

