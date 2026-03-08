import SqlViewer from './SqlViewer'
import ProvenanceTag from './ProvenanceTag'
import LlmBadge from './LlmBadge'
import AutoChart from '../charts/AutoChart'
import FeedbackButtons from './FeedbackButtons'
import styles from './MessageBubble.module.css'

export default function MessageBubble({ message }) {
    const isUser = message.role === 'user'

    if (isUser) {
        return (
            <div className={styles.userBubble}>
                <p>{message.content}</p>
            </div>
        )
    }

    return (
        <div className={styles.assistantBubble}>
            <div className={styles.answer}>{message.content}</div>

            {message.chart_hint && message.chart_data && (
                <div className={styles.chartWrapper}>
                    <AutoChart chartHint={message.chart_hint} data={message.chart_data} />
                </div>
            )}

            <SqlViewer sql={message.sql_query || message.sql} />

            <ProvenanceTag
                provenance={
                    typeof message.provenance === 'string'
                        ? JSON.parse(message.provenance || '[]')
                        : message.provenance
                }
            />

            <div className={styles.footerRow}>
                <LlmBadge
                    llmUsed={message.llm_used}
                    cacheHit={message.cache_hit}
                    fallbackReason={message.fallback_reason}
                />
                {!message.cache_hit && (
                    <FeedbackButtons
                        messageId={message.id || message.message_id}
                        initialScore={message.user_feedback || 0}
                    />
                )}
            </div>
        </div>
    )
}
