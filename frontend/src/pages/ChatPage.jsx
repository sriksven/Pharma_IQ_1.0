import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import Header from '../components/layout/Header'
import Sidebar from '../components/layout/Sidebar'
import ChatThread from '../components/chat/ChatThread'
import InputBar from '../components/chat/InputBar'
import ErrorBanner from '../components/common/ErrorBanner'
import { sendMessage, getSession } from '../api/client'
import styles from './ChatPage.module.css'

export default function ChatPage() {
    const [searchParams, setSearchParams] = useSearchParams()
    const [sessionId, setSessionId] = useState(null)
    const [messages, setMessages] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        const sid = searchParams.get('session')
        if (sid) {
            setSessionId(sid)
            loadSession(sid)
        }
    }, [searchParams])

    async function loadSession(sid) {
        try {
            const data = await getSession(sid)
            const msgs = data.messages.map((m) => ({
                ...m,
                chart_data: null,
                chart_hint: null,
            }))
            setMessages(msgs)
        } catch {
            setMessages([])
        }
    }

    function handleNewChat() {
        setSessionId(null)
        setMessages([])
        setError(null)
        setSearchParams({})
    }

    async function handleSubmit(question) {
        setError(null)
        const userMsg = { role: 'user', content: question }
        setMessages((prev) => [...prev, userMsg])
        setLoading(true)

        try {
            const response = await sendMessage(sessionId, question)

            if (!sessionId) {
                setSessionId(response.session_id)
                setSearchParams({ session: response.session_id })
            }

            const assistantMsg = {
                role: 'assistant',
                content: response.answer,
                sql_query: response.sql,
                provenance: response.provenance,
                chart_hint: response.chart_hint,
                chart_data: response.result_data || null,
                llm_used: response.llm_used,
                cache_hit: response.cache_hit,
                fallback_reason: response.fallback_reason,
            }

            setMessages((prev) => [...prev, assistantMsg])
        } catch (err) {
            setError(err.message || 'Something went wrong.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className={styles.page}>
            <Header />
            <div className={styles.body}>
                <Sidebar onNewChat={handleNewChat} currentSessionId={sessionId} />
                <main className={styles.main}>
                    <ErrorBanner message={error} onDismiss={() => setError(null)} />
                    <ChatThread messages={messages} loading={loading} />
                    <InputBar onSubmit={handleSubmit} disabled={loading} />
                </main>
            </div>
        </div>
    )
}
