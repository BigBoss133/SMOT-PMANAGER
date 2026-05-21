export interface WBSTask {
  id: string;
  name: string;
  duration_days: number | null;
  dependencies: string[];
}

export interface RACIEntry {
  role: string;
  responsible: string;
  accountable: string;
  consulted: string;
  informed: string;
}

export interface Risk {
  description: string;
  probability: string;
  impact: string;
  mitigation: string;
  owner: string;
}

export interface BudgetItem {
  name: string;
  estimated_cost: number;
  actual_cost: number;
}

export interface Budget {
  items: BudgetItem[];
  total: number;
}

export interface BundleData {
  project_name: string;
  wbs: WBSTask[];
  raci: RACIEntry[];
  risks: Risk[];
  budget: Budget;
}
