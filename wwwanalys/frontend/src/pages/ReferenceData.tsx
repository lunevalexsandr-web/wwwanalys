/** Справочники, загруженные из 1С (для проверки): Сорта и Объекты отбора. */
import React, { useEffect, useState } from 'react';
import { Card, CardBody, Table, Spinner, Alert, Form, Row, Col, Badge } from 'react-bootstrap';
import AppHeader from '../components/AppHeader';
import api from '../api/axios';

interface Ref { id: number; name: string; external_id: string | null; is_active?: boolean; }

const RefTable: React.FC<{ title: string; url: string; params?: any }> = ({ title, url, params }) => {
  const [items, setItems] = useState<Ref[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.get(url, { params })
      .then((r) => setItems(r.data || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [url]);

  const filtered = items.filter((i) => i.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <Card className="mb-4">
      <CardBody>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h6 className="mb-0">{title} <Badge bg="secondary">{items.length}</Badge></h6>
          <Form.Control
            size="sm" style={{ maxWidth: 260 }} placeholder="Поиск…"
            value={search} onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {loading ? (
          <div className="text-center py-4"><Spinner animation="border" /></div>
        ) : items.length === 0 ? (
          <Alert variant="info" className="mb-0">Пусто. Загрузите справочник из 1С (вкладка «Интеграция»).</Alert>
        ) : (
          <div style={{ maxHeight: 460, overflowY: 'auto' }}>
            <Table striped hover size="sm">
              <thead><tr><th style={{ width: 60 }}>#</th><th>Наименование</th><th>GUID (1С)</th></tr></thead>
              <tbody>
                {filtered.map((i, idx) => (
                  <tr key={i.id}>
                    <td className="text-muted">{idx + 1}</td>
                    <td>{i.name}</td>
                    <td className="text-muted small font-monospace">{i.external_id || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

const ReferenceData: React.FC = () => {
  return (
    <div className="min-h-screen bg-light">
      <AppHeader showAdminLink showDashboardLink />
      <div className="container-fluid py-4" style={{ maxWidth: 1100 }}>
        <h3 className="mb-1">Справочники из 1С</h3>
        <p className="text-muted">Данные, загруженные по OData. Наполняются на вкладке «Интеграция с 1С».</p>
        <Row>
          <Col md={6}>
            <RefTable title="Сорта" url="/api/varieties" params={{ active_only: true }} />
          </Col>
          <Col md={6}>
            <RefTable title="Объекты отбора" url="/api/analysis-objects" />
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default ReferenceData;
