import React from 'react'
import { useLocation } from 'react-router-dom'
import { ChatLayout } from '@/components/Chat'

export const ChatPage: React.FC = () => {
  const location = useLocation()
  const initialQuery = (location.state as any)?.query || ''

  return <ChatLayout initialQuery={initialQuery} />
}

export default ChatPage
