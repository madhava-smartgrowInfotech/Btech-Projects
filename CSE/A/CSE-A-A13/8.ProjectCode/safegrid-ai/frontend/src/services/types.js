/**
 * Data contracts mirrored from the backend (backend/app/models, backend/app/safety/models.py).
 * Plain JSDoc so editors give completion without a TypeScript build step.
 *
 * @typedef {"charge_battery"|"discharge_battery"|"import_power"|"export_power"|"curtail_generation"|"shift_load"|"idle"} ActionType
 *
 * @typedef {Object} EnergyAction
 * @property {string} agent_id
 * @property {ActionType} action_type
 * @property {number} power_kw
 * @property {number} duration_minutes
 * @property {string|null} target_node
 * @property {string[]} reason_codes
 * @property {number} confidence
 *
 * @typedef {"approved"|"projected"|"rejected"} ShieldStatus
 *
 * @typedef {Object} Violation
 * @property {string} code
 * @property {string} component
 * @property {number} requested
 * @property {number} allowed
 * @property {string} unit
 * @property {string} message
 *
 * @typedef {Object} ShieldDecision
 * @property {ShieldStatus} status
 * @property {EnergyAction} requested_action
 * @property {EnergyAction|null} validated_action
 * @property {Violation[]} violations
 * @property {{field:string, from:number, to:number, reason:string[]}[]} corrections
 * @property {{name:string, passed:boolean|null}[]} checks
 * @property {number} requested_power_kw
 * @property {number} safe_power_kw
 *
 * @typedef {Object} AgentRecord
 * @property {string} agent_id
 * @property {string} node_id
 * @property {EnergyAction} proposal
 * @property {string} decision_source  llm | mock | fallback | baseline | injected | operator
 * @property {number} latency_ms
 * @property {string|null} fallback_reason
 * @property {ShieldDecision} shield
 * @property {Object} explanation
 * @property {number} executed_power_kw
 */
export { ACTION_LABEL, SOURCE_LABEL } from '../lib/format'
