import React from 'react'

interface ProviderLogoProps {
  providerId: string
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

export const ProviderLogo: React.FC<ProviderLogoProps> = ({
  providerId,
  className = '',
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'w-5 h-5',
    md: 'w-7 h-7',
    lg: 'w-10 h-10',
  }[size]

  switch (providerId.toLowerCase()) {
    case 'gemini':
      return (
        <div className={`flex items-center justify-center shrink-0 ${sizeClasses} ${className}`}>
          <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
            <path
              d="M12 2C12 7.52285 7.52285 12 2 12C7.52285 12 12 16.4772 12 22C12 16.4772 16.4772 12 22 12C16.4772 12 12 7.52285 12 2Z"
              fill="url(#gemini-grad)"
            />
            <defs>
              <linearGradient id="gemini-grad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                <stop stopColor="#4E82EE" />
                <stop offset="0.5" stopColor="#9B72CB" />
                <stop offset="1" stopColor="#D96570" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      )

    case 'groq':
      return (
        <div className={`flex items-center justify-center shrink-0 rounded-lg bg-white/10 p-1 ${sizeClasses} ${className}`}>
          <svg viewBox="0 0 24 24" fill="none" className="w-full h-full" stroke="currentColor">
            <path
              d="M13 2L3 14H12L11 22L21 10H12L13 2Z"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-amber-400"
              fill="rgba(251, 191, 36, 0.2)"
            />
          </svg>
        </div>
      )

    case 'openai':
      return (
        <div className={`flex items-center justify-center shrink-0 ${sizeClasses} ${className}`}>
          <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-white">
            <path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813v6.7227zm1.1458-1.7849l2.547-1.4678 2.547 1.4678v2.9356l-2.547 1.4678-2.547-1.4678z" />
          </svg>
        </div>
      )

    case 'anthropic':
      return (
        <div className={`flex items-center justify-center shrink-0 ${sizeClasses} ${className}`}>
          <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-amber-500">
            <path d="M13.827 3.02H18.9L12.553 20.98H7.48L13.827 3.02ZM5.1 14.98H10.18L7.64 7.82L5.1 14.98Z" />
          </svg>
        </div>
      )

    case 'ollama':
      return (
        <div className={`flex items-center justify-center shrink-0 rounded-lg bg-white/5 border border-white/10 p-1 ${sizeClasses} ${className}`}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="w-full h-full text-emerald-400">
            <rect x="2" y="4" width="20" height="16" rx="4" strokeWidth="1.8" />
            <path d="M7 15L10 12L7 9" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            <line x1="13" y1="15" x2="17" y2="15" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        </div>
      )

    default:
      return (
        <div className={`flex items-center justify-center shrink-0 rounded-lg bg-white/5 p-1 ${sizeClasses} ${className}`}>
          <span className="text-xs font-mono font-bold text-white">AI</span>
        </div>
      )
  }
}

export default ProviderLogo

