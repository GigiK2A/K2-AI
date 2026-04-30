import { SUITE_AI_SERVICES, type SuiteAiService } from '../../src/data/suiteAiServices'

export type PublicSuiteAiService = Omit<SuiteAiService, 'skills'>

const SERVICE_BY_ID = new Map(SUITE_AI_SERVICES.map(service => [service.id, service]))

export function normalizeServiceId(value: unknown): string {
  return String(value || '').trim().toUpperCase()
}

export function getSuiteAiServices(): PublicSuiteAiService[] {
  return SUITE_AI_SERVICES.map(toPublicService)
}

export function getSuiteAiServiceById(id: unknown): SuiteAiService | null {
  const serviceId = normalizeServiceId(id)
  return SERVICE_BY_ID.get(serviceId) || null
}

export function isValidServiceId(id: unknown): boolean {
  return Boolean(getSuiteAiServiceById(id))
}

export function toPublicService(service: SuiteAiService): PublicSuiteAiService {
  const { skills: _skills, ...publicService } = service
  return publicService
}

export function getServiceSkills(id: unknown): string[] {
  return getSuiteAiServiceById(id)?.skills || []
}
