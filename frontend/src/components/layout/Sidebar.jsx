import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { getSessions, getTables, deleteSession } from '../../api/client'
import CsvModal from '../common/CsvModal'
import styles from './Sidebar.module.css'

export default function Sidebar({ onNewChat, currentSessionId }) {
    const [sessions, setSessions] = useState([])
    const [tables, setTables] = useState([])
    const [activeCsv, setActiveCsv] = useState(null)
    const navigate = useNavigate()
    const location = useLocation()

    const loadSessions = async () => {
        try {
            const data = await getSessions()
            setSessions(data.sessions || [])
        } catch (err) { console.error(err) }
    }

    const loadTables = async () => {
        try {
            const data = await getTables()
            setTables(data.tables || [])
        } catch (err) { console.error(err) }
    }

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        loadSessions()
        loadTables()
    }, [currentSessionId])

    async function handleDelete(e, sessionId) {
        e.stopPropagation()
        await deleteSession(sessionId)
        loadSessions()
        if (currentSessionId === sessionId) {
            onNewChat()
        }
    }

    return (
        <>
            <aside className={styles.sidebar}>
                <div className={styles.section}>
                    <button className={`btn btn-primary ${styles.newChat}`} onClick={onNewChat}>
                        New chat
                    </button>
                </div>

                <div className={styles.section}>
                    <div className={styles.sectionLabel}>Past chats</div>
                    {sessions.length === 0 && (
                        <div className={styles.empty}>No sessions yet</div>
                    )}
                    {sessions.map((s) => (
                        <div
                            key={s.session_id}
                            className={`${styles.sessionItem} ${currentSessionId === s.session_id ? styles.active : ''}`}
                            onClick={() => navigate(`/?session=${s.session_id}`)}
                        >
                            <span className={styles.sessionTitle}>{s.title || 'Untitled'}</span>
                            <button
                                className={styles.deleteBtn}
                                onClick={(e) => handleDelete(e, s.session_id)}
                                title="Delete chat"
                            >
                                x
                            </button>
                        </div>
                    ))}
                </div>

                <div className={styles.divider} />

                <div className={styles.section}>
                    <div className={styles.sectionLabel}>Data sources</div>
                    {tables.length === 0 && (
                        <div className={styles.empty}>No tables loaded</div>
                    )}
                    {tables.map((t) => (
                        <button
                            key={t}
                            className={styles.tableItem}
                            onClick={() => setActiveCsv(`${t}.csv`)}
                            title={`Preview ${t}.csv`}
                        >
                            {t}.csv
                        </button>
                    ))}
                </div>

                <div className={styles.divider} />

                <div className={styles.section}>
                    <button
                        className={`btn ${location.pathname === '/metrics' ? styles.activeNav : ''}`}
                        onClick={() => navigate('/metrics')}
                        style={{ width: '100%', justifyContent: 'flex-start' }}
                    >
                        Metrics
                    </button>
                </div>
            </aside>

            <CsvModal filename={activeCsv} onClose={() => setActiveCsv(null)} />
        </>
    )
}
