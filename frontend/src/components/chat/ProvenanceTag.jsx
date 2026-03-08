import { useState } from 'react'
import CsvModal from '../common/CsvModal'
import styles from './ProvenanceTag.module.css'

export default function ProvenanceTag({ provenance }) {
    const [activeCsv, setActiveCsv] = useState(null)

    if (!provenance || provenance.length === 0) return null

    return (
        <>
            <div className={styles.wrapper}>
                <span className={styles.label}>Source:</span>
                {provenance.map((p) => (
                    <button
                        key={p.table}
                        className={styles.tag}
                        onClick={() => setActiveCsv(p.file)}
                        title={`Preview ${p.file}`}
                    >
                        {p.file}
                    </button>
                ))}
            </div>
            <CsvModal filename={activeCsv} onClose={() => setActiveCsv(null)} />
        </>
    )
}
