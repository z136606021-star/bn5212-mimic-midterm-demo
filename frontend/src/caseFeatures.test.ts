import { describe, expect, it } from 'vitest'
import { CASE_FEATURES, deterministicMaskedFeatures, withMaskedFeatures } from './caseFeatures'

describe('case feature masking', () => {
  const sample = Object.fromEntries(
    CASE_FEATURES.map(({ key }, index) => [key, index === 3 ? null : index + 1]),
  )
  const modelFeatures = CASE_FEATURES.map(({ key }) => key)

  it('returns the same recorded fields for the same case and rate', () => {
    const first = deterministicMaskedFeatures(sample, modelFeatures, .4, 2)
    const second = deterministicMaskedFeatures(sample, modelFeatures, .4, 2)

    expect([...first]).toEqual([...second])
    expect(first.size).toBe(Math.round((CASE_FEATURES.length - 1) * .4))
    expect(first.has('resp_rate')).toBe(false)
  })

  it('sets only selected fields to null without mutating the source case', () => {
    const maskedKeys = new Set(['age', 'heart_rate'])
    const masked = withMaskedFeatures(sample, maskedKeys)

    expect(masked.age).toBeNull()
    expect(masked.heart_rate).toBeNull()
    expect(masked.gender_male).toBe(sample.gender_male)
    expect(sample.age).toBe(1)
  })
})
