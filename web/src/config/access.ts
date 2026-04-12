import { AppRole } from '../auth/session'

const permissionsByRole: Record<
  AppRole,
  {
    canTriggerWorkflow: boolean
    canPromoteRequests: boolean
    canApproveRequests: boolean
  }
> = {
  viewer: {
    canTriggerWorkflow: false,
    canPromoteRequests: false,
    canApproveRequests: false,
  },
  operator: {
    canTriggerWorkflow: true,
    canPromoteRequests: false,
    canApproveRequests: true,
  },
  admin: {
    canTriggerWorkflow: true,
    canPromoteRequests: true,
    canApproveRequests: true,
  },
}

export function getAccessByRole(role: AppRole) {
  return {
    role,
    ...permissionsByRole[role],
  }
}
