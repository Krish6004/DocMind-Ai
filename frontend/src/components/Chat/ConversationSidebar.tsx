import React, { useState } from 'react'
import {
  Plus,
  Search,
  Pin,
  PinOff,
  Trash2,
  Edit2,
  Check,
  X,
  Clock,
} from 'lucide-react'

export interface ConversationSession {
  id: string
  title: string
  lastMessage: string
  updatedAt: string
  isPinned: boolean
}

interface ConversationSidebarProps {
  sessions: ConversationSession[]
  activeSessionId: string
  onSelectSession: (id: string) => void
  onNewChat: () => void
  onDeleteSession: (id: string) => void
  onRenameSession: (id: string, newTitle: string) => void
  onTogglePin: (id: string) => void
}

export const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  onRenameSession,
  onTogglePin,
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')

  const handleStartRename = (e: React.MouseEvent, s: ConversationSession) => {
    e.stopPropagation()
    setEditingId(s.id)
    setEditTitle(s.title)
  }

  const handleSaveRename = (e: React.MouseEvent | React.KeyboardEvent, id: string) => {
    e.stopPropagation()
    if (editTitle.trim()) {
      onRenameSession(id, editTitle.trim())
    }
    setEditingId(null)
  }

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(null)
  }

  const filtered = sessions.filter(
    (s) =>
      s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const pinnedSessions = filtered.filter((s) => s.isPinned)
  const recentSessions = filtered.filter((s) => !s.isPinned)

  const renderSessionItem = (session: ConversationSession) => {
    const isActive = session.id === activeSessionId
    const isEditing = editingId === session.id

    return (
      <div
        key={session.id}
        onClick={() => onSelectSession(session.id)}
        className={`group relative p-3 rounded-xl border transition-all cursor-pointer ${
          isActive
            ? 'bg-cerulean/15 border-cerulean/40 text-white shadow-glow-cerulean/20'
            : 'bg-jet-950/40 border-white/[0.04] text-jet-300 hover:bg-white/[0.04] hover:border-white/10'
        }`}
      >
        {isEditing ? (
          <div className="flex items-center space-x-1.5" onClick={(e) => e.stopPropagation()}>
            <input
              type="text"
              autoFocus
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSaveRename(e, session.id)
                if (e.key === 'Escape') setEditingId(null)
              }}
              className="w-full px-2 py-1 bg-jet-900 border border-cerulean rounded text-xs text-white focus:outline-none"
            />
            <button
              type="button"
              onClick={(e) => handleSaveRename(e, session.id)}
              className="p-1 rounded text-emerald-400 hover:bg-emerald-500/10"
            >
              <Check className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={handleCancelRename}
              className="p-1 rounded text-jet-400 hover:bg-white/5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-1">
              <span className="text-xs font-semibold truncate flex-1 text-jet-100">
                {session.title}
              </span>
              <span className="text-[10px] font-mono text-jet-400 shrink-0">
                {session.updatedAt}
              </span>
            </div>

            <p className="text-[11px] text-jet-400 truncate leading-snug">
              {session.lastMessage || 'New inquiry thread...'}
            </p>

            {/* Hover Actions */}
            <div className="pt-1 flex items-center justify-end space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  onTogglePin(session.id)
                }}
                className="p-1 rounded hover:bg-white/10 text-jet-400 hover:text-cerulean-light transition-colors"
                title={session.isPinned ? 'Unpin chat' : 'Pin chat'}
              >
                {session.isPinned ? <PinOff className="w-3 h-3" /> : <Pin className="w-3 h-3" />}
              </button>

              <button
                type="button"
                onClick={(e) => handleStartRename(e, session)}
                className="p-1 rounded hover:bg-white/10 text-jet-400 hover:text-white transition-colors"
                title="Rename conversation"
              >
                <Edit2 className="w-3 h-3" />
              </button>

              {sessions.length > 1 && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteSession(session.id)
                  }}
                  className="p-1 rounded hover:bg-rose-500/10 text-jet-400 hover:text-rose-400 transition-colors"
                  title="Delete conversation"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col glass-panel rounded-3xl border border-white/10 overflow-hidden w-64 lg:w-72 shrink-0">
      {/* Top Action: New Chat */}
      <div className="p-4 border-b border-white/[0.08] space-y-3">
        <button
          type="button"
          onClick={onNewChat}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-cerulean hover:bg-cerulean-light text-white font-medium text-xs sm:text-sm shadow-glow-cerulean transition-all active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>New Chat</span>
        </button>

        {/* Search Bar */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-jet-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-jet-950/80 border border-white/10 text-xs text-jet-200 placeholder-jet-500 focus:outline-none focus:border-cerulean/50"
          />
        </div>
      </div>

      {/* Session Lists */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Pinned Section */}
        {pinnedSessions.length > 0 && (
          <div className="space-y-1.5">
            <div className="flex items-center space-x-1.5 px-2 text-[10px] uppercase font-mono tracking-wider text-jet-400">
              <Pin className="w-3 h-3 text-cerulean-light" />
              <span>Pinned ({pinnedSessions.length})</span>
            </div>
            <div className="space-y-1.5">{pinnedSessions.map(renderSessionItem)}</div>
          </div>
        )}

        {/* Recent Section */}
        <div className="space-y-1.5">
          <div className="flex items-center space-x-1.5 px-2 text-[10px] uppercase font-mono tracking-wider text-jet-400">
            <Clock className="w-3 h-3 text-jet-400" />
            <span>Recent Chats</span>
          </div>
          {recentSessions.length === 0 && pinnedSessions.length === 0 ? (
            <div className="p-4 text-center text-xs text-jet-400">No chats found.</div>
          ) : (
            <div className="space-y-1.5">{recentSessions.map(renderSessionItem)}</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ConversationSidebar
