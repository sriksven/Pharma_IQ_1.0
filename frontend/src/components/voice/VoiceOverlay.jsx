import { useState, useRef, useCallback, useEffect } from 'react'
import { Room, RoomEvent, Track, ConnectionState } from 'livekit-client'
import { getLiveKitToken } from '../../api/client'
import styles from './VoiceOverlay.module.css'

export default function VoiceOverlay({ sessionId, onClose, onVoiceMessage }) {
    const [status, setStatus] = useState('connecting') // connecting | listening | speaking | thinking | idle
    const [transcripts, setTranscripts] = useState([])
    const roomRef = useRef(null)
    const audioElemsRef = useRef([])
    const scrollRef = useRef(null)

    const cleanup = useCallback(() => {
        audioElemsRef.current.forEach((el) => {
            el.pause()
            el.remove()
        })
        audioElemsRef.current = []
        if (roomRef.current) {
            roomRef.current.disconnect()
            roomRef.current = null
        }
    }, [])

    const onVoiceMessageRef = useRef(onVoiceMessage)
    const onCloseRef = useRef(onClose)

    useEffect(() => {
        onVoiceMessageRef.current = onVoiceMessage
        onCloseRef.current = onClose
    }, [onVoiceMessage, onClose])

    const initialSessionId = useRef(sessionId)

    useEffect(() => {
        let isMounted = true

        const setupRoom = async () => {
            try {
                const { token, url } = await getLiveKitToken(initialSessionId.current)
                if (!isMounted) return

                const room = new Room()
                roomRef.current = room

                room.on(RoomEvent.TrackSubscribed, (track) => {
                    if (track.kind === Track.Kind.Audio) {
                        const el = track.attach()
                        document.body.appendChild(el)
                        audioElemsRef.current.push(el)
                        el.play().catch(console.error)
                    }
                })

                room.on(RoomEvent.TrackUnsubscribed, (track) => {
                    track.detach()
                })

                room.on(RoomEvent.DataReceived, (rawData) => {
                    try {
                        const data = new TextDecoder().decode(rawData)
                        const msg = JSON.parse(data)
                        console.log('[VoiceOverlay] Received data:', msg)

                        if (msg.type === 'user' || msg.type === 'assistant') {
                            setTranscripts(prev => [...prev, {
                                role: msg.type,
                                text: msg.text,
                                id: Date.now() + Math.random()
                            }])
                            onVoiceMessageRef.current?.(msg)
                        } else if (msg.type === 'status') {
                            setStatus(msg.status)
                        }
                    } catch (err) {
                        console.error('Error parsing livekit data:', err)
                    }
                })

                room.on(RoomEvent.ConnectionStateChanged, (state) => {
                    if (state === ConnectionState.Disconnected) {
                        if (isMounted) {
                            cleanup()
                            onCloseRef.current?.()
                        }
                    }
                })

                await room.connect(url, token, { autoSubscribe: true })
                await room.localParticipant.setMicrophoneEnabled(true)
                if (isMounted) setStatus('listening')
            } catch (err) {
                console.error('[VoiceOverlay] Connection error:', err)
                if (isMounted) {
                    cleanup()
                    onCloseRef.current?.()
                }
            }
        }

        setupRoom()

        return () => {
            isMounted = false
            cleanup()
        }
    }, [])

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [transcripts])

    return (
        <div className={styles.overlay}>
            <button className={styles.closeBtn} onClick={() => { cleanup(); onClose(); }} aria-label="Close voice mode">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>

            <div className={styles.visualizerContainer}>
                <div className={`${styles.circle} ${(status === 'listening' || status === 'speaking' || status === 'thinking') ? styles.activeCircle : ''}`}>
                    {(status === 'listening' || status === 'speaking' || status === 'thinking') && (
                        <div className={`${styles.pulse} ${status === 'listening' ? styles.activePulse : ''} ${status === 'thinking' ? styles.thinkingPulse : ''}`}></div>
                    )}
                </div>
            </div>

            <div className={styles.transcriptContainer} ref={scrollRef}>
                {transcripts.map((t, idx) => (
                    <div
                        key={t.id}
                        className={`${styles.transcriptEntry} ${t.role === 'user' ? styles.userText : styles.assistantText} ${idx === transcripts.length - 1 ? styles.last : ''}`}
                    >
                        {t.text}
                    </div>
                ))}
            </div>

            <div className={styles.status}>
                {status === 'connecting' && 'Connecting...'}
                {status === 'listening' && 'Listening...'}
                {status === 'thinking' && 'Thinking...'}
                {status === 'speaking' && 'Speaking...'}
            </div>
        </div>
    )
}
