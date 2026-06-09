import { useEffect, useState, useCallback } from 'react';
import { Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { EmotionCalendar, EmotionForm, EmotionCard, BotSuggestionModal } from '../components/emotions';
import { useEmotionStore } from '../stores/emotionStore';
import { useChatStore } from '../stores/chatStore';
import { toISODate } from '../utils/formatters';
import type { EmotionEntry, EmotionEntryCreate, EmotionEntryUpdate } from '../types';

type PanelMode = 'idle' | 'view' | 'create' | 'edit';

export default function EmotionDiaryPage() {
  const {
    entries,
    currentMonth,
    currentYear,
    loading,
    error,
    botSuggestion,
    botSuggestionLoading,
    setMonthYear,
    fetchEntries,
    createEntry,
    updateEntry,
    deleteEntry,
    generateSuggestion,
    clearSuggestion,
  } = useEmotionStore();

  const { conversations, fetchConversations } = useChatStore();

  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [panelMode, setPanelMode] = useState<PanelMode>('idle');
  const [currentEntry, setCurrentEntry] = useState<EmotionEntry | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Завантажуємо записи та розмови при монтуванні
  useEffect(() => {
    fetchEntries(currentMonth, currentYear);
    fetchConversations();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Навігація місяцями
  const handlePrevMonth = useCallback(() => {
    let m = currentMonth - 1;
    let y = currentYear;
    if (m < 1) { m = 12; y -= 1; }
    setMonthYear(m, y);
    setSelectedDate(null);
    setPanelMode('idle');
    setCurrentEntry(null);
  }, [currentMonth, currentYear, setMonthYear]);

  const handleNextMonth = useCallback(() => {
    let m = currentMonth + 1;
    let y = currentYear;
    if (m > 12) { m = 1; y += 1; }
    setMonthYear(m, y);
    setSelectedDate(null);
    setPanelMode('idle');
    setCurrentEntry(null);
  }, [currentMonth, currentYear, setMonthYear]);

  // Клік по дню в календарі
  const handleSelectDate = useCallback(
    (dateStr: string) => {
      setSelectedDate(dateStr);
      const entry = entries.find((e) => e.entry_date === dateStr);
      if (entry) {
        setCurrentEntry(entry);
        setPanelMode('view');
      } else {
        setCurrentEntry(null);
        setPanelMode('create');
      }
    },
    [entries],
  );

  // Зберегти новий запис
  const handleCreate = async (data: EmotionEntryCreate | EmotionEntryUpdate) => {
    setSaving(true);
    try {
      const created = await createEntry(data as EmotionEntryCreate);
      setCurrentEntry(created);
      setPanelMode('view');
      toast.success('Запис збережено ✨');
    } catch {
      toast.error('Не вдалося зберегти запис');
    } finally {
      setSaving(false);
    }
  };

  // Оновити запис
  const handleUpdate = async (data: EmotionEntryCreate | EmotionEntryUpdate) => {
    if (!currentEntry) return;
    setSaving(true);
    try {
      const updated = await updateEntry(currentEntry.id, data as EmotionEntryUpdate);
      setCurrentEntry(updated);
      setPanelMode('view');
      toast.success('Запис оновлено');
    } catch {
      toast.error('Не вдалося оновити запис');
    } finally {
      setSaving(false);
    }
  };

  // Видалити запис
  const handleDelete = async () => {
    if (!currentEntry) return;
    const confirmed = window.confirm('Видалити цей запис? Цю дію не можна скасувати.');
    if (!confirmed) return;

    setDeleting(true);
    try {
      await deleteEntry(currentEntry.id);
      setCurrentEntry(null);
      setPanelMode('idle');
      setSelectedDate(null);
      toast.success('Запис видалено');
    } catch {
      toast.error('Не вдалося видалити запис');
    } finally {
      setDeleting(false);
    }
  };

  // AI пропозиція — беремо останню завершену або активну розмову
  const handleRequestBotSuggestion = () => {
    // Пріоритет: остання завершена розмова (має повний контекст), потім активна
    const lastConversation =
      conversations.find((c) => c.status === 'ended') ??
      conversations[0] ??
      null;

    if (!lastConversation) {
      toast('Спочатку поговори з Emi — тоді AI зможе запропонувати запис 🤖', { icon: '💬' });
      return;
    }

    generateSuggestion(lastConversation.id, selectedDate ?? undefined);
  };

  // Зберегти пропозицію бота як запис
  const handleSaveSuggestion = async (data: { emoji: string; description: string; tags: string[] }) => {
    if (!selectedDate) return;
    setSaving(true);
    try {
      if (currentEntry) {
        const updated = await updateEntry(currentEntry.id, {
          emoji: data.emoji,
          bot_description: data.description,
          emotion_tags: data.tags,
        });
        setCurrentEntry(updated);
      } else {
        const created = await createEntry({
          entry_date: selectedDate,
          emoji: data.emoji,
          bot_description: data.description,
          emotion_tags: data.tags,
        });
        setCurrentEntry(created);
      }
      clearSuggestion();
      setPanelMode('view');
      toast.success('Пропозицію Emi збережено ✨');
    } catch {
      toast.error('Не вдалося зберегти');
    } finally {
      setSaving(false);
    }
  };

  // Сьогодні — відображаємо підсказку
  const todayStr = toISODate(new Date());
  const hasTodayEntry = entries.some((e) => e.entry_date === todayStr);

  return (
    <div className="h-full">
      {/* Кнопка "Записати за сьогодні" */}
      {!hasTodayEntry && (
        <div className="px-4 lg:px-6 pt-4">
          <button
            onClick={() => handleSelectDate(todayStr)}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white
                       rounded-xl text-sm font-medium transition-colors flex items-center gap-2"
          >
            <span>📝</span>
            Записати за сьогодні
          </button>
        </div>
      )}

      {/* Main content */}
      <div className="max-w-6xl mx-auto px-4 lg:px-6 py-6">
        {/* Error */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Ліва частина: Календар */}
          <div className="lg:col-span-3">
            {loading ? (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 flex flex-col items-center justify-center">
                <Loader2 className="w-8 h-8 text-primary-400 animate-spin mb-3" />
                <p className="text-sm text-gray-500">Завантаження...</p>
              </div>
            ) : (
              <EmotionCalendar
                month={currentMonth}
                year={currentYear}
                entries={entries}
                selectedDate={selectedDate}
                onSelectDate={handleSelectDate}
                onPrevMonth={handlePrevMonth}
                onNextMonth={handleNextMonth}
              />
            )}

            {/* Статистика місяця */}
            {entries.length > 0 && (
              <div className="mt-4 bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">
                  Статистика за місяць
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-primary-600">{entries.length}</p>
                    <p className="text-xs text-gray-500 mt-1">Записів</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl">
                      {getMostFrequentEmoji(entries) || '—'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">Часта емоція</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-accent-600">
                      {getTopTag(entries) || '—'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">Частий тег</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Права частина: Панель деталей */}
          <div className="lg:col-span-2">
            {panelMode === 'idle' && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
                <div className="text-5xl mb-4">📖</div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">
                  Оберіть день
                </h3>
                <p className="text-sm text-gray-500 leading-relaxed">
                  Натисніть на день у календарі, щоб переглянути або створити запис
                  про свій емоційний стан.
                </p>
              </div>
            )}

            {panelMode === 'view' && currentEntry && (
              <EmotionCard
                entry={currentEntry}
                onEdit={() => setPanelMode('edit')}
                onDelete={handleDelete}
                deleting={deleting}
              />
            )}

            {panelMode === 'create' && selectedDate && (
              <EmotionForm
                date={selectedDate}
                onSave={handleCreate}
                onCancel={() => { setPanelMode('idle'); setSelectedDate(null); }}
                onRequestBotSuggestion={handleRequestBotSuggestion}
                saving={saving}
              />
            )}

            {panelMode === 'edit' && selectedDate && currentEntry && (
              <EmotionForm
                date={selectedDate}
                existingEntry={currentEntry}
                onSave={handleUpdate}
                onCancel={() => setPanelMode('view')}
                onRequestBotSuggestion={handleRequestBotSuggestion}
                saving={saving}
              />
            )}
          </div>
        </div>
      </div>

      {/* Bot Suggestion Modal */}
      {(botSuggestion || botSuggestionLoading) && (
        <BotSuggestionModal
          suggestion={botSuggestion ?? { description: '', emoji: '😐', tags: [] }}
          loading={botSuggestionLoading}
          onSave={handleSaveSuggestion}
          onCancel={clearSuggestion}
        />
      )}
    </div>
  );
}

/* ── Хелпери для статистики ── */

function getMostFrequentEmoji(entries: EmotionEntry[]): string | null {
  const counts = new Map<string, number>();
  for (const e of entries) {
    if (e.emoji) counts.set(e.emoji, (counts.get(e.emoji) ?? 0) + 1);
  }
  let max = 0;
  let result: string | null = null;
  for (const [emoji, count] of counts) {
    if (count > max) { max = count; result = emoji; }
  }
  return result;
}

function getTopTag(entries: EmotionEntry[]): string | null {
  const counts = new Map<string, number>();
  for (const e of entries) {
    if (e.emotion_tags) {
      for (const tag of e.emotion_tags) {
        counts.set(tag, (counts.get(tag) ?? 0) + 1);
      }
    }
  }
  let max = 0;
  let result: string | null = null;
  for (const [tag, count] of counts) {
    if (count > max) { max = count; result = tag; }
  }
  return result;
}

