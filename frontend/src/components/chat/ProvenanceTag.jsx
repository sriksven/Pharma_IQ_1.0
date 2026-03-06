import styles from './ProvenanceTag.module.css'

export default function ProvenanceTag({ provenance }) {
    if (!provenance || provenance.length === 0) return null

    return (
        <div className={styles.wrapper}>
            <span className={styles.label}>Source:</span>
            {provenance.map((p) => (
                <span key={p.table} className={styles.tag}>
                    {p.file}
                </span>
            ))}
        </div>
    )
}
