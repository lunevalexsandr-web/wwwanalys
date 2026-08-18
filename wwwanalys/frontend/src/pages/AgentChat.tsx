/** Чат с агентом-экспертом: вопросы по анализам, отклонениям и рекомендациям. */
import React, { useState, useRef, useEffect } from 'react';
import { Card, CardBody, Form, Button, Spinner } from 'react-bootstrap';
import AppHeader from '../components/AppHeader';
import api from '../api/axios';

type Msg = { role: 'user' | 'assistant'; content: string };

const SUGGESTIONS = [
  'Что у нас произошло за вчерашний день?',
  'Покажи отклонения за последнюю неделю',
  'У нас отклонение по партии ... в показателе ... — что делать?',
];

const AgentChat: React.FC = () => {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  const send = async (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || loading) return;
    const history = messages.slice(-10);
    setMessages((m) => [...m, { role: 'user', content: q }]);
    setInput('');
    setLoading(true);
    try {
      const r = await api.post('/api/ai/chat', { message: q, history });
      setMessages((m) => [...m, { role: 'assistant', content: r.data?.text || '(пустой ответ)' }]);
    } catch (e: any) {
      const detail = e?.response?.data?.detail || 'Ошибка агента';
      setMessages((m) => [...m, { role: 'assistant', content: `⚠️ ${detail}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-light">
      <AppHeader showAdminLink showDashboardLink />
      <div className="container-fluid py-4" style={{ maxWidth: 900 }}>
        <h3 className="mb-3">🤖 Агент-эксперт — чат</h3>

        <Card className="mb-3"><CardBody style={{ minHeight: 340, maxHeight: '60vh', overflowY: 'auto' }}>
          {messages.length === 0 && (
            <div className="text-muted">
              <div className="mb-2">Спросите про анализы, отклонения или что делать с проблемой. Примеры:</div>
              {SUGGESTIONS.map((s, i) => (
                <Button key={i} variant="outline-secondary" size="sm" className="me-2 mb-2"
                        onClick={() => send(s)}>{s}</Button>
              ))}
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`d-flex mb-3 ${m.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}>
              <div
                className={`px-3 py-2 rounded ${m.role === 'user' ? 'bg-primary text-white' : 'bg-white border'}`}
                style={{ maxWidth: '85%', whiteSpace: 'pre-wrap' }}
              >
                {m.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="d-flex justify-content-start mb-2">
              <div className="px-3 py-2 rounded bg-white border text-muted">
                <Spinner size="sm" animation="border" className="me-2" />Агент думает…
              </div>
            </div>
          )}
          <div ref={endRef} />
        </CardBody></Card>

        <Form onSubmit={(e) => { e.preventDefault(); send(); }}>
          <div className="d-flex gap-2">
            <Form.Control
              as="textarea" rows={2}
              placeholder="Ваш вопрос агенту…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
              disabled={loading}
            />
            <Button type="submit" variant="primary" disabled={loading || !input.trim()}>Отправить</Button>
          </div>
          <Form.Text className="text-muted">Enter — отправить, Shift+Enter — новая строка</Form.Text>
        </Form>
      </div>
    </div>
  );
};

export default AgentChat;
