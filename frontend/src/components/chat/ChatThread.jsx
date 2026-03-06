import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'
import Spinner from '../common/Spinner'
import styles from './ChatThread.module.css'

export default function ChatThread({ messages, loading }) {
    const bottomRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, loading])

    if (messages.length === 0 && !loading) {
        return (
            <div className={styles.empty}>
                <p className={styles.emptyText}>Ask a question about your pharmaceutical sales data.</p>
                <p className={styles.emptyHint}>
                    Try: "Which Tier A HCPs haven't had a rep visit in the last 60 days?"
                </p>
            </div>
        )
    }

    return (
        <div className={styles.thread}>
            {messages.map((msg, i) => (
                <MessageBubble key={i} message={msg} />
            ))}
            {loading && (
                <div className={styles.loadingRow}>
                    <Spinner />
                    <span className={styles.loadingText}>Generating...</span>
                </div>
            )}
            <div ref={bottomRef} />
        </div>
    )
}
