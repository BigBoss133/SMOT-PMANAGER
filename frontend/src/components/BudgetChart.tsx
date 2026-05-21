import type { Budget } from '../types/bundle'

interface Props {
  budget: Budget
}

export default function BudgetChart({ budget }: Props) {
  const maxCost = Math.max(
    ...budget.items.map((i) => i.estimated_cost),
    budget.total
  )

  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Budget Overview</h2>
      <div className="space-y-4">
        {budget.items.map((item, idx) => (
          <div key={idx}>
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium">{item.name}</span>
              <span className="text-gray-600">
                ${item.estimated_cost.toLocaleString()}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-500 h-3 rounded-full transition-all"
                style={{ width: `${(item.estimated_cost / maxCost) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6 pt-4 border-t border-gray-200 flex justify-between items-center">
        <span className="font-semibold text-gray-900">Total Budget</span>
        <span className="text-2xl font-bold text-blue-600">
          ${budget.total.toLocaleString()}
        </span>
      </div>
    </div>
  )
}
