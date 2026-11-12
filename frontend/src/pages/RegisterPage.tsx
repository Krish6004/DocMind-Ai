import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Lock, Mail, User, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react'
import Logo from '@/components/common/Logo'
import Button from '@/components/common/Button'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/hooks/useToast'

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate()
  const { register } = useAuth()
  const { success, error: toastError } = useToast()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !email.trim() || !password) return

    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.')
      return
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.')
      return
    }

    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      await register(name.trim(), email.trim(), password)
      success('Account Created', 'Your private knowledge vault is ready.')
      navigate('/', { replace: true })
    } catch (err: any) {
      const msg = err.message || 'Registration failed.'
      setErrorMessage(msg)
      toastError('Registration Error', msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-jet-950 text-white relative overflow-hidden">
      {/* Background radial ambient lights */}
      <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-cerulean/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/3 w-96 h-96 bg-neonrose/10 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="w-full max-w-md p-8 rounded-3xl glass-panel border border-white/10 bg-jet-950/80 shadow-2xl relative z-10 space-y-6"
      >
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <Logo size="lg" showText={false} />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Create Workspace</h1>
          <p className="text-xs text-jet-400 font-mono">
            Isolated Document Vault & Encrypted History
          </p>
        </div>

        {errorMessage && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase tracking-wider text-jet-300">
              Full Name
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-jet-400 absolute left-3.5 top-3" />
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Alex Morgan"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-jet-900/80 border border-white/10 text-sm text-white placeholder:text-jet-500 focus:outline-none focus:border-cerulean-light transition-colors font-mono"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase tracking-wider text-jet-300">
              Work Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-jet-400 absolute left-3.5 top-3" />
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-jet-900/80 border border-white/10 text-sm text-white placeholder:text-jet-500 focus:outline-none focus:border-cerulean-light transition-colors font-mono"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase tracking-wider text-jet-300">
              Password (Min 6 Characters)
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-jet-400 absolute left-3.5 top-3" />
              <input
                type="password"
                required
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-jet-900/80 border border-white/10 text-sm text-white placeholder:text-jet-500 focus:outline-none focus:border-cerulean-light transition-colors font-mono"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase tracking-wider text-jet-300">
              Confirm Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-jet-400 absolute left-3.5 top-3" />
              <input
                type="password"
                required
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-jet-900/80 border border-white/10 text-sm text-white placeholder:text-jet-500 focus:outline-none focus:border-cerulean-light transition-colors font-mono"
              />
            </div>
          </div>

          <Button
            type="submit"
            variant="cerulean"
            size="lg"
            disabled={isSubmitting}
            rightIcon={<ArrowRight className="w-4 h-4" />}
            className="w-full py-3 font-semibold text-sm shadow-glass-sm"
          >
            {isSubmitting ? 'Creating Vault...' : 'Create Account'}
          </Button>
        </form>

        <div className="pt-4 border-t border-white/[0.08] text-center text-xs text-jet-400">
          Already have an account?{' '}
          <Link to="/login" className="text-cerulean-light hover:underline font-medium">
            Sign in
          </Link>
        </div>

        <div className="flex items-center justify-center gap-2 text-[10px] font-mono text-jet-400 pt-1">
          <ShieldCheck className="w-3 h-3 text-emerald-400" />
          <span>Multi-Tenant SQLite & NumPy isolation enabled</span>
        </div>
      </motion.div>
    </div>
  )
}

export default RegisterPage
