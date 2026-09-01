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
  const [msg, setMsg] = useState<{ text: string; variant: string } | null>(null);
  const [chat, setChat] = useState<{ role: 'user' | 'assistant'; content: string }[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

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

  // Контекст сводки для агента: дата + итоги + недопущенные с причинами
  const buildContext = () => {
    if (!digest) return '';
    const nr = (digest.not_released_batches || []).map((b: any) => {
      const why = b.reasons?.length ? b.reasons.map((r: any) => `${r.indicator} ${r.value ?? ''}${r.unit ? ' ' + r.unit : ''} (норма ${r.norm ?? '—'})`).join(', ') : `отметка «${b.value}»`;
      return `${b.batch}${b.variety ? ' [' + b.variety + ']' : ''}: ${why}`;
    }).join('; ');
    const rel = (digest.released_batches || []).map((b: any) => `${b.batch}${b.variety ? ' [' + b.variety + ']' : ''}`).join(', ');
    const dev = (digest.deviation_rows || []).slice(0, 40).map((d: any) =>
      `${d['партия']}${d['сорт'] ? ' [' + d['сорт'] + ']' : ''}${d['ёмкость'] ? ' ёмк.' + d['ёмкость'] : ''}: ${d['показатель']} ${d['значение']}${d['ед'] ? ' ' + d['ед'] : ''} (норма ${d['норма'] || '—'}, ${d['направление']})`).join('; ');
    const san = (digest.sanitation_overdue || []).slice(0, 15).map((s: any) =>
      `${s['мероприятие']} (${s['статус'] === 'ни разу не выполнялось' ? 'ни разу' : 'просрочка ' + s['просрочка_дн'] + ' дн'})`).join('; ');
    return `Ты отвечаешь по ежедневной сводке за ${digest.digest_date} (МСК). Итоги дня: отчётов ${digest.reports_count}, с отклонением ${digest.reports_with_deviations}, всего отклонений ${digest.deviations_count}, допущено партий ${digest.released_count}, не допущено ${digest.not_released_count}, санитария просрочена ${digest.sanitation_overdue_count || 0}.` +
      (rel ? ` Допущенные: ${rel}.` : '') +
      (nr ? ` Не допущенные и причины: ${nr}.` : '') +
      (dev ? ` Отклонения (партия/сорт/ёмкость/показатель/норма): ${dev}.` : '') +
      (san ? ` Просроченная санитария: ${san}.` : '') +
      ` При необходимости уточняй детали инструментами за дату ${digest.digest_date} (в т.ч. get_sanitation_compliance). Отвечай кратко и по делу на русском.`;
  };

  const sendChat = async () => {
    const q = chatInput.trim();
    if (!q || chatLoading) return;
    const next = [...chat, { role: 'user' as const, content: q }];
    setChat(next);
    setChatInput('');
    setChatLoading(true);
    try {
      const seed = [
        { role: 'user' as const, content: buildContext() },
        { role: 'assistant' as const, content: 'Готов отвечать по этой сводке.' },
      ];
      const r = await api.post('/api/ai/chat', { message: q, history: [...seed, ...chat] });
      setChat([...next, { role: 'assistant', content: r.data?.text || '(пустой ответ)' }]);
    } catch (e: any) {
      setChat([...next, { role: 'assistant', content: `⚠ ${e?.response?.data?.detail || 'Ошибка агента'}` }]);
    } finally { setChatLoading(false); }
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

  const notReleasedTable = (rows: any[]) => (
    <div style={{ maxHeight: 320, overflowY: 'auto' }}>
      <Table size="sm" striped bordered className="mb-0">
        <thead><tr><th>Партия</th><th>Сорт</th><th>По каким показателям</th></tr></thead>
        <tbody>{rows.map((b, i) => (
          <tr key={i}>
            <td><strong>{b.batch}</strong></td>
            <td>{b.variety || '—'}</td>
            <td>
              {b.reasons?.length ? (
                <div className="d-flex flex-column gap-1">
                  {b.reasons.map((r: any, j: number) => (
                    <span key={j}>
                      <Badge bg="danger" className="me-1 fw-normal">{r.indicator}</Badge>
                      <span className="small text-muted">{r.value}{r.unit ? ` ${r.unit}` : ''}{r.norm ? ` · норма ${r.norm}` : ''}</span>
                    </span>
                  ))}
                </div>
              ) : (
                <span className="small text-muted">отметка «{b.value}» без зафиксированных отклонений по показателям</span>
              )}
            </td>
          </tr>
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
            {/* Панель формирования (настройки расписания — в разделе «Настройки» → «Агенты») */}
            <Card className="mb-4"><CardBody>
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="mb-1">Ежедневная сводка</h6>
                  <div className="small text-muted">
                    Автозапуск и расписание — в разделе «⚙️ Настройки» → «🤖 Агенты».
                    {sched?.last_run_at ? ` Последний запуск: ${new Date(sched.last_run_at).toLocaleString('ru-RU')}.` : ''}
                  </div>
                </div>
                <Button variant="primary" onClick={runNow} disabled={running}>
                  {running ? <><Spinner size="sm" animation="border" className="me-2" />Формирую…</> : '▶ Сформировать сейчас'}
                </Button>
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

                {/* 1. Отклонения в отчётах — партия, сорт, ёмкость, показатель, отклонение */}
                <Card className="mb-4 border-danger">
                  <CardBody>
                    <h6 className="text-danger">⚠ Отклонения в отчётах{' '}
                      <Badge bg={digest.deviation_rows?.length ? 'danger' : 'success'}>{digest.deviation_rows?.length || 0}</Badge>
                    </h6>
                    {digest.deviation_rows?.length ? (
                      <div style={{ maxHeight: 460, overflowY: 'auto' }}>
                        <Table size="sm" striped bordered className="mb-0">
                          <thead><tr>
                            <th>Партия</th><th>Сорт</th><th>Ёмкость</th><th>Цех</th>
                            <th>Показатель</th><th>Значение</th><th>Норма</th><th>Отклонение</th>
                          </tr></thead>
                          <tbody>{digest.deviation_rows.map((d: any, i: number) => (
                            <tr key={i}>
                              <td><strong>{d['партия']}</strong></td>
                              <td>{d['сорт'] || '—'}</td>
                              <td>{d['ёмкость'] || '—'}</td>
                              <td className="small text-muted">{d['цех'] || '—'}</td>
                              <td>{d['показатель']}</td>
                              <td><Badge bg="danger">{d['значение']}{d['ед'] ? ` ${d['ед']}` : ''}</Badge></td>
                              <td className="small">{d['норма'] || '—'}</td>
                              <td className="small">
                                {d['направление']}{d['отклонение_пр'] != null ? ` (${d['отклонение_пр']}%)` : ''}
                              </td>
                            </tr>
                          ))}</tbody>
                        </Table>
                      </div>
                    ) : <div className="text-muted small">Отклонений в отчётах за день нет ✅</div>}
                  </CardBody>
                </Card>

                <Row className="g-3 mb-4">
                  {[['Допущено партий', digest.released_count, 'success'],
                    ['Не допущено', digest.not_released_count, 'warning'],
                    ['Санитария просрочена', digest.sanitation_overdue_count || 0, (digest.sanitation_overdue_count ? 'danger' : 'success')]].map(([l, v, c]: any, i) => (
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
                  <Col md={5}>
                    <Card className="mb-4"><CardBody>
                      <h6 className="text-success">✅ Допущенные партии <Badge bg="success">{digest.released_count}</Badge></h6>
                      {digest.released_batches?.length ? batchTable(digest.released_batches, 'success')
                        : <div className="text-muted small">Нет</div>}
                    </CardBody></Card>
                  </Col>
                  <Col md={7}>
                    <Card className="mb-4"><CardBody>
                      <h6 className="text-warning">⛔ Не допущенные партии <Badge bg="warning">{digest.not_released_count}</Badge></h6>
                      {digest.not_released_batches?.length ? notReleasedTable(digest.not_released_batches)
                        : <div className="text-muted small">Нет</div>}
                    </CardBody></Card>
                  </Col>
                </Row>

                {/* Санитария: просроченные / невыполненные мероприятия */}
                <Card className="mb-4">
                  <CardBody>
                    <h6 className="text-danger">🧼 Санитария — просрочено / не выполнено{' '}
                      <Badge bg={digest.sanitation_overdue_count ? 'danger' : 'success'}>{digest.sanitation_overdue_count || 0}</Badge>
                    </h6>
                    {digest.sanitation_overdue?.length ? (
                      <div style={{ maxHeight: 340, overflowY: 'auto' }}>
                        <Table size="sm" striped bordered className="mb-0">
                          <thead><tr>
                            <th>Мероприятие</th><th>Периодичность</th><th>Подразделение</th>
                            <th>Последнее</th><th>Срок</th><th>Просрочка</th>
                          </tr></thead>
                          <tbody>{digest.sanitation_overdue.map((s: any, i: number) => (
                            <tr key={i}>
                              <td>{s['мероприятие']}</td>
                              <td className="small text-muted">{s['частота'] || '—'}</td>
                              <td className="small">{s['подразделение'] || '—'}</td>
                              <td className="small">{s['последнее'] || '—'}</td>
                              <td className="small">{s['след_срок'] || '—'}</td>
                              <td>
                                {s['статус'] === 'ни разу не выполнялось'
                                  ? <Badge bg="dark">ни разу</Badge>
                                  : <Badge bg="danger">{s['просрочка_дн']} дн</Badge>}
                              </td>
                            </tr>
                          ))}</tbody>
                        </Table>
                      </div>
                    ) : <div className="text-muted small">Просроченных мероприятий нет — график санитарии соблюдается ✅</div>}
                  </CardBody>
                </Card>

                {/* Чат с агентом по итогам сводки */}
                <Card className="mb-4 border-info">
                  <CardBody>
                    <h6 className="mb-3">💬 Спросить агента по сводке за {digest.digest_date}</h6>
                    <div style={{ maxHeight: 340, overflowY: 'auto' }} className="mb-3">
                      {chat.length === 0 ? (
                        <div className="text-muted small">
                          Задайте вопрос по этой сводке. Например: «Почему не допущено Янтарное?»,
                          «Что срочно исправить?», «Есть ли связь с санитарией в цехе розлива?»
                        </div>
                      ) : chat.map((m, i) => (
                        <div key={i} className={`mb-2 d-flex ${m.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}>
                          <div className={`px-3 py-2 rounded ${m.role === 'user' ? 'bg-primary text-white' : 'bg-light border'}`}
                            style={{ maxWidth: '85%', whiteSpace: 'pre-wrap' }}>
                            {m.content}
                          </div>
                        </div>
                      ))}
                      {chatLoading && <div className="text-muted small"><Spinner size="sm" animation="border" className="me-2" />Агент думает…</div>}
                    </div>
                    <div className="d-flex gap-2">
                      <Form.Control
                        as="textarea" rows={1} value={chatInput} placeholder="Ваш вопрос по сводке…"
                        disabled={chatLoading}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } }}
                      />
                      <Button variant="info" className="text-white" onClick={sendChat} disabled={chatLoading || !chatInput.trim()}>
                        Отправить
                      </Button>
                      {chat.length > 0 && (
                        <Button variant="outline-secondary" onClick={() => setChat([])} disabled={chatLoading}>Очистить</Button>
                      )}
                    </div>
                  </CardBody>
                </Card>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default DailyDigest;
