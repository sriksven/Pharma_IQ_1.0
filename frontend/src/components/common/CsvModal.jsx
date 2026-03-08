import { useState, useEffect, useCallback } from 'react'
import styles from './CsvModal.module.css'

export default function CsvModal({ filename, onClose }) {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!filename) return
        setLoading(true)
        setError(null)
        fetch(`http://localhost:8000/api/v1/data/json/${filename}`)
            .then((r) => r.json())
            .then((d) => { setData(d); setLoading(false) })
            .catch(() => { setError('Failed to load data.'); setLoading(false) })
    }, [filename])

    const handleBackdropClick = useCallback((e) => {
        if (e.target === e.currentTarget) onClose()
    }, [onClose])

    useEffect(() => {
        const onKey = (e) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', onKey)
        return () => window.removeEventListener('keydown', onKey)
    }, [onClose])

    if (!filename) return null

    return (
        <div className={styles.backdrop} onClick={handleBackdropClick}>
            <div className={styles.modal}>
                <div className={styles.header}>
                    <span className={styles.title}>{filename}</span>
                    <button className={styles.closeBtn} onClick={onClose} title="Close">✕</button>
                </div>

                <div className={styles.body}>
                    {loading && <div className={styles.state}>Loading…</div>}
                    {error && <div className={styles.state}>{error}</div>}
                    {data && (
                        <>
                            <div className={styles.meta}>{data.rows.length} rows · {data.columns.length} columns</div>
                            <div className={styles.tableWrap}>
                                <table className={styles.table}>
                                    <thead>
                                        <tr>
                                            {data.columns.map((col) => (
                                                <th key={col}>{col}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.rows.map((row, i) => (
                                            <tr key={i}>
                                                {data.columns.map((col) => (
                                                    <td key={col}>{row[col] ?? ''}</td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
