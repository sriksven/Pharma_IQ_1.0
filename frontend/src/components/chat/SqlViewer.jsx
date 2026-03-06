import { useState } from 'react'
import styles from './SqlViewer.module.css'

export default function SqlViewer({ sql }) {
    const [open, setOpen] = useState(false)

    if (!sql) return null

    return (
        <div className={styles.wrapper}>
            <button className={styles.toggle} onClick={() => setOpen(!open)}>
                {open ? 'Hide SQL' : 'Show SQL'}
                <span className={styles.caret}>{open ? '▲' : '▼'}</span>
            </button>
            {open && (
                <pre className={styles.code}><code>{sql}</code></pre>
            )}
        </div>
    )
}
