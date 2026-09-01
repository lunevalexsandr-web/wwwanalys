/** План санитарных мероприятий на день: просроченные + плановые по графику. */
import React, { useEffect, useState } from 'react';
import { Card, CardBody, Table, Form, Button, Spinner, Alert, Badge, Row, Col } from 'react-bootstrap';
import AppHeader from '../components/AppHeader';
import api from '../api/axios';

const mskToday = () => {
  // сегодня по МСК (UTC+3)
  const d = new Date(Date.now() + 3 * 3600 * 1000);
  return d.toISOString().slice(0, 10);
};

const SanitationPlan: React.FC = () => {
  const [asOf, setAsOf] = useState(mskToday());
  const [horizon, setHorizon] = useState(0);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    setLoading(true); setErr(null);
    try {
      const r = await api.get('/api/ai/sanitation/plan', { params: { as_of: asOf, horizon_days: horizon } });
      setData(r.data);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'Ошибка загрузки плана');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [asOf, horizon]);

  const overdue = (data?.plan || []).filter((p: any) => p['приоритет'] === 'просрочено');
  const today = (data?.plan || []).filter((p: any) => p['приоритет'] === 'сегодня');

  const table = (rows: any[], badge: string) => (
    <div style={{ maxHeight: 420, overflowY: 'auto' }}>
      <Table size="sm" striped bordered className="mb-0">
        <thead><tr>
          <th>Мероприятие</th><th>Периодичность</th><th>Подразделение</th>
          <th>Последнее</th><th>Срок</th><th>Причина</th>
        </tr></thead>
        <tbody>{rows.map((p: any, i: number) => (
          <tr key={i}>
            <td>{p['мероприятие']}</td>
            <td className="small text-muted">{p['частота'] || '—'}</td>
            <td className="small">{p['подразделение'] || '—'}</td>
            <td className="small">{p['последнее'] || '—'}</td>
            <td className="small">{p['срок'] || '—'}</td>
            <td><Badge bg={badge}>{p['причина']}</Badge></td>
          </tr>
        ))}</tbody>
      </Table>
    </div>
  );

  return (
    <div className="min-h-screen bg-light">
      <AppHeader showAdminLink showDashboardLink />
      <div className="container-fluid py-4" style={{ maxWidth: 1100 }}>
        <h3 className="mb-3">🧼 План санитарных мероприятий</h3>

        <Card className="mb-4"><CardBody>
          <Row className="g-3 align-items-end">
            <Col md={3}>
              <Form.Label className="small text-muted mb-1">Дата (МСК)</Form.Label>
              <Form.Control type="date" value={asOf} onChange={(e) => setAsOf(e.target.value)} />
            </Col>
            <Col md={3}>
              <Form.Label className="small text-muted mb-1">Горизонт плановых</Form.Label>
              <Form.Select value={horizon} onChange={(e) => setHorizon(Number(e.target.value))}>
                <option value={0}>только сегодня</option>
                <option value={3}>+3 дня</option>
                <option value={7}>+7 дней</option>
                <option value={14}>+14 дней</option>
              </Form.Select>
            </Col>
            <Col md="auto">
              <Button variant="primary" onClick={load} disabled={loading}>
                {loading ? <><Spinner size="sm" animation="border" className="me-2" />Загрузка…</> : '🔄 Обновить'}
              </Button>
            </Col>
            <Col md="auto">
              <Button variant="outline-secondary" onClick={() => setAsOf(mskToday())} disabled={loading}>Сегодня</Button>
            </Col>
          </Row>
        </CardBody></Card>

        {err && <Alert variant="danger">{err}</Alert>}

        {loading ? <div className="text-center py-5"><Spinner animation="border" variant="primary" /></div> : data && (
          <>
            <Row className="g-3 mb-4">
              {[['Всего в плане', data.total, 'primary'], ['Просрочено', data.overdue_count, data.overdue_count ? 'danger' : 'success'],
                ['Плановых (в норме)', data.planned_count, 'secondary'], ['Событийных', data.event_based_count, 'info']].map(([l, v, c]: any, i) => (
                <Col key={i}><Card className="text-center"><CardBody>
                  <div className="h3 mb-0"><Badge bg={c}>{v}</Badge></div>
                  <small className="text-muted">{l}</small>
                </CardBody></Card></Col>
              ))}
            </Row>

            <Card className="mb-4 border-danger"><CardBody>
              <h6 className="text-danger">🔴 Сделать в первую очередь — просрочено <Badge bg="danger">{overdue.length}</Badge></h6>
              {overdue.length ? table(overdue, 'danger') : <div className="text-muted small">Просроченных нет ✅</div>}
            </CardBody></Card>

            <Card className="mb-4"><CardBody>
              <h6 className="text-primary">📅 По графику {horizon > 0 ? `(сегодня и +${horizon} дн)` : 'на сегодня'} <Badge bg="primary">{today.length}</Badge></h6>
              {today.length ? table(today, 'primary') : <div className="text-muted small">На выбранный период плановых нет.</div>}
            </CardBody></Card>

            <div className="text-muted small">
              Событийные мероприятия («каждый CIP», «каждые N часов работы») в план по календарю не включаются.
              План строится по периодичности из справочника и дате последнего фактического выполнения.
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SanitationPlan;
