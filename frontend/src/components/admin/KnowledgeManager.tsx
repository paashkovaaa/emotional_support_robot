import { useEffect, useRef, useState } from 'react';
import {
  Upload, Trash2, RefreshCw, FileText, BookOpen, AlertCircle,
  CheckCircle2, Loader2, FolderOpen, X,
} from 'lucide-react';
import toast from 'react-hot-toast';
import * as adminApi from '../../api/admin';
import type { KnowledgeDocument } from '../../api/admin';

const CATEGORY_LABELS: Record<string, string> = {
  cbt: 'КПТ', act: 'ACT', dbt: 'ДПТ', crisis: 'Криза',
  self_help: 'Самодопомога', article: 'Стаття', book: 'Книга', other: 'Інше',
};

const STATUS_CONFIG: Record<KnowledgeDocument['status'], { label: string; color: string; icon: React.ReactNode }> = {
  active:     { label: 'Активний',  color: 'text-green-600 bg-green-50',  icon: <CheckCircle2 className="w-3.5 h-3.5" /> },
  processing: { label: 'Обробка…',  color: 'text-amber-600 bg-amber-50',  icon: <Loader2 className="w-3.5 h-3.5 animate-spin" /> },
  archived:   { label: 'Архів',     color: 'text-gray-500 bg-gray-50',    icon: <FileText className="w-3.5 h-3.5" /> },
  error:      { label: 'Помилка',   color: 'text-red-600 bg-red-50',      icon: <AlertCircle className="w-3.5 h-3.5" /> },
};

export default function KnowledgeManager() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [reprocessingId, setReprocessingId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [formTitle, setFormTitle] = useState('');
  const [formCategory, setFormCategory] = useState('other');
  const [formSource, setFormSource] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval>>();

  const fetchDocuments = async () => {
    try {
      const data = await adminApi.getKnowledgeDocuments();
      setDocuments(data.documents);
      setTotal(data.total);
    } catch { /* silent */ } finally { setLoading(false); }
  };

  useEffect(() => { fetchDocuments(); }, []);

  useEffect(() => {
    const hasProcessing = documents.some((d) => d.status === 'processing');
    if (hasProcessing) { pollRef.current = setInterval(fetchDocuments, 5000); }
    return () => clearInterval(pollRef.current);
  }, [documents]);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    if (!formTitle) setFormTitle(file.name.replace(/\.[^.]+$/, ''));
    setShowForm(true);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleUpload = async () => {
    if (!selectedFile || !formTitle.trim()) { toast.error('Виберіть файл та вкажіть назву'); return; }
    setUploading(true); setUploadProgress(0);
    try {
      const result = await adminApi.uploadKnowledgeDocument(
        selectedFile, formTitle.trim(), formCategory,
        formSource.trim() || undefined, setUploadProgress,
      );
      toast.success(result.message);
      cancelUpload(); await fetchDocuments();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Помилка завантаження');
    } finally { setUploading(false); setUploadProgress(0); }
  };

  const cancelUpload = () => {
    setShowForm(false); setSelectedFile(null);
    setFormTitle(''); setFormCategory('other'); setFormSource('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDelete = async (doc: KnowledgeDocument) => {
    if (!confirm(`Видалити «${doc.title}»?\nЦе також видалить всі ембедінги документа.`)) return;
    setDeletingId(doc.id);
    try { await adminApi.deleteKnowledgeDocument(doc.id); toast.success(`«${doc.title}» видалено`); await fetchDocuments(); }
    catch { toast.error('Помилка видалення'); }
    finally { setDeletingId(null); }
  };

  const handleReprocess = async (doc: KnowledgeDocument) => {
    setReprocessingId(doc.id);
    try { const r = await adminApi.reprocessKnowledgeDocument(doc.id); toast.success(r.message); await fetchDocuments(); }
    catch { toast.error('Помилка переобробки'); }
    finally { setReprocessingId(null); }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-primary-500" />
          База знань
          {total > 0 && <span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{total} докум.</span>}
        </h3>
        <button onClick={() => { setShowForm(!showForm); if (!showForm) setSelectedFile(null); }}
          className="px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors">
          <Upload className="w-3.5 h-3.5" /> Завантажити
        </button>
      </div>

      {/* Upload form */}
      {showForm && (
        <div className="mb-5 border border-primary-100 bg-primary-50/30 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-gray-600">Новий документ</span>
            <button onClick={cancelUpload} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
          </div>

          {/* Drop zone */}
          <div onDrop={handleDrop} onDragOver={(e) => e.preventDefault()}
            onClick={() => !selectedFile && fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-4 text-center mb-3 transition-colors cursor-pointer ${selectedFile ? 'border-primary-300 bg-primary-50' : 'border-gray-200 hover:border-primary-300 hover:bg-primary-50/50'}`}>
            <input ref={fileInputRef} type="file" accept=".pdf,.txt,.docx,.doc" className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }} />
            {selectedFile ? (
              <div className="flex items-center justify-center gap-2 text-primary-600">
                <FileText className="w-4 h-4" />
                <span className="text-xs font-medium">{selectedFile.name}</span>
                <span className="text-xs text-gray-400">({(selectedFile.size / 1024 / 1024).toFixed(1)} МБ)</span>
                <button onClick={(e) => { e.stopPropagation(); setSelectedFile(null); if (fileInputRef.current) fileInputRef.current.value = ''; }}
                  className="ml-1 text-gray-400 hover:text-red-500"><X className="w-3.5 h-3.5" /></button>
              </div>
            ) : (
              <div className="text-gray-400">
                <Upload className="w-6 h-6 mx-auto mb-1" />
                <p className="text-xs">Перетягніть файл або натисніть</p>
                <p className="text-[10px] mt-0.5">PDF, TXT, DOCX (до 50 МБ)</p>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <input type="text" placeholder="Назва документа *" value={formTitle} onChange={(e) => setFormTitle(e.target.value)}
              className="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary-400" />
            <div className="flex gap-2">
              <select value={formCategory} onChange={(e) => setFormCategory(e.target.value)}
                className="flex-1 text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary-400 bg-white">
                {Object.entries(CATEGORY_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
              <input type="text" placeholder="Джерело / автор" value={formSource} onChange={(e) => setFormSource(e.target.value)}
                className="flex-1 text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary-400" />
            </div>
          </div>

          {uploading && (
            <div className="mt-3">
              <div className="flex justify-between text-[10px] text-gray-500 mb-1"><span>Завантаження...</span><span>{uploadProgress}%</span></div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-primary-500 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
              </div>
            </div>
          )}

          <button onClick={handleUpload} disabled={uploading || !selectedFile || !formTitle.trim()}
            className="mt-3 w-full py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
            {uploading ? <><Loader2 className="w-3.5 h-3.5 animate-spin" />Завантаження...</> : <><Upload className="w-3.5 h-3.5" />Завантажити та обробити</>}
          </button>
        </div>
      )}

      {/* List */}
      {loading ? (
        <div className="flex items-center justify-center py-8"><Loader2 className="w-6 h-6 text-primary-400 animate-spin" /></div>
      ) : documents.length === 0 ? (
        <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center">
          <FolderOpen className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-400 mb-1">База знань порожня</p>
          <p className="text-xs text-gray-400">Завантажте PDF-книги або статті з психології для покращення відповідей бота</p>
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => {
            const st = STATUS_CONFIG[doc.status];
            return (
              <div key={doc.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors group">
                <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center border border-gray-200 flex-shrink-0">
                  <FileText className="w-4 h-4 text-gray-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-700 truncate">{doc.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] text-gray-400">{CATEGORY_LABELS[doc.category] || doc.category}</span>
                    {doc.chunk_count != null && doc.chunk_count > 0 && <span className="text-[10px] text-gray-400">• {doc.chunk_count} фрагм.</span>}
                  </div>
                </div>
                <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium flex-shrink-0 ${st.color}`}>
                  {st.icon}{st.label}
                </span>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                  {doc.status === 'error' && (
                    <button onClick={() => handleReprocess(doc)} disabled={reprocessingId === doc.id} title="Переобробити"
                      className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-amber-100 text-amber-500 disabled:opacity-50">
                      {reprocessingId === doc.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                    </button>
                  )}
                  <button onClick={() => handleDelete(doc)} disabled={deletingId === doc.id} title="Видалити"
                    className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-red-100 text-red-400 disabled:opacity-50">
                    {deletingId === doc.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {documents.length > 0 && (
        <button onClick={fetchDocuments}
          className="mt-3 w-full text-xs text-gray-400 hover:text-gray-600 flex items-center justify-center gap-1.5 py-1.5 hover:bg-gray-50 rounded-xl transition-colors">
          <RefreshCw className="w-3 h-3" /> Оновити список
        </button>
      )}
    </div>
  );
}
