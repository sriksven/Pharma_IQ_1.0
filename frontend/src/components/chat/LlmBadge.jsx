import styles from './LlmBadge.module.css'

export default function LlmBadge({ llmUsed, cacheHit, fallbackReason }) {
    return (
        <div className={styles.wrapper}>
            {cacheHit && <span className="badge badge-cached">Cached</span>}
            {llmUsed === 'groq' && !cacheHit && (
                <span className="badge badge-info">Groq 70B</span>
            )}
            {llmUsed === 'openai' && (
                <span className="badge badge-fallback" title={fallbackReason || ''}>
                    OpenAI GPT-4o (fallback)
                </span>
            )}
        </div>
    )
}
