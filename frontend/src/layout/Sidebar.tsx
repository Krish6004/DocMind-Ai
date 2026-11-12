import React, { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  MessageSquare,
  Files,
  BarChart3,
  Gauge,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import Logo from '@/components/common/Logo'
import { useHealth } from '@/hooks/useHealth'

export interface SidebarProps {
  className?: string
}

interface NavItem {
  name: string
  to: string
  icon: React.ElementType
}

const navItems: NavItem[] = [
  { name: 'Dashboard', to: '/', icon: LayoutDashboard },
  { name: 'Chat Studio', to: '/chat', icon: MessageSquare },
  { name: 'Documents', to: '/documents', icon: Files },
  { name: 'Analytics', to: '/analytics', icon: BarChart3 },
  { name: 'Evaluation', to: '/evaluation', icon: Gauge },
  { name: 'Settings', to: '/settings', icon: Settings },
]

export const Sidebar: React.FC<SidebarProps> = ({ className = '' }) => {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const { data: health } = useHealth()

  const isHealthy = health?.status === 'healthy'

  return (
    <motion.aside
      animate={{ width: collapsed ? 76 : 240 }}
      transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
      className={`h-screen sticky top-0 flex flex-col glass-panel border-r border-white/[0.08] z-30 select-none bg-jet-950/80 backdrop-blur-xl shrink-0 ${className}`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center px-4 border-b border-white/[0.06] justify-between">
        <NavLink to="/" className="flex items-center overflow-hidden">
          <Logo size="md" showText={!collapsed} />
        </NavLink>

        {/* Collapse Toggle Button */}
        <button
          type="button"
          onClick={() => setCollapsed(!collapsed)}
          className="text-jet-400 hover:text-white p-1.5 rounded-lg hover:bg-white/[0.06] transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Menu */}
      <div className="flex-1 py-4 px-2.5 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname === item.to
          const Icon = item.icon

          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={`relative flex items-center px-3 py-2 rounded-xl text-xs font-medium transition-all group ${
                isActive
                  ? 'text-white bg-white/[0.07] border border-white/[0.08] shadow-glass-sm'
                  : 'text-jet-400 hover:text-jet-100 hover:bg-white/[0.03]'
              } ${collapsed ? 'justify-center' : 'justify-start space-x-3'}`}
            >
              <Icon
                className={`w-4 h-4 shrink-0 transition-colors ${
                  isActive ? 'text-cerulean-light' : 'text-jet-400 group-hover:text-jet-200'
                }`}
              />

              {!collapsed && (
                <span className="truncate tracking-wide">{item.name}</span>
              )}

              {/* Minimal Active Pip */}
              {isActive && (
                <motion.div
                  layoutId="active-nav-indicator"
                  className="absolute left-0 top-2 bottom-2 w-0.5 rounded-r bg-cerulean"
                  transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                />
              )}
            </NavLink>
          )
        })}
      </div>

      {/* Bottom Infrastructure Ping */}
      <div className="p-3 border-t border-white/[0.06]">
        <div
          className={`flex items-center rounded-xl p-2 bg-jet-900/60 border border-white/[0.04] ${
            collapsed ? 'justify-center' : 'justify-between'
          }`}
        >
          <div className="flex items-center space-x-2">
            <span className="relative flex h-2 w-2">
              <span
                className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  isHealthy ? 'bg-emerald-400' : 'bg-amber-400'
                }`}
              />
              <span
                className={`relative inline-flex h-2 w-2 rounded-full ${
                  isHealthy ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
              />
            </span>

            {!collapsed && (
              <span className="text-[11px] font-mono text-jet-300">
                {isHealthy ? 'Core Engine Ready' : 'Connecting...'}
              </span>
            )}
          </div>

          {!collapsed && (
            <span className="text-[10px] font-mono text-jet-400">
              v{health?.version || '1.0'}
            </span>
          )}
        </div>
      </div>
    </motion.aside>
  )
}

export default Sidebar
