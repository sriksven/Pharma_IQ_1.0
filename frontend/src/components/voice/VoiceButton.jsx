import { useState, useRef, useCallback, useEffect } from 'react'
import { Room, RoomEvent, Track, ConnectionState } from 'livekit-client'
import { getLiveKitToken } from '../../api/client'
import styles from './VoiceButton.module.css'

export default function VoiceButton({ sessionId, onVoiceMessage, disabled }) {
    const [status, setStatus] = useState('idle') // idle | connecting | active
    const roomRef = useRef(null)
    const audioElemsRef = useRef([])

    function cleanup() {
        audioElemsRef.current.forEach((el) => {
            el.pause()
            el.remove()
        })
        audioElemsRef.current = []
        if (roomRef.current) {
            roomRef.current.disconnect()
            roomRef.current = null
        }
    }

    const connect = useCallback(async () => {
        setStatus('connecting')
        try {
            const { token, url } = await getLiveKitToken(sessionId)
            const room = new Room()
            roomRef.current = room

            room.on(RoomEvent.TrackSubscribed, (track) => {
                if (track.kind === Track.Kind.Audio) {
                    const el = track.attach()
                    document.body.appendChild(el)
                    audioElemsRef.current.push(el)
                    el.play().catch(() => {
                        // Resume audio on next user gesture if autoplay blocked
                        room.startAudio()
                    })
                }
            })

            room.on(RoomEvent.TrackUnsubscribed, (track) => {
                track.detach()
            })

            room.on(RoomEvent.DataReceived, (rawData) => {
                try {
                    const msg = JSON.parse(new TextDecoder().decode(rawData))
                    onVoiceMessage?.(msg)
                } catch {
                    // ignore malformed data messages
                }
            })

            room.on(RoomEvent.ConnectionStateChanged, (state) => {
                if (state === ConnectionState.Disconnected) {
                    cleanup()
                    setStatus('idle')
                }
            })

            await room.connect(url, token, { autoSubscribe: true })
            await room.localParticipant.setMicrophoneEnabled(true)
            setStatus('active')
        } catch (err) {
            console.error('[VoiceButton] LiveKit connection error:', err)
            cleanup()
            setStatus('idle')
        }
    }, [sessionId, onVoiceMessage])

    const disconnect = useCallback(() => {
        cleanup()
        setStatus('idle')
    }, [])

    // Cleanup on unmount
    useEffect(() => () => cleanup(), [])

    const toggle = () => {
        if (status === 'idle') connect()
        else if (status === 'active') disconnect()
    }

    return (
        <button
            className={`${styles.voiceBtn} ${styles[status]}`}
            onClick={toggle}
            disabled={disabled || status === 'connecting'}
            title={status === 'idle' ? 'Start voice mode' : 'Stop voice mode'}
            aria-label={status === 'idle' ? 'Start voice' : 'Stop voice'}
            type="button"
        >
            {status === 'connecting' ? (
                <span className={styles.dots} aria-hidden="true">●●●</span>
            ) : (
                <MicIcon active={status === 'active'} />
            )}
        </button>
    )
}

function MicIcon({ active }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
            style={active ? { color: 'var(--accent)' } : undefined}
        >
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
        </svg>
    )
}
