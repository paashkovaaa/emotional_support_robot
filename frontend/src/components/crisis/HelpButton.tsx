import { useState } from 'react';
import { Phone } from 'lucide-react';
import CrisisModal from './CrisisModal';

interface HelpButtonProps {
  /** Показувати мітку поруч з іконкою (за замовчуванням true) */
  showLabel?: boolean;
  /** CSS-класи для кнопки */
  className?: string;
}

/**
 * Кнопка екстреної допомоги — завжди доступна в Header.
 * Відкриває CrisisModal з контактами підтримки.
 */
export default function HelpButton({ showLabel = true, className }: HelpButtonProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        aria-label="Потрібна допомога"
        className={
          className ??
          `flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-medium
           text-red-600 bg-red-50 hover:bg-red-100
           dark:text-red-400 dark:bg-red-950/40 dark:hover:bg-red-900/50
           border border-red-200 dark:border-red-800
           transition-colors focus:outline-none focus:ring-2 focus:ring-red-400/50`
        }
      >
        <Phone className="w-3.5 h-3.5 flex-shrink-0" />
        {showLabel && <span className="hidden sm:inline">Допомога</span>}
      </button>

      <CrisisModal open={open} onClose={() => setOpen(false)} />
    </>
  );
}

