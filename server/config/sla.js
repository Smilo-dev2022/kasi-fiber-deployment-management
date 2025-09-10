// SLA configuration and helpers

const DEFAULT_ACK_HOURS_BY_TYPE = {
  cac_check: 4,
  stringing: 8,
  installation: 8,
  testing: 8,
  maintenance: 4,
  documentation: 12,
  other: 12
};

const DEFAULT_COMPLETION_HOURS_BY_TYPE = {
  cac_check: 24,
  stringing: 72,
  installation: 48,
  testing: 24,
  maintenance: 24,
  documentation: 24,
  other: 48
};

const PRIORITY_MULTIPLIERS = {
  critical: 0.5,
  high: 0.8,
  medium: 1.0,
  low: 1.2
};

function computeSlaSettings(taskType, priority = 'medium') {
  const baseAck = DEFAULT_ACK_HOURS_BY_TYPE[taskType] ?? 12;
  const baseCompletion = DEFAULT_COMPLETION_HOURS_BY_TYPE[taskType] ?? 48;
  const multiplier = PRIORITY_MULTIPLIERS[priority] ?? 1.0;

  const ackHours = Math.max(1, Math.round(baseAck * multiplier));
  const completionHours = Math.max(1, Math.round(baseCompletion * multiplier));

  return { ackHours, completionHours };
}

module.exports = {
  computeSlaSettings,
  DEFAULT_ACK_HOURS_BY_TYPE,
  DEFAULT_COMPLETION_HOURS_BY_TYPE,
  PRIORITY_MULTIPLIERS
};

