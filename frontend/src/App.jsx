import { useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

export default function App() {
  const [incidents, setIncidents] = useState([])

  async function loadIncidents() {
    const res = await fetch(`${API}/api/v1/incidents`, { headers: { 'X-Role': 'sre' } })
    const data = await res.json()
    setIncidents(data.items || [])
  }

  async function seed() {
    await fetch(`${API}/api/v1/demo/seed`, { method: 'POST', headers: { 'X-Role': 'sre' } })
    loadIncidents()
  }

  async function triage(id) {
    await fetch(`${API}/api/v1/incidents/${id}/triage`, { method: 'POST', headers: { 'X-Role': 'sre' } })
    loadIncidents()
  }

  useEffect(() => { loadIncidents() }, [])

  return (
    <div className="page">
      <header className="hero">
        <div>
          <h1>ActionOps AI</h1>
          <p>Permissioned AI issue triage and recovery for product deployments.</p>
        </div>
        <button onClick={seed}>Seed demo incident</button>
      </header>

      <section className="grid">
        <div className="panel stats">
          <div><strong>{incidents.length}</strong><span>Incidents</span></div>
          <div><strong>{incidents.filter(i => i.status === 'recovered').length}</strong><span>Recovered</span></div>
          <div><strong>{incidents.filter(i => i.status === 'awaiting_approval').length}</strong><span>Awaiting approval</span></div>
        </div>

        <div className="panel">
          <h2>Triage Queue</h2>
          <div className="list">
            {incidents.map(incident => (
              <div className="card" key={incident.id}>
                <div className="card-head">
                  <div>
                    <h3>{incident.title}</h3>
                    <p>{incident.service} · {incident.environment} · {incident.status}</p>
                  </div>
                  <button onClick={() => triage(incident.id)}>Triage</button>
                </div>
                <p>{incident.triage_summary || 'Awaiting triage'}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
