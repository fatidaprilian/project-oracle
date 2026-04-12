export async function withRetry<T>(
  fn: () => Promise<T>,
  attempts = 2,
  delayMs = 500,
): Promise<T> {
  let lastError: unknown = null

  for (let attempt = 0; attempt <= attempts; attempt += 1) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      if (attempt === attempts) {
        break
      }
      await new Promise((resolve) => setTimeout(resolve, delayMs * (attempt + 1)))
    }
  }

  throw lastError
}