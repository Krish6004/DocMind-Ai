import React, { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  UploadCloud,
  FileText,
  Trash2,
  Search,
  Layers,
  HardDrive,
  FileCode,
  Loader2,
  Plus,
} from 'lucide-react'
import Button from '@/components/common/Button'
import Badge from '@/components/common/Badge'
import Card from '@/components/common/Card'
import { useDocuments } from '@/hooks/useDocuments'
import DocumentService from '@/services/documentService'
import { useQueryClient } from '@tanstack/react-query'
import { useToast } from '@/hooks/useToast'
import type { DocumentItem } from '@/types'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export const DocumentsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const { data: docData, isLoading } = useDocuments()
  const { success, error: toastError } = useToast()

  const [searchTerm, setSearchTerm] = useState('')
  const [selectedFormat, setSelectedFormat] = useState<string>('all')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<string>('')
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  const docs = docData?.documents || []

  // Filter and search
  const filteredDocs = docs.filter((doc) => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFormat =
      selectedFormat === 'all' ||
      doc.file_type.toLowerCase() === selectedFormat.toLowerCase()
    return matchesSearch && matchesFormat
  })

  // Batch and single upload handler
  const handleFilesUpload = async (fileList: FileList | File[]) => {
    const filesArray = Array.from(fileList).filter((f) => {
      const ext = '.' + f.name.split('.').pop()?.toLowerCase()
      return ['.pdf', '.docx', '.txt', '.md'].includes(ext)
    })

    if (filesArray.length === 0) {
      toastError('Invalid File Format', 'Please upload valid .pdf, .docx, .txt, or .md documents.')
      return
    }

    setIsUploading(true)
    let successCount = 0
    let failureCount = 0

    for (let i = 0; i < filesArray.length; i++) {
      const file = filesArray[i]
      const currentDocNum = i + 1
      const totalDocs = filesArray.length
      const prefix = totalDocs > 1 ? `[${currentDocNum}/${totalDocs}] ` : ''

      setUploadProgress(0)
      setUploadStatus(`${prefix}Uploading ${file.name}...`)

      try {
        const res = await DocumentService.uploadDocument(file, (percent) => {
          setUploadProgress(percent)
          if (percent >= 100) {
            setUploadStatus(`${prefix}Processing & indexing ${file.name}...`)
          } else {
            setUploadStatus(`${prefix}Uploading ${file.name}: ${percent}%`)
          }
        })
        successCount++
        queryClient.invalidateQueries({ queryKey: ['documents-list'] })
        queryClient.invalidateQueries({ queryKey: ['backend-health'] })
        if (totalDocs === 1) {
          success('Document Indexed', `${res.filename} was successfully processed and chunked.`)
        }
      } catch (err: any) {
        failureCount++
        toastError(`Failed: ${file.name}`, err.message || 'Error processing document.')
      }
    }

    if (filesArray.length > 1) {
      if (successCount > 0) {
        success(
          'Upload Complete',
          `Successfully processed and indexed ${successCount} of ${filesArray.length} documents.`
        )
      }
    }

    setIsUploading(false)
    setUploadProgress(null)
    setUploadStatus('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // Delete handler
  const handleDelete = async (doc: DocumentItem) => {
    if (!window.confirm(`Delete "${doc.filename}" and purge all its vector chunks?`)) return
    setDeletingId(doc.id)
    try {
      await DocumentService.deleteDocument(doc.id)
      success('Document Purged', `${doc.filename} removed from knowledge base.`)
      queryClient.invalidateQueries({ queryKey: ['documents-list'] })
    } catch (err: any) {
      toastError('Deletion Failed', err.message || 'Error purging document.')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Hidden File Input with multiple selection */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            handleFilesUpload(e.target.files)
          }
        }}
        accept=".pdf,.docx,.txt,.md"
        multiple
        className="hidden"
      />

      {/* Header and Summary */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/[0.06]">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <HardDrive className="w-5 h-5 text-cerulean-light" />
            <span>Document Vault & Knowledge Base</span>
          </h1>
          <p className="text-xs text-jet-400 mt-1">
            Manage files indexed into SQLite, dense vector stores, and sparse BM25 indices.
          </p>
        </div>

        <Button
          variant="cerulean"
          size="md"
          leftIcon={isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          disabled={isUploading}
          onClick={() => fileInputRef.current?.click()}
          className="shadow-glow-cerulean/30"
        >
          {isUploading ? (uploadStatus || 'Ingesting Documents...') : 'Upload Documents'}
        </Button>
      </div>

      {/* Dropzone Panel */}
      <div
        onClick={() => !isUploading && fileInputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          if (!isUploading && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFilesUpload(e.dataTransfer.files)
          }
        }}
        className={`rounded-2xl glass-panel p-6 border border-dashed transition-all text-center group bg-jet-950/40 ${
          isUploading
            ? 'border-cerulean/50 cursor-wait'
            : 'border-white/15 hover:border-cerulean/50 cursor-pointer'
        }`}
      >
        {isUploading ? (
          <div className="py-2">
            <Loader2 className="w-8 h-8 animate-spin text-cerulean-light mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-white">
              {uploadStatus || 'Processing document...'}
            </h3>
            {uploadProgress !== null && uploadProgress > 0 && uploadProgress < 100 && (
              <div className="w-64 max-w-full mx-auto mt-3">
                <div className="w-full bg-jet-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-cerulean h-full transition-all duration-300"
                    style={{ width: `${Math.min(uploadProgress, 100)}%` }}
                  />
                </div>
              </div>
            )}
            <p className="text-xs text-jet-400 mt-2">
              Generating semantic chunks and vector embeddings. Please wait...
            </p>
          </div>
        ) : (
          <>
            <div className="w-12 h-12 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center mx-auto mb-3 text-cerulean-light group-hover:scale-105 transition-transform">
              <UploadCloud className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-white">
              Drop documents here, or <span className="text-cerulean-light underline underline-offset-2">browse files</span>
            </h3>
            <p className="text-xs text-jet-400 mt-1">
              Supports PDF, DOCX, TXT, and Markdown files up to 50 MB.
            </p>
          </>
        )}
      </div>

      {/* Controls: Search & Filter Tabs */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-jet-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search documents by name..."
            className="w-full pl-9 pr-3 py-2 text-xs rounded-xl bg-jet-950/80 border border-white/[0.08] text-white placeholder-jet-500 focus:outline-none focus:border-cerulean/50"
          />
        </div>

        {/* Filter Format Chips */}
        <div className="flex items-center space-x-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          {(
            [
              { id: 'all', label: 'All Files' },
              { id: 'pdf', label: 'PDF' },
              { id: 'docx', label: 'DOCX' },
              { id: 'txt', label: 'TXT' },
              { id: 'md', label: 'Markdown' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedFormat(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                selectedFormat === tab.id
                  ? 'bg-white/10 text-white border border-white/15'
                  : 'text-jet-400 hover:text-jet-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Documents List */}
      <div className="space-y-2.5">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-jet-400 flex items-center justify-center space-x-2">
            <Loader2 className="w-4 h-4 animate-spin text-cerulean-light" />
            <span>Loading documents from SQLite...</span>
          </div>
        ) : filteredDocs.length === 0 ? (
          <Card variant="default" className="py-12 text-center border-dashed border-white/10">
            <FileText className="w-8 h-8 text-jet-500 mx-auto mb-2 opacity-50" />
            <p className="text-xs font-semibold text-jet-200">No documents found</p>
            <p className="text-[11px] text-jet-400 mt-1 max-w-sm mx-auto">
              Upload your first PDF, DOCX, TXT, or Markdown document to start grounding queries in your data.
            </p>
          </Card>
        ) : (
          filteredDocs.map((doc, idx) => {
            const isDeleting = deletingId === doc.id
            const isMarkdown = doc.file_type === 'md'
            const formattedDate = doc.upload_timestamp
              ? new Date(doc.upload_timestamp).toLocaleDateString([], {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })
              : 'Indexed'

            return (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: idx * 0.02 }}
                className="p-4 rounded-xl glass-panel border border-white/[0.06] hover:border-white/15 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
              >
                {/* File Info */}
                <div className="flex items-center space-x-3.5 min-w-0">
                  <div className="w-9 h-9 rounded-xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center text-cerulean-light shrink-0">
                    {isMarkdown ? <FileCode className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
                  </div>

                  <div className="min-w-0">
                    <h3 className="text-xs sm:text-sm font-semibold text-white truncate group-hover:text-cerulean-light transition-colors">
                      {doc.filename}
                    </h3>
                    <div className="flex items-center space-x-2 text-[11px] font-mono text-jet-400 mt-0.5">
                      <span className="uppercase">{doc.file_type}</span>
                      <span>•</span>
                      <span>{formatBytes(doc.file_size)}</span>
                      <span>•</span>
                      <span className="flex items-center space-x-1 text-jet-300">
                        <Layers className="w-3 h-3 text-cerulean-light" />
                        <span>{doc.chunk_count} chunks</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Metadata & Actions */}
                <div className="flex items-center justify-between sm:justify-end space-x-4 shrink-0">
                  <div className="text-right hidden md:block">
                    <span className="text-[11px] text-jet-400 font-mono block">{formattedDate}</span>
                    <Badge variant="cerulean" size="sm" dot>
                      {doc.status}
                    </Badge>
                  </div>

                  <button
                    type="button"
                    disabled={isDeleting}
                    onClick={() => handleDelete(doc)}
                    className="p-2 rounded-lg text-jet-400 hover:text-neonrose hover:bg-neonrose/10 transition-colors disabled:opacity-50"
                    title="Purge document"
                  >
                    {isDeleting ? (
                      <Loader2 className="w-4 h-4 animate-spin text-neonrose" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </motion.div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default DocumentsPage
