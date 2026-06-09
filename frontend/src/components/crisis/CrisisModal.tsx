import { useEffect, useRef } from 'react';
import { X, Phone, ExternalLink, HeartHandshake, ShieldAlert } from 'lucide-react';

interface CrisisContact {
  name_uk: string;
  phone: string;
  description_uk: string;
  available: string;
  type: 'emergency' | 'crisis_hotline' | 'mental_health' | 'youth';
}

interface CrisisModalProps {
  open: boolean;
  onClose: () => void;
}

const CRISIS_CONTACTS: CrisisContact[] = [
  {
    name_uk: 'Екстрена медична допомога',
    phone: '103',
    description_uk: 'Швидка допомога — телефонуйте у разі загрози життю',
    available: '24/7',
    type: 'emergency',
  },
  {
    name_uk: 'Лайфлайн Україна',
    phone: '7333',
    description_uk: 'Гаряча лінія психологічної підтримки. Безкоштовно з мобільного.',
    available: '24/7',
    type: 'crisis_hotline',
  },
  {
    name_uk: 'Національна гаряча лінія з психічного здоров\'я',
    phone: '0 800 500 335',
    description_uk: 'Безкоштовна психологічна допомога. Конфіденційно.',
    available: '24/7',
    type: 'mental_health',
  },
  {
    name_uk: 'Поліція',
    phone: '102',
    description_uk: 'У разі загрози насильства або домашнього насильства',
    available: '24/7',
    type: 'emergency',
  },
  {
    name_uk: 'Гаряча лінія для дітей та молоді',
    phone: '0 800 500 225',
    description_uk: 'La Strada — Національна гаряча лінія з протидії насильству',
    available: 'Пн-Пт 10:00-18:00',
    type: 'youth',
  },
];

const TYPE_STYLES: Record<CrisisContact['type'], { bg: string; icon: string; border: string }> = {
  emergency: { bg: 'bg-red-50', icon: 'text-red-600', border: 'border-red-200' },
  crisis_hotline: { bg: 'bg-orange-50', icon: 'text-orange-600', border: 'border-orange-200' },
  mental_health: { bg: 'bg-blue-50', icon: 'text-blue-600', border: 'border-blue-200' },
  youth: { bg: 'bg-purple-50', icon: 'text-purple-600', border: 'border-purple-200' },
};

export default function CrisisModal({ open, onClose }: CrisisModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onClose]);

  // Prevent body scroll when open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-auto animate-in">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-900 rounded-t-2xl border-b border-gray-100 dark:border-gray-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 dark:bg-red-900/40 rounded-xl flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-800 dark:text-gray-100">Потрібна допомога?</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">Ви не самотні. Зверніться за підтримкою.</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Disclaimer */}
        <div className="px-6 pt-4 pb-2">
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-xl p-3.5">
            <p className="text-sm text-amber-800 dark:text-amber-300 leading-relaxed">
              <HeartHandshake className="w-4 h-4 inline mr-1.5 -mt-0.5" />
              Якщо ви або хтось з ваших близьких перебуває у кризовому стані — зверніться за
              допомогою. Звертатися по допомогу — це нормально і правильно.
            </p>
          </div>
        </div>

        {/* Contacts list */}
        <div className="px-6 py-4 space-y-3">
          {CRISIS_CONTACTS.map((contact) => {
            const style = TYPE_STYLES[contact.type];
            return (
              <div
                key={contact.phone}
                className={`${style.bg} border ${style.border} rounded-xl p-4 transition-shadow hover:shadow-md dark:bg-opacity-20`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
                      {contact.name_uk}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">
                      {contact.description_uk}
                    </p>
                    <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">
                      🕐 {contact.available}
                    </p>
                  </div>
                  <a
                    href={`tel:${contact.phone.replace(/\s/g, '')}`}
                    className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-semibold
                      ${style.bg} ${style.icon} border ${style.border}
                      hover:shadow-sm transition-all flex-shrink-0 dark:bg-opacity-30`}
                  >
                    <Phone className="w-3.5 h-3.5" />
                    {contact.phone}
                  </a>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-6 pb-5 pt-2">
          <a
            href="https://www.who.int/campaigns/connecting-for-life"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
            Більше ресурсів для допомоги
          </a>
        </div>
      </div>
    </div>
  );
}
