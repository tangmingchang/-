import { ButtonHTMLAttributes, ReactNode } from 'react'
import { Loader2 } from 'lucide-react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'text' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  children: ReactNode
}

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  className = '',
  children,
  ...props
}: ButtonProps) {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'
  
  const variants = {
    primary: 'bg-gradient-creative dark:bg-gradient-to-r dark:from-indigo-600 dark:via-purple-600 dark:to-purple-700 text-white hover:shadow-lg dark:hover:from-indigo-500 dark:hover:via-purple-500 dark:hover:to-purple-600 focus:ring-primary-500 dark:focus:ring-purple-500 active:scale-95',
    secondary: 'bg-white/50 dark:bg-dark-card border border-paper-300 dark:border-dark-border text-gold dark:text-white hover:bg-white/70 dark:hover:bg-dark-card/80 focus:ring-primary-500 dark:focus:ring-purple-500 active:scale-95',
    text: 'text-gold dark:text-slate-300 hover:bg-white/50 dark:hover:bg-white/10 focus:ring-primary-500 dark:focus:ring-purple-500',
    danger: 'bg-red-500 text-white hover:bg-red-600 focus:ring-red-500 active:scale-95',
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  }

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
      )}
      {children}
    </button>
  )
}











