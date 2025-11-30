import { useState } from 'react'
import { Search, Loader2, AlertCircle, DollarSign, Clock } from 'lucide-react'
import axios from 'axios'
import './QueryInterface.css'

interface Citation {
  document_id: string
  chunk_id: string
  content: string
  title?: string
  author?: string
  source_url?: string
  relevance_score: number
}

interface QueryResponse {
  query: string
  answer: string
  citations: Citation[]
  retrieval_results: number
  cost: number
  tokens_used: { input: number; output: number; total: number }
  tenant_balance: number
  processing_time_ms: number
  cached: boolean
}

interface QueryInterfaceProps {
  tenantId: string
}

export default function QueryInterface({ tenantId }: QueryInterfaceProps) {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const result = await axios.post(
        `/api/v1/query`,
        null,
        {
          params: { query: query.trim(), top_k: 5, use_cache: true },
          headers: { 'X-Tenant-ID': tenantId },
        }
      )

      setResponse(result.data)
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          'Failed to process query. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="query-interface">
      <div className="query-section">
        <h2 className="section-title">Ask a Question</h2>
        <form onSubmit={handleSubmit} className="query-form">
          <div className="input-wrapper">
            <Search size={20} className="search-icon" aria-hidden="true" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your question..."
              className="query-input"
              disabled={loading}
              aria-label="Query input"
              autoFocus
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="submit-button"
            aria-label="Submit query"
          >
            {loading ? (
              <>
                <Loader2 size={20} className="spinner" />
                Processing...
              </>
            ) : (
              'Search'
            )}
          </button>
        </form>
      </div>

      {error && (
        <div className="error-message" role="alert">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {response && (
        <div className="results-section">
          <div className="answer-card">
            <h3 className="answer-title">Answer</h3>
            <p className="answer-text">{response.answer}</p>

            <div className="metadata">
              <div className="metadata-item">
                <Clock size={16} />
                <span>
                  {response.processing_time_ms.toFixed(0)}ms
                  {response.cached && ' (cached)'}
                </span>
              </div>
              <div className="metadata-item">
                <DollarSign size={16} />
                <span>${response.cost.toFixed(4)}</span>
              </div>
              <div className="metadata-item">
                <span>
                  {response.tokens_used.total} tokens ({response.tokens_used.input} in,{' '}
                  {response.tokens_used.output} out)
                </span>
              </div>
              <div className="metadata-item">
                <span>Balance: ${response.tenant_balance.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {response.citations.length > 0 && (
            <div className="citations-card">
              <h3 className="citations-title">
                Sources ({response.citations.length})
              </h3>
              <div className="citations-list">
                {response.citations.map((citation, index) => (
                  <div key={citation.chunk_id} className="citation-item">
                    <div className="citation-header">
                      <span className="citation-number">[{index + 1}]</span>
                      <span className="citation-title">
                        {citation.title || 'Untitled Document'}
                      </span>
                      <span className="citation-score">
                        {(citation.relevance_score * 100).toFixed(0)}% match
                      </span>
                    </div>
                    {citation.author && (
                      <div className="citation-author">By: {citation.author}</div>
                    )}
                    <div className="citation-content">{citation.content}</div>
                    {citation.source_url && (
                      <a
                        href={citation.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="citation-link"
                      >
                        View Source →
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
