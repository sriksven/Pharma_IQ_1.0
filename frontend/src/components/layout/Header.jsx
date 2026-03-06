import styles from './Header.module.css'

export default function Header({ llmStatus }) {
    return (
        <header className={styles.header}>
            <div className={styles.left}>
                <span className={styles.title}>Pharma IQ 1.0</span>
                <span className={styles.subtitle}>Natural language analytics over pharma sales data</span>
            </div>
            <div className={styles.right}>
                <span className="badge badge-info">Groq Llama 3 70B</span>
                <span className="badge">DuckDB</span>
            </div>
        </header>
    )
}
