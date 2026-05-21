import type { RACIEntry } from '../types/bundle'

interface Props {
  entries: RACIEntry[]
}

export default function RACIMatrix({ entries }: Props) {
  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-slate-900 mb-4">RACI Matrix</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 px-3 font-medium text-gray-600">Role</th>
              <th className="text-left py-2 px-3 font-medium text-gray-600">Responsible</th>
              <th className="text-left py-2 px-3 font-medium text-gray-600">Accountable</th>
              <th className="text-left py-2 px-3 font-medium text-gray-600">Consulted</th>
              <th className="text-left py-2 px-3 font-medium text-gray-600">Informed</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry, idx) => (
              <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2 px-3 font-medium">{entry.role}</td>
                <td className="py-2 px-3">{entry.responsible}</td>
                <td className="py-2 px-3">{entry.accountable}</td>
                <td className="py-2 px-3 text-gray-600">{entry.consulted}</td>
                <td className="py-2 px-3 text-gray-600">{entry.informed}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
