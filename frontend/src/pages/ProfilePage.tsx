import { useState, useEffect } from 'react';
import {
  Mail,
  Calendar,
  Shield,
  Pencil,
  Save,
  X,
  Trash2,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuthStore } from '../stores/authStore';
import { changePassword } from '../api/auth';
import { formatDateLong } from '../utils/formatters';
import type { ProfileUpdate, CommunicationStyle, Gender } from '../types';

const COMMUNICATION_STYLES: { value: CommunicationStyle; label: string; emoji: string; description: string }[] = [
  {
    value: 'friendly',
    label: 'Дружній',
    emoji: '🤗',
    description: 'Тепле, неформальне спілкування',
  },
  {
    value: 'balanced',
    label: 'Збалансований',
    emoji: '⚖️',
    description: 'Поєднання теплоти та структурованості',
  },
  {
    value: 'analytical',
    label: 'Аналітичний',
    emoji: '🧠',
    description: 'Структурований, конкретний підхід',
  },
];

const GENDERS: { value: Gender; label: string }[] = [
  { value: 'male', label: 'Чоловік' },
  { value: 'female', label: 'Жінка' },
  { value: 'other', label: 'Інше' },
  { value: 'prefer_not_to_say', label: 'Не хочу вказувати' },
];

export default function ProfilePage() {
  const { user, profile, updateProfile, deleteAccount } = useAuthStore();

  // Profile editing
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<ProfileUpdate>({});

  // Password change
  const [showPasswordSection, setShowPasswordSection] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ oldPassword: '', newPassword: '', confirmPassword: '' });
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  // Delete account
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  // Initialize form when editing starts
  useEffect(() => {
    if (editing && profile) {
      setForm({
        nickname: profile.nickname,
        age: profile.age,
        gender: profile.gender,
        communication_style: profile.communication_style,
        life_area: profile.life_area,
        concern: profile.concern,
        works_with_psychologist: profile.works_with_psychologist,
      });
    }
  }, [editing, profile]);

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      await updateProfile(form);
      toast.success('Профіль оновлено');
      setEditing(false);
    } catch {
      toast.error('Не вдалося зберегти зміни');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      toast.error('Паролі не співпадають');
      return;
    }
    if (passwordForm.newPassword.length < 8) {
      toast.error('Пароль має бути не менше 8 символів');
      return;
    }
    setPasswordSaving(true);
    try {
      await changePassword(passwordForm.oldPassword, passwordForm.newPassword);
      toast.success('Пароль змінено');
      setShowPasswordSection(false);
      setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' });
    } catch {
      toast.error('Не вдалося змінити пароль. Перевірте поточний пароль.');
    } finally {
      setPasswordSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== 'ВИДАЛИТИ') {
      toast.error('Введіть "ВИДАЛИТИ" для підтвердження');
      return;
    }
    try {
      await deleteAccount();
      toast.success('Акаунт видалено');
      // authStore will redirect to login
    } catch {
      toast.error('Не вдалося видалити акаунт');
    }
  };

  if (!user || !profile) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-2xl mx-auto px-4 lg:px-6 py-6 space-y-6">

        {/* ── User Card ── */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-primary-100 flex items-center justify-center">
                <span className="text-2xl font-bold text-primary-700">
                  {(profile.nickname?.[0] || '?').toUpperCase()}
                </span>
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-800">{profile.nickname}</h2>
                <div className="flex items-center gap-1.5 mt-1 text-sm text-gray-500">
                  <Mail className="w-3.5 h-3.5" />
                  {user.email}
                </div>
                <div className="flex items-center gap-1.5 mt-0.5 text-xs text-gray-400">
                  <Calendar className="w-3 h-3" />
                  Зареєстровано {formatDateLong(user.created_at)}
                </div>
              </div>
            </div>
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-primary-600
                           hover:bg-primary-50 rounded-lg transition-colors"
              >
                <Pencil className="w-3.5 h-3.5" />
                Редагувати
              </button>
            )}
          </div>

          {user.role === 'admin' && (
            <div className="mt-3 flex items-center gap-1.5 text-xs text-purple-600 bg-purple-50 px-2.5 py-1 rounded-lg w-fit">
              <Shield className="w-3 h-3" />
              Адміністратор
            </div>
          )}
        </div>

        {/* ── Profile Details / Edit Form ── */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            {editing ? 'Редагування профілю' : 'Деталі профілю'}
          </h3>

          {editing ? (
            <div className="space-y-4">
              {/* Nickname */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Нікнейм</label>
                <input
                  type="text"
                  value={form.nickname || ''}
                  onChange={(e) => setForm({ ...form, nickname: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm
                             focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400"
                  placeholder="Ваш нікнейм"
                />
              </div>

              {/* Age */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Вік</label>
                <input
                  type="number"
                  value={form.age ?? ''}
                  onChange={(e) => setForm({ ...form, age: e.target.value ? Number(e.target.value) : null })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm
                             focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400"
                  placeholder="Ваш вік"
                  min={1}
                  max={120}
                />
              </div>

              {/* Gender */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Стать</label>
                <select
                  value={form.gender || ''}
                  onChange={(e) => setForm({ ...form, gender: (e.target.value || null) as Gender | null })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm bg-white
                             focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400"
                >
                  <option value="">Не вказано</option>
                  {GENDERS.map((g) => (
                    <option key={g.value} value={g.value}>{g.label}</option>
                  ))}
                </select>
              </div>

              {/* Communication style */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-2">Стиль спілкування</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {COMMUNICATION_STYLES.map((style) => (
                    <button
                      key={style.value}
                      type="button"
                      onClick={() => setForm({ ...form, communication_style: style.value })}
                      className={`p-3 rounded-xl border text-left transition-all
                        ${form.communication_style === style.value
                          ? 'border-primary-400 bg-primary-50 ring-2 ring-primary-500/20'
                          : 'border-gray-200 hover:border-gray-300'
                        }`}
                    >
                      <span className="text-lg">{style.emoji}</span>
                      <p className="text-sm font-medium text-gray-700 mt-1">{style.label}</p>
                      <p className="text-[11px] text-gray-500">{style.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Life area */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Сфера життя</label>
                <input
                  type="text"
                  value={form.life_area || ''}
                  onChange={(e) => setForm({ ...form, life_area: e.target.value || null })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm
                             focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400"
                  placeholder="Наприклад: робота, навчання, стосунки"
                />
              </div>

              {/* Concern */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Що турбує</label>
                <textarea
                  value={form.concern || ''}
                  onChange={(e) => setForm({ ...form, concern: e.target.value || null })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm resize-none
                             focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400"
                  placeholder="Опишіть коротко, що вас турбує"
                  rows={3}
                />
              </div>

              {/* Works with psychologist */}
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.works_with_psychologist ?? false}
                  onChange={(e) => setForm({ ...form, works_with_psychologist: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">Працюю з психологом</span>
              </label>

              {/* Actions */}
              <div className="flex items-center gap-2 pt-2">
                <button
                  onClick={handleSaveProfile}
                  disabled={saving}
                  className="flex items-center gap-1.5 px-4 py-2 bg-primary-600 hover:bg-primary-700
                             text-white font-medium rounded-xl text-sm transition-colors disabled:opacity-50"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Зберегти
                </button>
                <button
                  onClick={() => setEditing(false)}
                  className="flex items-center gap-1.5 px-4 py-2 bg-gray-100 hover:bg-gray-200
                             text-gray-700 font-medium rounded-xl text-sm transition-colors"
                >
                  <X className="w-4 h-4" />
                  Скасувати
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <InfoRow label="Нікнейм" value={profile.nickname} />
              <InfoRow label="Вік" value={profile.age ? `${profile.age} років` : 'Не вказано'} />
              <InfoRow
                label="Стать"
                value={GENDERS.find((g) => g.value === profile.gender)?.label || 'Не вказано'}
              />
              <InfoRow
                label="Стиль спілкування"
                value={
                  COMMUNICATION_STYLES.find((s) => s.value === profile.communication_style)
                    ? `${COMMUNICATION_STYLES.find((s) => s.value === profile.communication_style)!.emoji} ${COMMUNICATION_STYLES.find((s) => s.value === profile.communication_style)!.label}`
                    : 'Не вказано'
                }
              />
              <InfoRow label="Сфера життя" value={profile.life_area || 'Не вказано'} />
              <InfoRow label="Що турбує" value={profile.concern || 'Не вказано'} />
              <InfoRow
                label="Працює з психологом"
                value={profile.works_with_psychologist ? 'Так' : 'Ні'}
              />
              {profile.survey_completed && (
                <div className="flex items-center gap-1.5 text-xs text-green-600 bg-green-50 px-2.5 py-1.5 rounded-lg w-fit mt-2">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Опитування завершено
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Change Password ── */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <Lock className="w-4 h-4 text-gray-400" />
              Безпека
            </h3>
            {!showPasswordSection && (
              <button
                onClick={() => setShowPasswordSection(true)}
                className="text-xs text-primary-600 hover:text-primary-700 font-medium"
              >
                Змінити пароль
              </button>
            )}
          </div>

          {showPasswordSection && (
            <div className="space-y-3">
              {/* Old password */}
              <div className="relative">
                <label className="block text-xs font-medium text-gray-500 mb-1">Поточний пароль</label>
                <div className="relative">
                  <input
                    type={showOldPassword ? 'text' : 'password'}
                    value={passwordForm.oldPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, oldPassword: e.target.value })}
                    className="w-full px-3 py-2 pr-10 border border-gray-200 rounded-xl text-sm
                               focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400"
                  />
                  <button
                    type="button"
                    onClick={() => setShowOldPassword(!showOldPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showOldPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* New password */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Новий пароль</label>
                <div className="relative">
                  <input
                    type={showNewPassword ? 'text' : 'password'}
                    value={passwordForm.newPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                    className="w-full px-3 py-2 pr-10 border border-gray-200 rounded-xl text-sm
                               focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm password */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Підтвердити пароль</label>
                <input
                  type="password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm
                             focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <button
                  onClick={handleChangePassword}
                  disabled={passwordSaving}
                  className="flex items-center gap-1.5 px-4 py-2 bg-primary-600 hover:bg-primary-700
                             text-white font-medium rounded-xl text-sm transition-colors disabled:opacity-50"
                >
                  {passwordSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                  Змінити
                </button>
                <button
                  onClick={() => {
                    setShowPasswordSection(false);
                    setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' });
                  }}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700
                             font-medium rounded-xl text-sm transition-colors"
                >
                  Скасувати
                </button>
              </div>
            </div>
          )}

          {!showPasswordSection && (
            <p className="text-xs text-gray-400">
              Регулярно змінюйте пароль для захисту вашого акаунту
            </p>
          )}
        </div>

        {/* ── Danger Zone ── */}
        <div className="bg-white rounded-2xl shadow-sm border border-red-100 p-6">
          <h3 className="text-sm font-semibold text-red-600 flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4" />
            Небезпечна зона
          </h3>
          <p className="text-xs text-gray-500 mb-4">
            Видалення акаунту є незворотною дією. Всі ваші дані, розмови та записи в щоденнику будуть видалені назавжди.
          </p>

          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="flex items-center gap-1.5 px-4 py-2 border border-red-200 text-red-600
                         hover:bg-red-50 font-medium rounded-xl text-sm transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              Видалити акаунт
            </button>
          ) : (
            <div className="space-y-3 bg-red-50 rounded-xl p-4 border border-red-200">
              <p className="text-sm text-red-700 font-medium">
                Ви впевнені? Введіть «ВИДАЛИТИ» для підтвердження:
              </p>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="ВИДАЛИТИ"
                className="w-full px-3 py-2 border border-red-300 rounded-xl text-sm
                           focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-400"
              />
              <div className="flex items-center gap-2">
                <button
                  onClick={handleDeleteAccount}
                  disabled={deleteConfirmText !== 'ВИДАЛИТИ'}
                  className="flex items-center gap-1.5 px-4 py-2 bg-red-600 hover:bg-red-700
                             text-white font-medium rounded-xl text-sm transition-colors disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                  Підтвердити видалення
                </button>
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setDeleteConfirmText('');
                  }}
                  className="px-4 py-2 bg-white hover:bg-gray-50 text-gray-700 border border-gray-200
                             font-medium rounded-xl text-sm transition-colors"
                >
                  Скасувати
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/** Small helper component for info rows */
function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between py-2 border-b border-gray-50 last:border-b-0">
      <span className="text-xs font-medium text-gray-400">{label}</span>
      <span className="text-sm text-gray-700 text-right max-w-[60%]">{value}</span>
    </div>
  );
}

