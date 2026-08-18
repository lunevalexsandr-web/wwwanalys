/** Аналитика по отчётам: отклонения/в норме, по дням, топ показателей + разбор ИИ. */
import React, { useEffect, useState } from 'react';
import { Card, CardBody, Row, Col, Table, Form, Button, Spinner, Alert, Badge } from 'react-bootstrap';
import AppHeader from '../components/AppHeader';
import api from '../api/axios';

const fmtDate = (d: Date) => d.toISOString().slice(0, 10);

const ReportsAnalytics: React.FC = () => {
  const today = new Date();
  const weekAgo = new Date(); weekAgo.setDate(today.getDate() - 7);
  const [dateFrom, setDateFrom] = useState(fmtDate(weekAgo));
  const [dateTo, setDateTo] = useState(fmtDate(today));
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [aiText, setAiText] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiMsg, setAiMsg] = useState<string | null>(null);

  const load = async () => {
    setLoading(true); setAiText(null); setAiMsg(null);
    try {
      const r = await api.get('/api/ai/analytics/summary', { params: { date_from: dateFrom || undefined, date_to: dateTo || undefined } });
      setData(r.data);
    } catch (e: any) {
      setData(null); setAiMsg(e?.response?.data?.detail || 'Ошибка загрузки аналитики');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const runAi = async () => {
    setAiLoading(true); setAiText(null); setAiMsg(null);
    try {
      const r = await api.post('/api/ai/analytics/analyze', null, { params: { date_from: dateFrom || undefined, date_to: dateTo || undefined } });
      const txt = r.data?.summary || r.data?.report_text;
      if (txt) setAiText(txt);
      else setAiMsg('Разбор пуст. Проверьте подключение модели.');
    } catch (e: any) {
      setAiMsg(e?.response?.data?.detail || 'Ошибка разбора ИИ');
    } finally { setAiLoading(false); }
  };

  const kpi = (label: string, value: any, variant = 'secondary') => (
    <Col><Card className="text-center"><CardBody>
      <div className="h3 mb-0"><Badge bg={variant}>{value}</Badge></div>
      <small className="text-muted">{label}</small>
    </CardBody></Card></Col>
  );

  return (
    <div className="min-h-screen bg-light">
      <AppHeader showAdminLink showDashboardLink />
      <div className="container-fluid py-4" style={{ maxWidth: 1150 }}>
        <h3 className="mb-3">Аналитика по анализам</h3>

        <Card className="mb-4"><CardBody>
          <Row className="g-2 align-items-end">
            <Col md={3}>
              <Form.Label>С даты</Form.Label>
              <Form.Control type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            </Col>
            <Col md={3}>
              <Form.Label>По дату</Form.Label>
              <Form.Control type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            </Col>
            <Col md="auto">
              <Button variant="primary" onClick={load} disabled={loading}>
                {loading ? <Spinner size="sm" animation="border" /> : 'Показать'}
              </Button>
            </Col>
            <Col md="auto">
              <Button variant="outline-primary" onClick={runAi} disabled={aiLoading || !data}>
                {aiLoading ? <><Spinner size="sm" animation="border" className="me-2" />Разбор…</> : '🍺 Разбор ИИ-эксперта'}
              </Button>
            </Col>
          </Row>
        </CardBody></Card>

        {aiMsg && <Alert variant="info">{aiMsg}</Alert>}

        {data && (
          <>
            <Row className="g-3 mb-4">
              {kpi('Отчётов', data.reports_count, 'primary')}
              {kpi('Отчётов с отклонением', data.reports_with_deviations ?? '—', 'danger')}
              {kpi('Отчётов в норме', data.reports_normal ?? '—', 'success')}
              {kpi('Показателей', data.values_count, 'secondary')}
              {kpi('Отклонений', data.deviations_count, 'danger')}
              {kpi('Доля отклонений', `${data.deviation_rate}%`, 'warning')}
            </Row>

            {aiText && (
              <Card className="mb-4 border-primary"><CardBody>
                <h6 className="mb-2">🍺 Разбор ИИ-эксперта</h6>
                <div style={{ whiteSpace: 'pre-wrap' }}>{aiText}</div>
              </CardBody></Card>
            )}

            <Row>
              <Col md={4}>
                <Card className="mb-4"><CardBody>
                  <h6>По дням</h6>
                  <Table size="sm" striped>
                    <thead><tr><th>Дата</th><th>Показателей</th><th>Откл.</th></tr></thead>
                    <tbody>{(data.by_day || []).map((d: any) => (
                      <tr key={d.day}><td>{d.day}</td><td>{d.values}</td><td>{d.deviations ? <Badge bg="danger">{d.deviations}</Badge> : 0}</td></tr>
                    ))}</tbody>
                  </Table>
                </CardBody></Card>
              </Col>
              <Col md={4}>
                <Card className="mb-4"><CardBody>
                  <h6>Топ показателей по отклонениям</h6>
                  <Table size="sm" striped>
                    <thead><tr><th>Показатель</th><th>Откл.</th></tr></thead>
                    <tbody>{(data.top_indicators || []).map((d: any, i: number) => (
                      <tr key={i}><td>{d.indicator}</td><td>{d.deviations}</td></tr>
                    ))}</tbody>
                  </Table>
                </CardBody></Card>
              </Col>
              <Col md={4}>
                <Card className="mb-4"><CardBody>
                  <h6>По шаблонам</h6>
                  <Table size="sm" striped>
                    <thead><tr><th>Шаблон</th><th>Откл.</th></tr></thead>
                    <tbody>{(data.by_template || []).map((d: any, i: number) => (
                      <tr key={i}><td>{d.template}</td><td>{d.deviations}</td></tr>
                    ))}</tbody>
                  </Table>
                </CardBody></Card>
              </Col>
            </Row>

            <Card><CardBody>
              <h6>Отклонения ({(data.deviations || []).length})</h6>
              <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                <Table size="sm" striped bordered>
                  <thead style={{ position: 'sticky', top: 0 }}><tr>
                    <th>Партия</th><th>Шаблон</th><th>Сорт</th><th>День</th><th>Показатель</th><th>Значение</th><th>Норма</th>
                  </tr></thead>
                  <tbody>{(data.deviations || []).map((d: any, i: number) => (
                    <tr key={i}>
                      <td>{d.batch_number}</td><td>{d.template}</td><td>{d.variety || '—'}</td>
                      <td>{d.day ?? '—'}</td><td>{d.indicator}{d.unit ? `, ${d.unit}` : ''}</td>
                      <td><strong>{d.value}</strong></td>
                      <td>{(d.min_value != null || d.max_value != null) ? `${d.min_value ?? '?'} – ${d.max_value ?? '?'}` : (d.norm_text || '—')}</td>
                    </tr>
                  ))}</tbody>
                </Table>
              </div>
            </CardBody></Card>
          </>
        )}
      </div>
    </div>
  );
};

export default ReportsAnalytics;
