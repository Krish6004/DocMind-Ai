import React, { forwardRef } from 'react'
import { motion, type HTMLMotionProps } from 'framer-motion'
import { Loader2 } from 'lucide-react'

export interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  children?: React.ReactNode
  variant?: 'cerulean' | 'rose' | 'glass' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'cerulean',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    // Size tokens
    const sizeClasses = {
      sm: 'px-3 py-1.5 text-xs font-medium gap-1.5 rounded-lg',
      md: 'px-4 py-2 text-sm font-medium gap-2 rounded-xl',
      lg: 'px-6 py-3 text-base font-semibold gap-2.5 rounded-xl',
    }[size]

    // Variant tokens (Jet Black, Cerulean Blue, Neon Rose only)
    const variantClasses = {
      cerulean:
        'bg-cerulean hover:bg-cerulean-light text-white shadow-glow-cerulean/50 hover:shadow-glow-cerulean-lg/70 border border-cerulean-light/30 active:border-cerulean-light',
      rose:
        'bg-neonrose hover:bg-neonrose-light text-white shadow-glow-rose/50 hover:shadow-glow-rose-lg/70 border border-neonrose-light/30 active:border-neonrose-light',
      glass:
        'bg-white/[0.04] hover:bg-white/[0.08] text-jet-100 border border-white/10 hover:border-cerulean/50 shadow-glass-sm backdrop-blur-md',
      outline:
        'bg-transparent hover:bg-cerulean/10 text-cerulean-light border border-cerulean/40 hover:border-cerulean',
      ghost:
        'bg-transparent hover:bg-white/[0.05] text-jet-300 hover:text-jet-100 border border-transparent',
    }[variant]

    const isDisabled = disabled || isLoading

    return (
      <motion.button
        ref={ref}
        whileTap={isDisabled ? undefined : { scale: 0.98 }}
        whileHover={isDisabled ? undefined : { scale: 1.01 }}
        transition={{ duration: 0.15 }}
        disabled={isDisabled}
        className={`inline-flex items-center justify-center transition-all select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-cerulean/60 ${sizeClasses} ${variantClasses} ${
          isDisabled ? 'opacity-45 cursor-not-allowed pointer-events-none' : 'cursor-pointer'
        } ${className}`}
        {...props}
      >
        {isLoading && <Loader2 className="w-4 h-4 animate-spin shrink-0" />}
        {!isLoading && leftIcon && <span className="shrink-0">{leftIcon}</span>}
        {children && <span>{children}</span>}
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </motion.button>
    )
  }
)

Button.displayName = 'Button'
export default Button
