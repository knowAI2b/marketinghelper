/** Intent module output (POST /intent) */
export interface IntentOutput {
  demand_summary: string
  intent_type: string
  intent_breakdown?: string[] | null
  intent_breakdown_candidates?: string[] | null
  slots: Record<string, unknown>
  needs_clarification: boolean
  clarification_question?: string | null
  suggested_agents: string[]
  user_can_edit_task_breakdown?: boolean
  missing_slots?: string[] | null
  ambiguous_intent?: string | null
}

/** Fulfillability check result (POST /fulfillability) */
export interface FulfillabilityResult {
  can_fulfill: boolean
  reason?: string | null
  reason_detail?: string | null
  message_to_user?: string | null
  alternative?: string | null
  transfer_to_human?: boolean
  blocked_step?: string | null
}

/** Planner step */
export interface PlanStep {
  step_id: string
  agent: string
  input_summary: string
  depends_on: string[]
  acceptance_criteria: string
}

/** Planner run response */
export interface PlannerResult {
  plan?: { steps: PlanStep[] }
  past_steps?: Array<[PlanStep, { agent: string; output: string; step_id?: string }]>
  response?: string
}

export type AccountContext = Record<string, unknown>
