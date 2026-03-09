import { useState, useRef } from 'react'
import styles from './InputBar.module.css'
import VoiceButton from '../voice/VoiceButton'

export default function InputBar({ onSubmit, disabled, onVoiceClick }) {
    const [value, setValue] = useState('')
    const textareaRef = useRef(null)

    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            submit()
        }
    }

    function submit() {
        const q = value.trim()
        if (!q || disabled) return
        onSubmit(q)
        setValue('')
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto'
        }
    }

    function handleInput(e) {
        setValue(e.target.value)
        // Auto-grow textarea
        e.target.style.height = 'auto'
        e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px'
    }

    return (
        <div className={styles.wrapper}>
            <div className={styles.bar}>
                <textarea
                    ref={textareaRef}
                    className={styles.input}
                    placeholder="Ask a question about your data..."
                    value={value}
                    onChange={handleInput}
                    onKeyDown={handleKeyDown}
                    disabled={disabled}
                    rows={1}
                />
                <button
                    className={`btn btn-primary ${styles.sendBtn}`}
                    onClick={submit}
                    disabled={disabled || !value.trim()}
                >
                    Send
                </button>
                <VoiceButton
                    onClick={onVoiceClick}
                    disabled={disabled}
                />
            </div>
            <div className={styles.hint}>Enter to send, Shift+Enter for newline</div>
        </div>
    )
}
