import type { Risk } from '../types/bundle'

interface Props {
  risks: Risk[]
}

function riskColor(probability: string, impact: string): string {
  const p = probability.toLowerCase()
  const i = impact.toLowerCase()
  if (p === 'high' || i === 'high') return 'bg-red-50 border-red-200'
  if (p === 'medium' || i === 'medium') return 'bg-yellow-50 border-yellow-200'
  return 'bg-green-50 border-green-200'
}

function badgeColor(level: string): string {
  switch (level.toLowerCase()) {
    case 'high': return 'bg-red-100 text-red-800'
    case 'medium': return 'bg-yellow-100 text-yellow-800'
    case 'low': return 'bg-green-100 text-green-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

export default function RiskBoard({ risks }: Props) {
  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Risk Register</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {risks.map((risk, idx) => (
          <div
            key={idx}
            className={`rounded-lg border p-4 ${riskColor(risk.probability, risk.impact)}`}
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-medium text-gray-900">{risk.description}</h3>
              <div className="flex gap-2 ml-2">
                <span className={`text-xs px-2 py-1 rounded-full ${badgeColor(risk.probability)}`}>
                  {risk.probability}
                </span>
                <span className={`text-xs px-2 py-1 rounded-full ${badgeColor(risk.impact)}`}>
                  {risk.impact}
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-2">
              <span className="font-medium">Mitigation:</span> {risk.mitigation}
            </p>
            <p className="text-sm text-gray-500">
              <span className="font-medium">Owner:</span> {risk.owner}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
