/** Справочники, загруженные из 1С: Сорта, Объекты отбора, Санитарные мероприятия. */
import React, { useEffect, useState } from 'react';
import { Table, Spinner, Alert, Form, Badge, Tabs, Tab, InputGroup } from 'react-bootstrap';
import AppHeader from '../components/AppHeader';
import api from '../api/axios';
import Admin from './Admin';

interface Ref { id: number; name: string; external_id: string | null; }

const SearchBar: React.FC<{ value: string; onChange: (v: string) => void; placeholder?: string }> = ({ value, onChange, placeholder }) => (
  <InputGroup size="sm" style={{ maxWidth: 320 }}>
    <InputGroup.Text className="bg-white text-muted">🔍</InputGroup.Text>
    <Form.Control placeholder={placeholder || 'Поиск по названию…'} value={value} onChange={(e) => onChange(e.target.value)} />
    {value && (
      <InputGroup.Text role="button" className="bg-white text-muted" onClick={() => onChange('')}>✕</InputGroup.Text>
    )}
  </InputGroup>
);

const emptyBox = (text: string) => (
  <div className="text-center text-muted py-5">
    <div style={{ fontSize: 32, opacity: 0.4 }}>📭</div>
    <div className="mt-2">{text}</div>
  </div>
);

/** Простой справочник: наименование + GUID. */
const SimpleRef: React.FC<{ url: string; params?: any }> = ({ url, params }) => {
  const [items, setItems] = useState<Ref[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    api.get(url, { params }).then((r) => setItems(r.data || [])).catch(() => setItems([])).finally(() => setLoading(false));
  }, [url]);

  const filtered = items.filter((i) => (i.name || '').toLowerCase().includes(search.toLowerCase()));

  if (loading) return <div className="text-center py-5"><Spinner animation="border" variant="primary" /></div>;
  if (items.length === 0) return emptyBox('Пусто. Загрузите справочник из 1С (Админ → «Интеграция с 1С»).');

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <span className="text-muted small">Найдено: <strong>{filtered.length}</strong> из {items.length}</span>
        <SearchBar value={search} onChange={setSearch} />
      </div>
      <div className="border rounded" style={{ maxHeight: '62vh', overflowY: 'auto' }}>
        <Table hover size="sm" className="mb-0 align-middle">
          <thead className="table-light" style={{ position: 'sticky', top: 0, zIndex: 1 }}>
            <tr><th style={{ width: 56 }} className="text-muted">#</th><th>Наименование</th><th className="text-muted">GUID (1С)</th></tr>
          </thead>
          <tbody>
            {filtered.map((i, idx) => (
              <tr key={i.id}>
                <td className="text-muted">{idx + 1}</td>
                <td className="fw-medium">{i.name}</td>
                <td><code className="small text-muted">{i.external_id || '—'}</code></td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </>
  );
};

/** Санитарные мероприятия с частотой. */
const SanitationMeasures: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.get('/api/external/1c/sanitation-measures').then((r) => setItems(r.data || [])).catch(() => setItems([])).finally(() => setLoading(false));
  }, []);

  const filtered = items.filter((i) => (i.name || '').toLowerCase().includes(search.toLowerCase()));

  if (loading) return <div className="text-center py-5"><Spinner animation="border" variant="primary" /></div>;
  if (items.length === 0) return emptyBox('Пусто. Загрузите санитарию из 1С (Админ → «Интеграция с 1С»).');

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <span className="text-muted small">Найдено: <strong>{filtered.length}</strong> из {items.length}</span>
        <SearchBar value={search} onChange={setSearch} placeholder="Поиск по мероприятию…" />
      </div>
      <div className="border rounded" style={{ maxHeight: '62vh', overflowY: 'auto' }}>
        <Table hover size="sm" className="mb-0 align-middle">
          <thead className="table-light" style={{ position: 'sticky', top: 0, zIndex: 1 }}>
            <tr>
              <th style={{ width: 56 }} className="text-muted">#</th>
              <th>Мероприятие</th>
              <th style={{ width: 170 }}>Частота</th>
              <th style={{ width: 90 }} className="text-end">Интервал</th>
              <th style={{ width: 90 }} className="text-end">Длит.</th>
              <th>Подразделение</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((i, idx) => (
              <tr key={idx}>
                <td className="text-muted">{idx + 1}</td>
                <td className="fw-medium">{i.name}</td>
                <td>{i.frequency ? <Badge bg="info" className="fw-normal">{i.frequency}</Badge> : <span className="text-muted">—</span>}</td>
                <td className="text-end text-muted small">{i.interval_hours ? `${i.interval_hours} ч` : '—'}</td>
                <td className="text-end text-muted small">{i.duration_min ? `${i.duration_min} мин` : '—'}</td>
                <td className="small">{i.department || '—'}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </>
  );
};

const ReferenceData: React.FC = () => {
  return (
    <div className="min-h-screen bg-light">
      <AppHeader showAdminLink showDashboardLink />
      <div className="container-fluid py-4" style={{ maxWidth: 1150 }}>
        <div className="mb-4">
          <h3 className="mb-1 d-flex align-items-center gap-2">📚 Справочники</h3>
          <p className="text-muted mb-0">Данные, загруженные из 1С по OData. Наполняются на вкладке «Интеграция с 1С» в админ-панели.</p>
        </div>

        <div className="bg-white border rounded-3 shadow-sm p-3 p-md-4">
          <Tabs defaultActiveKey="varieties" className="mb-3" mountOnEnter unmountOnExit>
            <Tab eventKey="templates" title={<span>📋 Шаблоны</span>}>
              <div className="pt-2"><Admin mode="templates" embedded /></div>
            </Tab>
            <Tab eventKey="library" title={<span>📈 Показатели</span>}>
              <div className="pt-2"><Admin mode="library" embedded /></div>
            </Tab>
            <Tab eventKey="varieties" title={<span>🍺 Сорта</span>}>
              <div className="pt-3"><SimpleRef url="/api/varieties" params={{ active_only: true }} /></div>
            </Tab>
            <Tab eventKey="objects" title={<span>🎯 Объекты отбора</span>}>
              <div className="pt-3"><SimpleRef url="/api/analysis-objects" /></div>
            </Tab>
            <Tab eventKey="sanitation" title={<span>🧼 Санитарные мероприятия</span>}>
              <div className="pt-3"><SanitationMeasures /></div>
            </Tab>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default ReferenceData;
