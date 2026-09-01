/** Ежедневная сводка «дежурного агента»: расписание, стоп/старт, результаты за день. */
import React, { useEffect, useState } from 'react';
import { Card, CardBody, Row, Col, Table, Form, Button, Spinner, Alert, Badge } from 'react-bootstrap';
import AppHeader from '../components/AppHeader';
import api from '../api/axios';

const DailyDigest: React.FC = () => {
  const [sched, setSched] = useState<any>(null);
  const [digest, setDigest] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ text: string; variant: string } | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [s, d] = await Promise.all([
        api.get('/api/ai/digest/schedule'),
        api.get('/api/ai/digest/latest'),
      ]);
      setSched(s.data);
      setDigest(d.data);
    } catch (e: any) {
      setMsg({ text: e?.response?.data?.detail || 'Ошибка загрузки', variant: 'danger' });
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const saveSchedule = async (patch: any) => {
    setSaving(true);
    try {
      const r = await api.put('/api/ai/digest/schedule', { ...sched, ...patch });
      setSched(r.data);
    } catch (e: any) {
      setMsg({ text: e?.response?.data?.detail || 'Ошибка сохранения', variant: 'danger' });
    } finally { setSaving(false); }
  };

  const runNow = async () => {
    setRunning(true); setMsg(null);
    try {
      const r = await api.post('/api/ai/digest/run', {});
      setDigest(r.data);
      setMsg({ text: 'Сводка сформирована', variant: 'success' });
      load();
    } catch (e: any) {
      setMsg({ text: e?.response?.data?.detail || 'Ошибка формирования сводки', variant: 'danger' });
    } finally { setRunning(false); }
  };

  const batchTable = (rows: any[], variant: string) => (
    <div style={{ maxHeight: 260, overflowY: 'auto' }}>
      <Table size="sm" striped bordered className="mb-0">
        <thead><tr><th>Партия</th><th>Сорт</th><th>Допуск</th></tr></thead>
        <tbody>{rows.map((b, i) => (
          <tr key={i}><td><strong>{b.batch}</strong></td><td>{b.variety || '—'}</td>
            <td><Badge bg={variant}>{b.value || '—'}</Badge></td></tr>
        ))}</tbody>
      </Table>
    </div>
  );

  return (
    <div className="min-h-screen bg-light">
      <AppHeader showAdminLink showDashboardLink />
      <div className="container-fluid py-4" style={{ maxWidth: 1100 }}>
        <h3 className="mb-3">📅 Ежедневная сводка</h3>
        {msg && <Alert variant={msg.variant} dismissible onClose={() => setMsg(null)}>{msg.text}</Alert>}

        {loading ? <div className="text-center py-5"><Spinner animation="border" variant="primary" /></div> : (
          <>
            {/* Настройки расписания */}
            <Card className="mb-4"><CardBody>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h6 className="mb-0">Автозапуск агента</h6>
                <Badge bg={sched?.enabled ? 'success' : 'secondary'}>{sched?.enabled ? 'Работает' : 'Остановлен'}</Badge>
              </div>
              <Row className="g-3 align-items-end">
                <Col md="auto">
                  <Form.Check type="switch" id="digest-enabled" label={sched?.enabled ? 'Агент включён' : 'Агент выключен'}
                    checked={!!sched?.enabled} disabled={saving}
                    onChange={(e) => saveSchedule({ enabled: e.target.checked })} />
                </Col>
                <Col md={3}>
                  <Form.Label className="small text-muted mb-1">Время запуска (время сервера, UTC)</Form.Label>
                  <Form.Control type="time" value={sched?.run_time || '07:00'} disabled={saving}
                    onChange={(e) => setSched({ ...sched, run_time: e.target.value })}
                    onBlur={(e) => saveSchedule({ run_time: e.target.value })} />
                </Col>
                <Col md={3}>
                  <Form.Label className="small text-muted mb-1">За какой день</Form.Label>
                  <Form.Select value={sched?.day_mode || 'yesterday'} disabled={saving}
                    onChange={(e) => saveSchedule({ day_mode: e.target.value })}>
                    <option value="yesterday">за вчера</option>
                    <option value="today">за сегодня</option>
                  </Form.Select>
                </Col>
                <Col md="auto">
                  <Button variant="primary" onClick={runNow} disabled={running}>
                    {running ? <><Spinner size="sm" animation="border" className="me-2" />Формирую…</> : '▶ Сформировать сейчас'}
                  </Button>
                </Col>
              </Row>
              <div className="small text-muted mt-2">
                Последний запуск: {sched?.last_run_at ? new Date(sched.last_run_at).toLocaleString('ru-RU') : '—'}
                {sched?.last_status ? ` · статус: ${sched.last_status}` : ''}
              </div>
            </CardBody></Card>

            {/* Сводка */}
            {!digest ? (
              <Alert variant="info">Сводок пока нет. Нажмите «Сформировать сейчас» или включите автозапуск.</Alert>
            ) : (
              <>
                <div className="d-flex align-items-center gap-2 mb-3">
                  <h5 className="mb-0">Сводка за {digest.digest_date}</h5>
                  {digest.status && digest.status !== 'ok' && <Badge bg="warning">{digest.status}</Badge>}
                  <span className="text-muted small">сформирована {digest.created_at ? new Date(digest.created_at).toLocaleString('ru-RU') : ''} ({digest.triggered_by === 'schedule' ? 'авто' : 'вручную'})</span>
                </div>
                {digest.error && <Alert variant="warning" className="py-2">Замечания импорта: {digest.error}</Alert>}

                <Row className="g-3 mb-4">
                  {[['Отчётов', digest.reports_count, 'primary'], ['С отклонением', digest.reports_with_deviations, 'danger'],
                    ['Отклонений', digest.deviations_count, 'danger'], ['Допущено партий', digest.released_count, 'success'],
                    ['Не допущено', digest.not_released_count, 'warning']].map(([l, v, c]: any, i) => (
                    <Col key={i}><Card className="text-center"><CardBody>
                      <div className="h3 mb-0"><Badge bg={c}>{v}</Badge></div>
                      <small className="text-muted">{l}</small>
                    </CardBody></Card></Col>
                  ))}
                </Row>

                {digest.summary && (
                  <Card className="mb-4 border-primary"><CardBody>
                    <h6 className="mb-2">🍺 Разбор агента — что исправить</h6>
                    <div style={{ whiteSpace: 'pre-wrap' }}>{digest.summary}</div>
                  </CardBody></Card>
                )}

                <Row>
                  <Col md={6}>
                    <Card className="mb-4"><CardBody>
                      <h6 className="text-success">✅ Допущенные партии <Badge bg="success">{digest.released_count}</Badge></h6>
                      {digest.released_batches?.length ? batchTable(digest.released_batches, 'success')
                        : <div className="text-muted small">Нет</div>}
                    </CardBody></Card>
                  </Col>
                  <Col md={6}>
                    <Card className="mb-4"><CardBody>
                      <h6 className="text-warning">⛔ Не допущенные партии <Badge bg="warning">{digest.not_released_count}</Badge></h6>
                      {digest.not_released_batches?.length ? batchTable(digest.not_released_batches, 'warning')
                        : <div className="text-muted small">Нет</div>}
                    </CardBody></Card>
                  </Col>
                </Row>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default DailyDigest;
