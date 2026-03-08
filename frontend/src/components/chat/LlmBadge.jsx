import styles from './LlmBadge.module.css'

export default function LlmBadge({ llmUsed, cacheHit, fallbackReason }) {
    return (
        <div className={styles.wrapper}>
            {!!cacheHit && <span className="badge badge-cached">Cached</span>}
            {llmUsed === 'groq' && !cacheHit && (
                <span className="badge badge-info">Groq 120B/8B</span>
            )}
            {llmUsed === 'groq_fallback' && (
                <span className="badge badge-fallback" title={fallbackReason || ''}>
                    Groq 20B (fallback)
                </span>
            )}
        </div>
    )
}
