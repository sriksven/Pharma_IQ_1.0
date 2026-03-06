import styles from './ErrorBanner.module.css'

export default function ErrorBanner({ message, onDismiss }) {
    if (!message) return null
    return (
        <div className={styles.banner}>
            <span>{message}</span>
            {onDismiss && (
                <button className={styles.dismiss} onClick={onDismiss}>Dismiss</button>
            )}
        </div>
    )
}
