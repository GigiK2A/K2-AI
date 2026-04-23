import React from 'react'

export function ChatBubble({ role, text }: { role: 'user' | 'assistant'; text: string }) {
  const isAssistant = role === 'assistant'
  return (
    <div className={`kbot-msg-row ${isAssistant ? 'assistant' : 'user'} msg-in`}>
      {isAssistant ? <span className="kbot-avatar">K</span> : null}
      <div className={`kbot-bubble ${isAssistant ? 'assistant' : 'user'}`}>
        <div className="kbot-bubble-role">{isAssistant ? 'K-BOT' : 'Tu'}</div>
        <div className="kbot-bubble-text">{text}</div>
      </div>
    </div>
  )
}
