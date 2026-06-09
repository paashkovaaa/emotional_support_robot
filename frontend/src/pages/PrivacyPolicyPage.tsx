import { useState, useEffect } from 'react';
import { ChevronLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';

interface LegalSection {
  heading: string;
  content: string;
}

interface LegalDocument {
  title: string;
  last_updated: string;
  sections: LegalSection[];
}

export default function PrivacyPolicyPage() {
  const navigate = useNavigate();
  const [doc, setDoc] = useState<LegalDocument | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client
      .get('/legal/privacy')
      .then((res) => setDoc(res.data))
      .catch(() => setDoc(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="animate-pulse text-gray-400 text-lg">Завантаження...</div>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
        <p className="text-red-500">Не вдалося завантажити документ</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1 text-indigo-600 hover:text-indigo-800 mb-6 transition"
        >
          <ChevronLeft size={20} />
          Назад
        </button>

        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">{doc.title}</h1>
          <p className="text-sm text-gray-400 mb-8">
            Останнє оновлення: {doc.last_updated}
          </p>

          <div className="space-y-6">
            {doc.sections.map((section, idx) => (
              <div key={idx}>
                <h2 className="text-lg font-semibold text-gray-700 mb-2">
                  {section.heading}
                </h2>
                <p className="text-gray-600 leading-relaxed whitespace-pre-line">
                  {section.content}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer link */}
        <div className="text-center mt-6">
          <button
            onClick={() => navigate('/terms')}
            className="text-indigo-500 hover:text-indigo-700 text-sm underline transition"
          >
            Умови використання →
          </button>
        </div>
      </div>
    </div>
  );
}

