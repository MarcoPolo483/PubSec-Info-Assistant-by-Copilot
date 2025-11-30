import { Building2 } from 'lucide-react'
import './Header.css'

interface HeaderProps {
  tenantId: string
  onTenantChange: (tenantId: string) => void
}

export default function Header({ tenantId, onTenantChange }: HeaderProps) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <Building2 size={32} className="logo-icon" aria-hidden="true" />
          <h1 className="title">PubSec Info Assistant</h1>
        </div>
        <div className="header-right">
          <label htmlFor="tenant-select" className="tenant-label">
            Tenant:
          </label>
          <select
            id="tenant-select"
            value={tenantId}
            onChange={(e) => onTenantChange(e.target.value)}
            className="tenant-select"
            aria-label="Select tenant"
          >
            <option value="default">Default</option>
            <option value="agency-a">Agency A</option>
            <option value="agency-b">Agency B</option>
            <option value="agency-c">Agency C</option>
          </select>
        </div>
      </div>
    </header>
  )
}
