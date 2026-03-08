import { useState } from 'react'
import { rateMessage } from '../../api/client'
import styles from './FeedbackButtons.module.css'

export default function FeedbackButtons({ messageId, initialScore = 0 }) {
    const [score, setScore] = useState(initialScore)
    const [loading, setLoading] = useState(false)

    const handleRate = async (newScore) => {
        if (loading || score === newScore) return

        // Toggle off if clicking the currently active button
        const finalScore = score === newScore ? 0 : newScore

        setLoading(true)
        try {
            await rateMessage(messageId, finalScore)
            setScore(finalScore)
        } catch (err) {
            console.error('Failed to rate message:', err)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className={styles.container}>
            <button
                className={`${styles.btn} ${score === 1 ? styles.activeUp : ''}`}
                onClick={() => handleRate(1)}
                disabled={loading}
                title="Good response"
            >
                👍
            </button>
            <button
                className={`${styles.btn} ${score === -1 ? styles.activeDown : ''}`}
                onClick={() => handleRate(-1)}
                disabled={loading}
                title="Bad response"
            >
                👎
            </button>
        </div>
    )
}
