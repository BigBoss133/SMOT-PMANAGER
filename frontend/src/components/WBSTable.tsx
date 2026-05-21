import type { WBSTask } from '../types/bundle'

interface Props {
  tasks: WBSTask[]
}

export default function WBSTable({ tasks }: Props) {
  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Work Breakdown Structure</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 px-3 font-medium text-gray-600">ID</th>
              <th className="text-left py-2 px-3 font-medium text-gray-600">Name</th>
              <th className="text-left py-2 px-3 font-medium text-gray-600">Duration (days)</th>
              <th className="text-left py-2 px-3 font-medium text-gray-600">Dependencies</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2 px-3 font-mono text-blue-600">{task.id}</td>
                <td className="py-2 px-3">{task.name}</td>
                <td className="py-2 px-3">{task.duration_days ?? '-'}</td>
                <td className="py-2 px-3 text-gray-500">
                  {task.dependencies.length > 0 ? task.dependencies.join(', ') : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
