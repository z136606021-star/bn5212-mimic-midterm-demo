<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Layout,
  Progress,
  Row,
  Select,
  Spin,
  Statistic,
  Tag,
} from 'ant-design-vue'
import { api } from './api'
import type { Prediction, Summary, Task } from './api'
import {
  CASE_FEATURES,
  FEATURE_GROUPS,
  deterministicMaskedFeatures,
  featureByKey,
  featureValue,
  formatFeatureValue,
  withMaskedFeatures,
} from './caseFeatures'

const ROBUSTNESS_TASKS = ['mortality', 'long_stay'] as const
type RobustnessTask = (typeof ROBUSTNESS_TASKS)[number]
type RobustnessScore = { baseline: Prediction; masked: Prediction }

const tasks = ref<Task[]>([])
const summary = ref<Summary | null>(null)
const selected = ref('mortality')
const sample = ref(0)
const maskRate = ref(0.25)
const prediction = ref<Prediction | null>(null)
const robustnessScores = ref<Partial<Record<RobustnessTask, RobustnessScore>>>({})
const loading = ref(true)
const running = ref(false)
const error = ref('')

const task = computed(() => tasks.value.find((item) => item.id === selected.value))
const metric = computed(() => summary.value?.tasks[selected.value])
const currentSample = computed(() => summary.value?.demo_samples[sample.value])
const sampleOptions = computed(() =>
  (summary.value?.demo_samples ?? []).map((_, index) => ({
    value: index,
    label: `Demo case ${String(index + 1).padStart(2, '0')}`,
  })),
)
const caseGroups = computed(() =>
  FEATURE_GROUPS.map((group) => ({
    ...group,
    features: CASE_FEATURES.filter((feature) => feature.group === group.id),
  })),
)
const maskRates = computed(() => {
  const rates = (summary.value?.robustness ?? []).map((row) => row.mask_rate)
  return [...new Set(rates)].sort((left, right) => left - right)
})
const maskedFeatureKeys = computed(() =>
  selected.value === 'missingness'
    ? deterministicMaskedFeatures(
        currentSample.value,
        summary.value?.features ?? [],
        maskRate.value,
        sample.value,
      )
    : new Set<string>(),
)
const recordedCount = computed(() =>
  CASE_FEATURES.filter(({ key }) => typeof currentSample.value?.[key] === 'number').length,
)
const robustnessGroups = computed(() =>
  ROBUSTNESS_TASKS.map((taskId) => {
    const rows = (summary.value?.robustness ?? [])
      .filter((row) => row.task === taskId)
      .sort((left, right) => left.mask_rate - right.mask_rate)
    return {
      task: taskId,
      label: taskLabel(taskId),
      rows,
      baseline: rows.find((row) => row.mask_rate === 0)?.auroc,
    }
  }),
)

const percent = (value: number) => `${(value * 100).toFixed(1)}%`
const taskLabel = (taskId: string) =>
  taskId === 'mortality' ? 'In-hospital mortality' : 'Prolonged ICU stay'
const aurocDelta = (value: number, baseline: number | undefined) => {
  if (baseline === undefined) return 'Baseline unavailable'
  const delta = value - baseline
  return `Δ vs 0%: ${delta >= 0 ? '+' : ''}${delta.toFixed(3)}`
}
const contributionLabel = (feature: string) =>
  featureByKey.get(feature)?.label ?? feature.replaceAll('_', ' ')
const contributionValue = (feature: string) => {
  const definition = featureByKey.get(feature)
  if (!definition) {
    const value = featureValue(currentSample.value, feature)
    return value === null ? 'Not recorded' : value.toFixed(1)
  }
  const value = featureValue(currentSample.value, feature)
  const formatted = formatFeatureValue(definition, value)
  return value === null || !definition.unit ? formatted : `${formatted} ${definition.unit}`
}
const contributionDirection = (direction: string) =>
  direction === 'higher' ? 'Pushed signal higher' : 'Pushed signal lower'

async function load() {
  loading.value = true
  error.value = ''
  try {
    ;[tasks.value, summary.value] = await Promise.all([
      api.tasks().then((response) => response.tasks),
      api.summary(),
    ])
    if (sample.value >= (summary.value.demo_samples?.length ?? 0)) sample.value = 0
    if (maskRates.value.length && !maskRates.value.includes(maskRate.value)) {
      maskRate.value = maskRates.value[0]
    }
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : 'Unable to load demo'
  } finally {
    loading.value = false
  }
}

function choose(id: string) {
  selected.value = id
  prediction.value = null
  robustnessScores.value = {}
  error.value = ''
}

function caseChanged() {
  prediction.value = null
  robustnessScores.value = {}
  error.value = ''
}

async function runPrediction() {
  if (selected.value === 'missingness' || !currentSample.value || !summary.value) return
  running.value = true
  error.value = ''
  try {
    prediction.value = await api.predict(
      selected.value,
      currentSample.value,
      summary.value.features,
    )
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : 'Prediction failed'
  } finally {
    running.value = false
  }
}

async function runRobustness() {
  if (!currentSample.value || !summary.value) return
  running.value = true
  error.value = ''
  robustnessScores.value = {}
  const maskedSample = withMaskedFeatures(currentSample.value, maskedFeatureKeys.value)
  try {
    const results = await Promise.all(
      ROBUSTNESS_TASKS.flatMap((taskId) => [
        api.predict(taskId, currentSample.value!, summary.value!.features),
        api.predict(taskId, maskedSample, summary.value!.features),
      ]),
    )
    robustnessScores.value = {
      mortality: { baseline: results[0], masked: results[1] },
      long_stay: { baseline: results[2], masked: results[3] },
    }
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : 'Mask-and-rescore failed'
  } finally {
    running.value = false
  }
}

onMounted(load)
</script>

<template>
  <Layout class="app-shell">
    <main class="page">
      <header class="hero">
        <Tag color="blue">BN5212 · RESEARCH DEMO</Tag>
        <h1>Early ICU Risk Lab</h1>
        <p>Four transparent tracks for understanding first-24-hour signals, outcomes, and missing-data robustness.</p>
        <Alert
          message="Educational demo only / 仅供教学演示"
          description="Outputs are relative model signals, not diagnoses, treatment advice, or calibrated clinical probabilities."
          type="warning"
          show-icon
        />
      </header>

      <Spin :spinning="loading">
        <template v-if="error && !summary">
          <Alert type="error" message="Demo unavailable" :description="error" show-icon>
            <template #action><Button @click="load">Retry</Button></template>
          </Alert>
        </template>

        <template v-else-if="summary">
          <Row :gutter="[16, 16]" class="stats">
            <Col :xs="12" :lg="6"><Statistic title="ICU stays" :value="summary.cohort.stays" /></Col>
            <Col :xs="12" :lg="6"><Statistic title="Patients" :value="summary.cohort.patients" /></Col>
            <Col :xs="12" :lg="6"><Statistic title="Observation window" :value="summary.cohort.window_hours" suffix="h" /></Col>
            <Col :xs="12" :lg="6"><Statistic title="Model features" :value="summary.features.length" /></Col>
          </Row>

          <section>
            <div class="section-heading">
              <span>01</span>
              <div>
                <h2>Research tracks / 研究路径</h2>
                <p>One cohort and observation window, four questions.</p>
              </div>
            </div>
            <Row :gutter="[16, 16]">
              <Col v-for="(item, index) in tasks" :key="item.id" :xs="24" :md="12">
                <Card
                  class="track"
                  :class="{ active: selected === item.id }"
                  role="button"
                  :tabindex="0"
                  :aria-pressed="selected === item.id"
                  @click="choose(item.id)"
                  @keydown.enter="choose(item.id)"
                  @keydown.space.prevent="choose(item.id)"
                >
                  <div class="track-meta">
                    <span>0{{ index + 1 }}</span>
                    <Tag :color="item.type === 'prediction' ? 'geekblue' : 'purple'">
                      {{ item.type === 'prediction' ? 'PREDICTION' : 'STRESS TEST' }}
                    </Tag>
                  </div>
                  <h3>{{ item.title }}</h3>
                  <p>{{ item.question }}</p>
                  <small>{{ item.window }} · {{ item.label }}</small>
                </Card>
              </Col>
            </Row>
          </section>

          <div class="workspace">
            <section class="workspace-section">
              <Card title="02 / Model card / 模型卡">
                <template #extra><Tag>{{ task?.title }}</Tag></template>

                <template v-if="selected === 'missingness'">
                  <p class="card-intro">
                    Precomputed cohort AUROC under deterministic masking. Each change is measured from that task’s 0% baseline.
                  </p>
                  <section
                    v-for="group in robustnessGroups"
                    :key="group.task"
                    class="robust-group"
                  >
                    <h3>{{ group.label }}</h3>
                    <div
                      v-for="row in group.rows"
                      :key="`${row.task}-${row.mask_rate}`"
                      class="robust-row"
                    >
                      <div class="robust-label">
                        <span>{{ percent(row.mask_rate) }} masked / 已隐藏</span>
                        <small>{{ aurocDelta(row.auroc, group.baseline) }}</small>
                      </div>
                      <Progress
                        :percent="row.auroc * 100"
                        :format="() => row.auroc.toFixed(3)"
                      />
                    </div>
                  </section>
                </template>

                <template v-else-if="metric">
                  <Row :gutter="16">
                    <Col
                      v-for="item in [['AUROC', metric.auroc], ['AUPRC', metric.auprc], ['F1', metric.f1]]"
                      :key="String(item[0])"
                      :xs="8"
                    >
                      <Statistic :title="String(item[0])" :value="Number(item[1])" :precision="3" />
                    </Col>
                  </Row>
                  <div class="detail-grid">
                    <span>Positive rate <b>{{ percent(metric.positive_rate) }}</b></span>
                    <span>Test samples <b>{{ metric.test_samples }}</b></span>
                    <span>Sensitivity <b>{{ metric.sensitivity }}</b></span>
                    <span>Specificity <b>{{ metric.specificity }}</b></span>
                  </div>
                  <p class="muted">Logistic regression · median imputation + missing indicators · patient-level split</p>
                </template>
              </Card>
            </section>

            <section class="workspace-section">
              <Card title="03 / Live teaching demo / 实时教学演示">
                <template v-if="!summary.demo_samples.length">
                  <Empty description="This summary has no held-out demo case / 当前摘要没有留出的演示案例" />
                </template>

                <template v-else>
                  <label for="sample">Anonymous held-out case / 匿名留出案例</label>
                  <Select
                    id="sample"
                    v-model:value="sample"
                    class="sample-select"
                    :options="sampleOptions"
                    @change="caseChanged"
                  />

                  <div class="case-heading">
                    <div>
                      <h3>First 24-hour values</h3>
                      <p>首 24 小时输入值</p>
                    </div>
                    <Tag>{{ recordedCount }}/{{ CASE_FEATURES.length }} recorded</Tag>
                  </div>

                  <div class="case-groups">
                    <section v-for="group in caseGroups" :key="group.id" class="case-group">
                      <h4>{{ group.label }} <small>{{ group.subtitle }}</small></h4>
                      <dl>
                        <div
                          v-for="feature in group.features"
                          :key="feature.key"
                          class="case-value"
                          :class="{
                            'is-missing': featureValue(currentSample, feature.key) === null,
                            'is-masked': maskedFeatureKeys.has(feature.key),
                          }"
                        >
                          <dt>{{ feature.label }}</dt>
                          <dd v-if="maskedFeatureKeys.has(feature.key)">
                            <Tag color="orange">Masked / 已隐藏</Tag>
                            <small>sent as null</small>
                          </dd>
                          <dd v-else>
                            {{ formatFeatureValue(feature, featureValue(currentSample, feature.key)) }}
                            <small v-if="featureValue(currentSample, feature.key) !== null && feature.unit">
                              {{ feature.unit }}
                            </small>
                          </dd>
                        </div>
                      </dl>
                    </section>
                  </div>

                  <template v-if="selected === 'missingness'">
                    <div class="mask-panel">
                      <div class="mask-heading">
                        <div>
                          <h3>Mask and rescore</h3>
                          <p>隐藏并重新评分</p>
                        </div>
                        <strong>{{ maskedFeatureKeys.size }} fields masked</strong>
                      </div>
                      <div class="mask-rates" role="group" aria-label="Mask rate">
                        <button
                          v-for="rate in maskRates"
                          :key="rate"
                          type="button"
                          :class="{ active: maskRate === rate }"
                          :aria-pressed="maskRate === rate"
                          @click="maskRate = rate; robustnessScores = {}; error = ''"
                        >
                          {{ percent(rate) }}
                        </button>
                      </div>
                      <p class="method-note">
                        The same case and rate always mask the same recorded fields. Masked values are sent as
                        <code>null</code> and filled with the training median by the Java scorer. The online scorer
                        does not replay the separate missing-indicator coefficients used in Python training.
                      </p>
                      <Button type="primary" block :loading="running" @click="runRobustness">
                        Run mask-and-rescore / 运行稳健性演示
                      </Button>
                    </div>

                    <Alert v-if="error" type="error" :message="error" class="inline-alert" />
                    <div v-if="Object.keys(robustnessScores).length" class="robust-results">
                      <h3>Case-level score comparison</h3>
                      <p>案例评分对比</p>
                      <div
                        v-for="taskId in ROBUSTNESS_TASKS"
                        :key="taskId"
                        class="score-comparison"
                      >
                        <h4>{{ taskLabel(taskId) }}</h4>
                        <div>
                          <span>Unmasked <strong>{{ robustnessScores[taskId]?.baseline.ranking_score.toFixed(3) }}</strong></span>
                          <span>Masked <strong>{{ robustnessScores[taskId]?.masked.ranking_score.toFixed(3) }}</strong></span>
                        </div>
                      </div>
                      <small>
                        Scores are catalog-relative ranking signals, not probabilities or clinical decisions.
                      </small>
                    </div>
                  </template>

                  <template v-else>
                    <Button type="primary" block :loading="running" @click="runPrediction">
                      Run teaching prediction / 运行教学预测
                    </Button>
                    <Alert v-if="error" type="error" :message="error" class="inline-alert" />
                    <div v-if="prediction" class="result">
                      <span>Catalog-relative ranking signal</span>
                      <strong>{{ prediction.ranking_score.toFixed(3) }}</strong>
                      <Tag :color="prediction.risk_band === 'higher' ? 'red' : 'blue'">
                        {{ prediction.risk_band }} catalog-relative band
                      </Tag>
                      <p class="score-explanation">
                        This score compares this case with cases in the demo catalog. It is not a probability or a clinical decision.
                      </p>
                      <h4>Largest model contributions</h4>
                      <div
                        v-for="item in prediction.top_contributors"
                        :key="item.feature"
                        class="contribution"
                      >
                        <div>
                          <span>{{ contributionLabel(item.feature) }}</span>
                          <small>Case value: {{ contributionValue(item.feature) }}</small>
                        </div>
                        <b :class="item.direction">
                          {{ contributionDirection(item.direction) }} ·
                          {{ item.contribution >= 0 ? '+' : '' }}{{ item.contribution.toFixed(2) }}
                        </b>
                      </div>
                      <small>{{ prediction.disclaimer }}</small>
                    </div>
                  </template>
                </template>
              </Card>
            </section>
          </div>

          <section>
            <div class="section-heading">
              <span>04</span>
              <div>
                <h2>Data transparency / 数据透明度</h2>
                <p>Missingness is modeled explicitly and stress-tested as a reliability concern.</p>
              </div>
            </div>
            <div class="missingness">
              <div
                v-for="entry in Object.entries(summary.missingness).sort((a, b) => b[1] - a[1]).slice(0, 10)"
                :key="entry[0]"
              >
                <span>{{ contributionLabel(entry[0]) }}</span>
                <Progress :percent="entry[1] * 100" :show-info="false" size="small" />
                <b>{{ percent(entry[1]) }}</b>
              </div>
            </div>
          </section>
        </template>
      </Spin>

      <footer>MIMIC-IV v3.1 · De-identified data · Reproducible course prototype</footer>
    </main>
  </Layout>
</template>
