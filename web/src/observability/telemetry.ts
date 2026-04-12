type TelemetryPayload = {
  kind: 'web-vitals' | 'frontend-error'
  name: string
  value?: number
  message?: string
  path: string
  at: string
}

const telemetryEndpoint = (import.meta.env.VITE_TELEMETRY_ENDPOINT || '').trim()

let initialized = false

function currentPath(): string {
  return `${window.location.pathname}${window.location.search}`
}

function sendTelemetry(payload: TelemetryPayload): void {
  if (!telemetryEndpoint) {
    console.debug('[telemetry]', payload)
    return
  }

  const body = JSON.stringify(payload)
  if (navigator.sendBeacon) {
    const blob = new Blob([body], { type: 'application/json' })
    navigator.sendBeacon(telemetryEndpoint, blob)
    return
  }

  void fetch(telemetryEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body,
    keepalive: true,
  }).catch(() => undefined)
}

function emitMetric(name: string, value: number): void {
  sendTelemetry({
    kind: 'web-vitals',
    name,
    value: Number(value.toFixed(6)),
    path: currentPath(),
    at: new Date().toISOString(),
  })
}

function observePerformance(
  entryType: string,
  handler: (entries: PerformanceEntry[]) => void,
): void {
  if (!('PerformanceObserver' in window)) {
    return
  }

  try {
    const observer = new PerformanceObserver((list) => {
      handler(list.getEntries())
    })
    observer.observe({ type: entryType, buffered: true })
  } catch {
    // Ignore unsupported metric types in older browsers.
  }
}

export function initFrontendObservability(): void {
  if (initialized || typeof window === 'undefined') {
    return
  }
  initialized = true

  window.addEventListener('error', (event) => {
    sendTelemetry({
      kind: 'frontend-error',
      name: 'window.error',
      message: event.message,
      path: currentPath(),
      at: new Date().toISOString(),
    })
  })

  window.addEventListener('unhandledrejection', (event) => {
    sendTelemetry({
      kind: 'frontend-error',
      name: 'window.unhandledrejection',
      message: String(event.reason ?? 'unknown reason'),
      path: currentPath(),
      at: new Date().toISOString(),
    })
  })

  observePerformance('paint', (entries) => {
    for (const entry of entries) {
      if (entry.name === 'first-contentful-paint') {
        emitMetric('fcp', entry.startTime)
      }
    }
  })

  observePerformance('largest-contentful-paint', (entries) => {
    const lastEntry = entries[entries.length - 1]
    if (lastEntry) {
      emitMetric('lcp', lastEntry.startTime)
    }
  })

  let clsTotal = 0
  observePerformance('layout-shift', (entries) => {
    for (const entry of entries) {
      const shift = entry as PerformanceEntry & {
        value?: number
        hadRecentInput?: boolean
      }
      if (!shift.hadRecentInput && typeof shift.value === 'number') {
        clsTotal += shift.value
      }
    }
    emitMetric('cls', clsTotal)
  })

  observePerformance('first-input', (entries) => {
    const firstInput = entries[0] as PerformanceEntry & {
      processingStart?: number
    }
    if (firstInput && typeof firstInput.processingStart === 'number') {
      emitMetric('fid', firstInput.processingStart - firstInput.startTime)
    }
  })
}
