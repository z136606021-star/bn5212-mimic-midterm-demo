Object.defineProperty(window, 'matchMedia', { writable: true, value: () => ({ matches: false, addListener: () => {}, removeListener: () => {}, addEventListener: () => {}, removeEventListener: () => {}, dispatchEvent: () => false }) })
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import App from './App.vue'
import { api } from './api'
vi.mock('./api', () => ({ api: { tasks: vi.fn(), summary: vi.fn(), predict: vi.fn() } }))
const mocked = vi.mocked(api)

const features = [
  'age',
  'gender_male',
  'heart_rate',
  'resp_rate',
  'temperature',
  'spo2',
  'sbp',
  'dbp',
  'map',
  'creatinine',
  'glucose',
  'sodium',
  'potassium',
  'hemoglobin',
  'wbc',
  'platelets',
  'bicarbonate',
  'bun',
]

const metric = {
  auroc: .8,
  auprc: .4,
  f1: .3,
  positive_rate: .1,
  test_samples: 10,
  sensitivity: .5,
  specificity: .9,
  status: 'preliminary_demo',
}

const tasks = [
  { id: 'mortality', title: 'In-hospital mortality', question: 'q', label: 'l', window: '24h', type: 'prediction' },
  { id: 'long_stay', title: 'Prolonged ICU stay', question: 'q', label: 'l', window: '24h', type: 'prediction' },
  { id: 'readmission', title: '30-day readmission', question: 'q', label: 'l', window: '24h', type: 'prediction' },
  { id: 'missingness', title: 'Missing-data robustness', question: 'q', label: 'l', window: 'evaluation', type: 'robustness' },
]

const demoSample = {
  stay_id: 11111111,
  age: 72,
  gender_male: 1,
  heart_rate: 90,
  resp_rate: 18,
  temperature: 36.8,
  spo2: 97,
  sbp: null,
  dbp: null,
  map: 80,
  creatinine: 1.1,
  glucose: 120,
  sodium: 138,
  potassium: 4.2,
  hemoglobin: 12,
  wbc: 8,
  platelets: 200,
  bicarbonate: 24,
  bun: 18,
  mortality: 0,
  long_stay: 0,
  readmission: 0,
}

const robustness = ['mortality', 'long_stay'].flatMap((task) =>
  [0, .1, .25, .4, .6].map((mask_rate, index) => ({
    task,
    mask_rate,
    auroc: .8 - index * .02,
    auprc: .4,
    f1: .3,
  })),
)

const summary = {
  cohort: { stays: 10, patients: 8, window_hours: 24 },
  features,
  missingness: { temperature: .2 },
  tasks: { mortality: metric, long_stay: metric, readmission: metric },
  robustness,
  demo_samples: [demoSample],
}

async function mountDashboard(customSummary = summary) {
  mocked.tasks.mockResolvedValue({ tasks, disclaimer: '' })
  mocked.summary.mockResolvedValue(customSummary as any)
  const wrapper = mount(App)
  await vi.waitFor(() => expect(wrapper.text()).toContain('First 24-hour values'))
  return wrapper
}

describe('dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows grouped selected-case values without identifiers or outcomes', async () => {
    const wrapper = await mountDashboard()
    const values = wrapper.get('.case-groups').text()

    expect(values).toContain('Demographics')
    expect(values).toContain('Heart rate')
    expect(values).toContain('90 bpm')
    expect(values).toContain('Not recorded')
    expect(values).not.toContain('11111111')
    expect(values).not.toContain('readmission')
  })

  it('ties prediction contributions to the selected case value', async () => {
    mocked.predict.mockResolvedValue({
      task: 'mortality',
      task_title: 'In-hospital mortality',
      ranking_score: .72,
      risk_band: 'higher',
      source: 'manual teaching input',
      top_contributors: [{ feature: 'age', direction: 'higher', contribution: .42 }],
      disclaimer: 'Educational demo.',
    })
    const wrapper = await mountDashboard()

    const runButton = wrapper.findAll('button').find((button) => button.text().includes('Run teaching prediction'))
    await runButton!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Case value: 72 years')
    expect(wrapper.text()).toContain('Pushed signal higher · +0.42')
    expect(wrapper.text()).toContain('not a probability or a clinical decision')
  })

  it('masks recorded fields deterministically and rescores both robustness tasks', async () => {
    mocked.predict.mockImplementation(async (task) => ({
      task,
      task_title: task,
      ranking_score: task === 'mortality' ? .61 : .48,
      risk_band: 'middle',
      source: 'manual teaching input',
      top_contributors: [],
      disclaimer: 'Educational demo.',
    }))
    const wrapper = await mountDashboard()

    const missingnessTrack = wrapper.findAll('.track').find((card) => card.text().includes('Missing-data robustness'))
    await missingnessTrack!.trigger('click')
    await wrapper.findAll('.mask-rates button').find((button) => button.text() === '25.0%')!.trigger('click')

    expect(wrapper.text()).toContain('4 fields masked')
    expect(wrapper.text()).not.toContain('Select a prediction track')
    expect(wrapper.text()).toContain('does not replay the separate missing-indicator coefficients')

    const runButton = wrapper.findAll('button').find((button) => button.text().includes('Run mask-and-rescore'))
    await runButton!.trigger('click')
    await flushPromises()

    expect(mocked.predict).toHaveBeenCalledTimes(4)
    expect(mocked.predict.mock.calls.map(([task]) => task)).toEqual([
      'mortality',
      'mortality',
      'long_stay',
      'long_stay',
    ])
    const baseline = mocked.predict.mock.calls[0][1]
    const masked = mocked.predict.mock.calls[1][1]
    const newlyMasked = features.filter(
      (feature) => typeof baseline[feature] === 'number' && masked[feature] === null,
    )
    expect(newlyMasked).toHaveLength(4)
    expect(wrapper.text()).toContain('Case-level score comparison')
    expect(wrapper.text()).toContain('Unmasked')
    expect(wrapper.text()).toContain('Masked')
  })

  it('shows a useful state when no held-out cases are available', async () => {
    mocked.tasks.mockResolvedValue({ tasks, disclaimer: '' })
    mocked.summary.mockResolvedValue({ ...summary, demo_samples: [] } as any)
    const wrapper = mount(App)
    await vi.waitFor(() => expect(wrapper.text()).toContain('This summary has no held-out demo case'))
    expect(wrapper.find('.sample-select').exists()).toBe(false)
  })
})
