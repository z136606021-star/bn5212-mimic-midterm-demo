import type { DemoSample, FeatureValue } from './api'

export type FeatureGroupId = 'demographics' | 'vitals' | 'labs'

export type CaseFeature = {
  key: string
  label: string
  group: FeatureGroupId
  unit?: string
}

export const FEATURE_GROUPS: { id: FeatureGroupId; label: string; subtitle: string }[] = [
  { id: 'demographics', label: 'Demographics', subtitle: '人口信息' },
  { id: 'vitals', label: 'Vital signs', subtitle: '生命体征' },
  { id: 'labs', label: 'Laboratory results', subtitle: '实验室结果' },
]

export const CASE_FEATURES: CaseFeature[] = [
  { key: 'age', label: 'Age', group: 'demographics', unit: 'years' },
  { key: 'gender_male', label: 'Sex', group: 'demographics' },
  { key: 'heart_rate', label: 'Heart rate', group: 'vitals', unit: 'bpm' },
  { key: 'resp_rate', label: 'Respiratory rate', group: 'vitals', unit: 'breaths/min' },
  { key: 'temperature', label: 'Temperature', group: 'vitals', unit: '°C' },
  { key: 'spo2', label: 'SpO₂', group: 'vitals', unit: '%' },
  { key: 'sbp', label: 'Systolic blood pressure', group: 'vitals', unit: 'mmHg' },
  { key: 'dbp', label: 'Diastolic blood pressure', group: 'vitals', unit: 'mmHg' },
  { key: 'map', label: 'Mean arterial pressure', group: 'vitals', unit: 'mmHg' },
  { key: 'creatinine', label: 'Creatinine', group: 'labs', unit: 'mg/dL' },
  { key: 'glucose', label: 'Glucose', group: 'labs', unit: 'mg/dL' },
  { key: 'sodium', label: 'Sodium', group: 'labs', unit: 'mmol/L' },
  { key: 'potassium', label: 'Potassium', group: 'labs', unit: 'mmol/L' },
  { key: 'hemoglobin', label: 'Hemoglobin', group: 'labs', unit: 'g/dL' },
  { key: 'wbc', label: 'White blood cells', group: 'labs', unit: 'K/µL' },
  { key: 'platelets', label: 'Platelets', group: 'labs', unit: 'K/µL' },
  { key: 'bicarbonate', label: 'Bicarbonate', group: 'labs', unit: 'mmol/L' },
  { key: 'bun', label: 'Blood urea nitrogen', group: 'labs', unit: 'mg/dL' },
]

export const featureByKey = new Map(CASE_FEATURES.map((feature) => [feature.key, feature]))

export function featureValue(sample: DemoSample | undefined, key: string): FeatureValue {
  const value = sample?.[key]
  return value === null || typeof value === 'number' ? value : null
}

export function formatFeatureValue(feature: CaseFeature, value: FeatureValue): string {
  if (value === null || !Number.isFinite(value)) return 'Not recorded'
  if (feature.key === 'gender_male') return value >= 0.5 ? 'Male' : 'Female'
  if (feature.key === 'age') return Math.round(value).toString()
  return Number.isInteger(value) ? value.toString() : value.toFixed(1)
}

function stableHash(value: string): number {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

export function deterministicMaskedFeatures(
  sample: DemoSample | undefined,
  modelFeatures: readonly string[],
  rate: number,
  caseIndex: number,
): Set<string> {
  if (!sample || rate <= 0) return new Set()
  const modelFeatureSet = new Set(modelFeatures)
  const recorded = CASE_FEATURES
    .filter(({ key }) => modelFeatureSet.has(key) && typeof sample[key] === 'number')
    .map(({ key }) => key)
  const count = Math.min(recorded.length, Math.round(recorded.length * rate))
  return new Set(
    recorded
      .map((key) => ({ key, order: stableHash(`${caseIndex}:${rate.toFixed(4)}:${key}`) }))
      .sort((left, right) => left.order - right.order || left.key.localeCompare(right.key))
      .slice(0, count)
      .map(({ key }) => key),
  )
}

export function withMaskedFeatures(sample: DemoSample, masked: ReadonlySet<string>): DemoSample {
  return Object.fromEntries(
    Object.entries(sample).map(([key, value]) => [key, masked.has(key) ? null : value]),
  )
}
