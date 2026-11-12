import React, { forwardRef } from 'react'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  accent?: 'cerulean' | 'rose'
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      accent = 'cerulean',
      className = '',
      id,
      disabled,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined)

    const focusBorder =
      accent === 'rose'
        ? 'focus:border-neonrose focus:ring-2 focus:ring-neonrose/20'
        : 'focus:border-cerulean focus:ring-2 focus:ring-cerulean/20'

    return (
      <div className="w-full flex flex-col space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="text-xs font-medium text-jet-300">
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3.5 text-jet-400 pointer-events-none flex items-center">
              {leftIcon}
            </div>
          )}

          <input
            id={inputId}
            ref={ref}
            disabled={disabled}
            className={`w-full rounded-xl py-2.5 text-sm bg-jet-950/80 border text-jet-100 placeholder-jet-500 transition-all duration-200 outline-none backdrop-blur-md ${
              leftIcon ? 'pl-10' : 'pl-3.5'
            } ${rightIcon ? 'pr-10' : 'pr-3.5'} ${
              error
                ? 'border-neonrose/70 focus:border-neonrose focus:ring-2 focus:ring-neonrose/25'
                : `border-white/10 ${focusBorder} hover:border-white/20`
            } ${disabled ? 'opacity-50 cursor-not-allowed bg-jet-950/40' : ''} ${className}`}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3.5 text-jet-400 pointer-events-none flex items-center">
              {rightIcon}
            </div>
          )}
        </div>

        {error && <span className="text-xs text-neonrose font-medium mt-0.5">{error}</span>}
        {!error && helperText && <span className="text-xs text-jet-400 mt-0.5">{helperText}</span>}
      </div>
    )
  }
)

Input.displayName = 'Input'
export default Input
