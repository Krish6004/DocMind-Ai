import React from 'react'
import {
  Bot,
  BookmarkCheck,
  PanelLeftClose,
  PanelLeftOpen,
  Trash2,
  Cpu,
} from 'lucide-react'
import Badge from '@/components/common/Badge'

interface ChatHeaderProps {
  sessionTitle: string
  modelName?: string
  sidebarOpen: boolean
  onToggleSidebar: () => void
  drawerOpen: boolean
  onToggleDrawer: () => void
  onClearChat?: () => void
  messagesCount: number
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  sessionTitle,
  modelName = 'Llama-3-70b',
  sidebarOpen,
  onToggleSidebar,
  drawerOpen,
  onToggleDrawer,
  onClearChat,
  messagesCount,
}) => {
  return (
    <div className="px-4 sm:px-6 py-3 border-b border-white/[0.08] flex items-center justify-between bg-jet-950/60 backdrop-blur-md z-10">
      {/* Left: Sidebar Toggle + Title */}
      <div className="flex items-center space-x-3 min-w-0">
        <button
          type="button"
          onClick={onToggleSidebar}
          className="p-1.5 rounded-lg text-jet-400 hover:text-white hover:bg-white/5 transition-colors shrink-0"
          title={sidebarOpen ? 'Collapse conversations' : 'Open conversations'}
          aria-label="Toggle conversation sidebar"
        >
          {sidebarOpen ? (
            <PanelLeftClose className="w-4 h-4 text-cerulean-light" />
          ) : (
            <PanelLeftOpen className="w-4 h-4" />
          )}
        </button>

        <div className="w-7 h-7 rounded-lg bg-cerulean/15 border border-cerulean/30 flex items-center justify-center text-cerulean-light shrink-0">
          <Bot className="w-4 h-4" />
        </div>

        <div className="min-w-0">
          <div className="flex items-center space-x-2">
            <h2 className="text-xs sm:text-sm font-semibold text-jet-100 truncate max-w-[180px] sm:max-w-xs md:max-w-md">
              {sessionTitle}
            </h2>
            <Badge variant="cerulean" size="sm" dot>
              Grounded
            </Badge>
          </div>
          <div className="flex items-center space-x-2 text-[10px] text-jet-400 font-mono">
            <span className="flex items-center space-x-1">
              <Cpu className="w-2.5 h-2.5 text-cerulean-light" />
              <span>{modelName}</span>
            </span>
            <span>•</span>
            <span className="hidden sm:inline text-jet-500">BM25 + BGE Dense + Cross-Encoder</span>
          </div>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-2 shrink-0">
        {messagesCount > 0 && onClearChat && (
          <button
            type="button"
            onClick={onClearChat}
            className="p-2 rounded-xl text-xs text-jet-400 hover:text-neonrose hover:bg-neonrose/10 transition-colors hidden sm:flex items-center space-x-1"
            title="Clear current conversation turns"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="text-[11px]">Clear</span>
          </button>
        )}

        {/* Right Drawer Toggle */}
        <button
          type="button"
          onClick={onToggleDrawer}
          className={`p-2 rounded-xl text-xs flex items-center space-x-1.5 transition-colors border ${
            drawerOpen
              ? 'bg-cerulean/20 text-cerulean-light border-cerulean/40'
              : 'bg-white/5 text-jet-400 hover:text-white border-white/10'
          }`}
          title={drawerOpen ? 'Close telemetry & sources drawer' : 'Open telemetry & sources drawer'}
        >
          <BookmarkCheck className="w-3.5 h-3.5" />
          <span className="hidden md:inline font-medium">Telemetry & Sources</span>
        </button>
      </div>
    </div>
  )
}

export default ChatHeader
