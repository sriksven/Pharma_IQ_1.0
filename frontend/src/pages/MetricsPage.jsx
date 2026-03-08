import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMetricsSummary, getMetricsQueries, getMetricsEvals } from '../api/client'
import Header from '../components/layout/Header'
import styles from './MetricsPage.module.css'

export default function MetricsPage() {
    const [summary, setSummary] = useState(null)
    const [queries, setQueries] = useState([])
    const [evals, setEvals] = useState([])
    const navigate = useNavigate()

    useEffect(() => {
        getMetricsSummary().then(setSummary).catch(() => { })
        getMetricsQueries(10).then((d) => setQueries(d.queries || [])).catch(() => { })
        getMetricsEvals(10).then((d) => setEvals(d.evals || [])).catch(() => { })
    }, [])

    return (
        <div className={styles.page}>
            <Header />
            <div className={styles.body}>
                <div className={styles.topBar}>
                    <button className="btn" onClick={() => navigate('/')}>Back to chat</button>
                    <h1 className={styles.title}>Monitoring</h1>
                </div>

                {summary && (
                    <div className={styles.grid}>
                        <Stat label="Total queries" value={summary.total_queries} />
                        <Stat label="Avg latency" value={`${summary.avg_latency_ms} ms`} />
                        <Stat label="Cache hit rate" value={`${summary.cache_hit_rate}%`} />
                        <Stat label="Fallback rate" value={`${summary.fallback_rate}%`} />
                        <Stat label="Avg retry count" value={summary.avg_retry_count} />
                        <Stat label="Failed rate" value={`${summary.failed_rate}%`} />
                        <Stat label="Avg SQL correctness" value={`${summary.avg_sql_correctness}/10`} />
                        <Stat label="Avg answer relevance" value={`${summary.avg_answer_relevance}/10`} />
                        <Stat label="Avg faithfulness" value={summary.avg_faithfulness != null ? `${summary.avg_faithfulness}/10` : '--'} />
                        <Stat label="Avg schema precision" value={summary.avg_schema_precision != null ? `${summary.avg_schema_precision}/10` : '--'} />
                    </div>
                )}

                {queries.length > 0 && (
                    <div className={styles.section}>
                        <h2 className={styles.sectionTitle}>Recent queries</h2>
                        <table className={styles.table}>
                            <thead>
                                <tr>
                                    <th>Latency (ms)</th>
                                    <th>LLM</th>
                                    <th>Cache</th>
                                    <th>Retries</th>
                                    <th>Failed</th>
                                    <th>Recorded</th>
                                </tr>
                            </thead>
                            <tbody>
                                {queries.map((q, i) => (
                                    <tr key={i}>
                                        <td>{q.total_latency_ms}</td>
                                        <td>{q.llm_used}</td>
                                        <td>{q.cache_hit ? 'Yes' : 'No'}</td>
                                        <td>{q.retry_count}</td>
                                        <td>{q.failed ? 'Yes' : 'No'}</td>
                                        <td>{q.recorded_at?.slice(0, 19)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {evals.length > 0 && (
                    <div className={styles.section}>
                        <h2 className={styles.sectionTitle}>Recent evals</h2>
                        <table className={styles.table}>
                            <thead>
                                <tr>
                                    <th>SQL Correctness</th>
                                    <th>SQL Efficiency</th>
                                    <th>Schema Precision</th>
                                    <th>Answer Relevance</th>
                                    <th>Answer Clarity</th>
                                    <th>Insight</th>
                                    <th>Faithfulness</th>
                                    <th>Evaluated</th>
                                </tr>
                            </thead>
                            <tbody>
                                {evals.map((e, i) => (
                                    <tr key={i}>
                                        <td>{(e.sql_correctness * 10).toFixed(1)}</td>
                                        <td>{(e.sql_efficiency * 10).toFixed(1)}</td>
                                        <td>{e.sql_schema_precision != null ? (e.sql_schema_precision * 10).toFixed(1) : '--'}</td>
                                        <td>{(e.answer_relevance * 10).toFixed(1)}</td>
                                        <td>{(e.answer_clarity * 10).toFixed(1)}</td>
                                        <td>{(e.answer_insight * 10).toFixed(1)}</td>
                                        <td>{e.answer_faithfulness != null ? (e.answer_faithfulness * 10).toFixed(1) : '--'}</td>
                                        <td>{e.evaluated_at?.slice(0, 19)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}

function Stat({ label, value }) {
    return (
        <div className={styles.stat}>
            <div className={styles.statValue}>{value ?? '--'}</div>
            <div className={styles.statLabel}>{label}</div>
        </div>
    )
}
