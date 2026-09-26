import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, selectModelFeatures } from './api'

describe('prediction API contract', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('keeps only recognized model features in the prediction payload', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)
    const sample = { stay_id: 11111111, age: 72, heart_rate: null, mortality: 0, long_stay: 1 }

    await api.predict('mortality', sample, ['age', 'heart_rate'])

    const [, init] = fetchMock.mock.calls[0]
    expect(JSON.parse(init.body)).toEqual({
      task: 'mortality',
      features: { age: 72, heart_rate: null },
    })
  })

  it('omits malformed values as well as unknown fields', () => {
    expect(selectModelFeatures({ age: 47, gender_male: '1', mortality: 0 }, ['age', 'gender_male'])).toEqual({ age: 47 })
  })
})