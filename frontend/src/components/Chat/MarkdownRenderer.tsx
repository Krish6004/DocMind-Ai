import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ExternalLink } from 'lucide-react'
import CodeBlock from './CodeBlock'

interface MarkdownRendererProps {
  content: string
  onCitationClick?: (sourceNum: number) => void
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = React.memo(
  ({ content, onCitationClick }) => {
    // Process markdown to make citations interactive if applicable
    const processedContent = content

    return (
      <div className="prose prose-invert max-w-none text-xs sm:text-sm text-jet-200 leading-relaxed space-y-3 break-words">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Code Blocks & Inline Code
            code({ className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '')
              const isInline = !match && !String(children).includes('\n')
              const codeString = String(children).replace(/\n$/, '')

              if (!isInline) {
                return (
                  <CodeBlock
                    language={match ? match[1] : 'text'}
                    value={codeString}
                  />
                )
              }

              // Check if inline code looks like a citation [1] or [2]
              const citationMatch = /^\[(\d+)\]$/.exec(codeString.trim())
              if (citationMatch && onCitationClick) {
                const num = parseInt(citationMatch[1], 10)
                return (
                  <button
                    type="button"
                    onClick={() => onCitationClick(num)}
                    className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-cerulean/20 text-cerulean-light border border-cerulean/40 hover:bg-cerulean/30 transition-colors mx-0.5"
                    title={`View Citation Source [${num}]`}
                  >
                    [{num}]
                  </button>
                )
              }

              return (
                <code
                  className="px-1.5 py-0.5 rounded-md bg-white/[0.08] text-cerulean-light font-mono text-[12px] border border-white/[0.05]"
                  {...props}
                >
                  {children}
                </code>
              )
            },

            // Headings
            h1: ({ children }) => (
              <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight mt-5 mb-2 pb-1 border-b border-white/[0.08]">
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-base sm:text-lg font-bold text-jet-100 tracking-tight mt-4 mb-2">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-sm sm:text-base font-semibold text-jet-100 mt-3 mb-1.5">
                {children}
              </h3>
            ),

            // Paragraphs
            p: ({ children }) => (
              <p className="leading-relaxed text-jet-200 my-2">
                {children}
              </p>
            ),

            // Blockquotes
            blockquote: ({ children }) => (
              <blockquote className="border-l-2 border-cerulean pl-3.5 py-1 my-3 bg-cerulean/[0.04] rounded-r-lg text-jet-300 italic text-xs sm:text-sm">
                {children}
              </blockquote>
            ),

            // Lists
            ul: ({ children }) => (
              <ul className="list-disc list-outside ml-4 space-y-1 text-jet-200 my-2">
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal list-outside ml-4 space-y-1 text-jet-200 my-2">
                {children}
              </ol>
            ),
            li: ({ children }) => (
              <li className="leading-relaxed pl-1">
                {children}
              </li>
            ),

            // Tables
            table: ({ children }) => (
              <div className="overflow-x-auto my-4 rounded-xl border border-white/10 bg-jet-950/60 shadow-glass-sm">
                <table className="w-full text-left text-xs border-collapse">
                  {children}
                </table>
              </div>
            ),
            thead: ({ children }) => (
              <thead className="bg-jet-900 border-b border-white/10 text-jet-200 uppercase font-mono text-[10px] tracking-wider">
                {children}
              </thead>
            ),
            tbody: ({ children }) => (
              <tbody className="divide-y divide-white/[0.05] text-jet-300">
                {children}
              </tbody>
            ),
            tr: ({ children }) => (
              <tr className="hover:bg-white/[0.02] transition-colors">
                {children}
              </tr>
            ),
            th: ({ children }) => (
              <th className="px-3.5 py-2.5 font-semibold text-jet-200">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="px-3.5 py-2">
                {children}
              </td>
            ),

            // Links
            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-1 text-cerulean-light underline underline-offset-2 hover:text-white transition-colors"
              >
                <span>{children}</span>
                <ExternalLink className="w-3 h-3 inline ml-0.5 opacity-70" />
              </a>
            ),

            // Horizontal Rule
            hr: () => <hr className="border-white/[0.08] my-4" />,
          }}
        >
          {processedContent}
        </ReactMarkdown>
      </div>
    )
  }
)

MarkdownRenderer.displayName = 'MarkdownRenderer'

export default MarkdownRenderer

