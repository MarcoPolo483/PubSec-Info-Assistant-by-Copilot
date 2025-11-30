import { useState } from 'react'
import QueryInterface from './components/QueryInterface'
import Header from './components/Header'
import './App.css'

function App() {
  const [tenantId, setTenantId] = useState('default')

  return (
    <div className="app">
      <Header tenantId={tenantId} onTenantChange={setTenantId} />
      <main className="main-content">
        <QueryInterface tenantId={tenantId} />
      </main>
      <footer className="footer">
        <p>PubSec Info Assistant v0.1.0 | Enterprise RAG System</p>
        <p>Multi-tenant • SOC2 Ready • WCAG 2.1 AA</p>
      </footer>
    </div>
  )
}

export default App
