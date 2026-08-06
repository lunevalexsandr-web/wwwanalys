/** База знаний технологических карт (RAG) — загрузка и управление. Только админ. */
import React, { useEffect, useRef, useState } from 'react';
import { Card, CardBody, Button, Form, Table, Alert, Spinner, Badge } from 'react-bootstrap';
import AppHeader from '../components/AppHeader';
import AppToast from '../components/AppToast';
import { useToast } from '../hooks/useToast';
import api from '../api/axios';

interface TechDoc {
  id: number;
  title: string;
  variety: string | null;
  filename: string;
  size_bytes: number | null;
  status: string;
  char_count: number;
  chunk_count: number;
  created_at: string;
}

const ACCEPT = '.pdf,.docx,.xlsx,.txt,.md,.csv';

const TechCards: React.FC = () => {
  const [docs, setDocs] = useState<TechDoc[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [available, setAvailable] = useState(true);
  const [title, setTitle] = useState('');
  const [variety, setVariety] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const { toast, showToast, hideToast } = useToast();

  const loadDocs = async () => {
    setLoading(true);
    try {
      const r = await api.get('/api/ai/tech-cards');
      setDocs(r.data || []);
      setAvailable(true);
    } catch (e: any) {
      // модуль RAG недоступен/выключен — не мешаем, просто показываем сообщение
      if (e?.response?.status === 404) setAvailable(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadDocs(); }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      showToast('Выберите файл', 'warning');
      return;
    }
    const fd = new FormData();
    fd.append('file', file);
    fd.append('title', title);
    fd.append('variety', variety);
    setUploading(true);
    try {
      await api.post('/api/ai/tech-cards/upload', fd, {
        headers: { 'Content-Type': undefined },
      });
      showToast('Файл загружен и проиндексирован', 'success');
      setTitle('');
      setVariety('');
      setFile(null);
      if (fileRef.current) fileRef.current.value = '';
      loadDocs();
    } catch (e: any) {
      showToast(e?.response?.data?.detail || 'Ошибка загрузки', 'danger');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Удалить документ и все его фрагменты?')) return;
    try {
      await api.delete(`/api/ai/tech-cards/${id}`);
      showToast('Документ удалён', 'success');
      loadDocs();
    } catch {
      showToast('Не удалось удалить', 'danger');
    }
  };

  const fmtSize = (b: number | null) =>
    b == null ? '-' : b < 1024 ? `${b} Б` : b < 1048576 ? `${(b / 1024).toFixed(0)} КБ` : `${(b / 1048576).toFixed(1)} МБ`;

  return (
    <div className="min-h-screen bg-light">
      <AppHeader showAdminLink showDashboardLink />
      <div className="container-fluid py-4" style={{ maxWidth: 1100 }}>
        <h3 className="mb-1">База знаний — технологические карты</h3>
        <p className="text-muted">
          Загрузите карты сортов (PDF, DOCX, XLSX, TXT, MD, CSV). Файлы разбираются на
          фрагменты и хранятся в векторной базе для подсказок AI-эксперта при разборе отклонений.
        </p>

        {!available ? (
          <Alert variant="secondary">
            Модуль базы знаний недоступен или выключен на сервере (AI_ENABLED / pgvector).
            На основные функции приложения это не влияет.
          </Alert>
        ) : (
          <>
            <Card className="mb-4">
              <CardBody>
                <h6 className="mb-3">Загрузить карту</h6>
                <Form onSubmit={handleUpload}>
                  <div className="row g-3">
                    <div className="col-md-4">
                      <Form.Label>Файл</Form.Label>
                      <Form.Control
                        ref={fileRef as any}
                        type="file"
                        accept={ACCEPT}
                        onChange={(e: any) => setFile(e.target.files?.[0] || null)}
                        required
                      />
                    </div>
                    <div className="col-md-4">
                      <Form.Label>Название</Form.Label>
                      <Form.Control
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="По умолчанию — имя файла"
                      />
                    </div>
                    <div className="col-md-4">
                      <Form.Label>Сорт</Form.Label>
                      <Form.Control
                        type="text"
                        value={variety}
                        onChange={(e) => setVariety(e.target.value)}
                        placeholder="Например: Жигулёвское"
                      />
                    </div>
                  </div>
                  <div className="mt-3">
                    <Button type="submit" variant="primary" disabled={uploading}>
                      {uploading ? (
                        <><Spinner animation="border" size="sm" className="me-2" />Обработка…</>
                      ) : 'Загрузить'}
                    </Button>
                  </div>
                </Form>
              </CardBody>
            </Card>

            <Card>
              <CardBody>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h6 className="mb-0">Документы</h6>
                  <Button variant="outline-secondary" size="sm" onClick={loadDocs} disabled={loading}>
                    Обновить
                  </Button>
                </div>
                {loading ? (
                  <div className="text-center py-4"><Spinner animation="border" /></div>
                ) : docs.length === 0 ? (
                  <Alert variant="info">Пока нет загруженных карт.</Alert>
                ) : (
                  <Table striped hover size="sm" responsive>
                    <thead>
                      <tr>
                        <th>Название</th>
                        <th>Сорт</th>
                        <th>Файл</th>
                        <th>Размер</th>
                        <th>Фрагментов</th>
                        <th>Загружен</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {docs.map((d) => (
                        <tr key={d.id}>
                          <td>{d.title}</td>
                          <td>{d.variety || <span className="text-muted">—</span>}</td>
                          <td className="text-muted small">{d.filename}</td>
                          <td>{fmtSize(d.size_bytes)}</td>
                          <td><Badge bg="secondary">{d.chunk_count}</Badge></td>
                          <td className="small">{new Date(d.created_at).toLocaleString('ru-RU')}</td>
                          <td>
                            <Button variant="outline-danger" size="sm" onClick={() => handleDelete(d.id)}>
                              Удалить
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                )}
              </CardBody>
            </Card>
          </>
        )}
      </div>
      <AppToast toast={toast} onClose={hideToast} />
    </div>
  );
};

export default TechCards;
