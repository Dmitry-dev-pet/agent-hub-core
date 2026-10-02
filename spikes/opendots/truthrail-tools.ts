import { defineTool } from '@copilotkit/runtime/v2';
import { z } from 'zod';

type ProviderResponse = { result?: unknown; error?: string };

export function truthrailTools(options?: {
  baseUrl?: string;
  token?: string;
}) {
  const baseUrl = (
    options?.baseUrl ??
    process.env.TRUTHRAIL_PROVIDER_URL ??
    'http://127.0.0.1:8766'
  ).replace(/\/$/, '');
  const token = options?.token ?? process.env.TRUTHRAIL_PROVIDER_TOKEN;

  async function call(name: string, args: Record<string, unknown>) {
    const response = await fetch(`${baseUrl}/v1/call`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ name, arguments: args }),
    });
    const payload = (await response.json()) as ProviderResponse;
    if (!response.ok || payload.error)
      throw new Error(payload.error ?? `Truthrail returned HTTP ${response.status}`);
    return payload.result;
  }

  return [
    defineTool({
      name: 'truthrail_status',
      description:
        'Read authoritative live Truthrail state for one project. Never mutates external systems.',
      parameters: z.object({
        project: z.string().min(1),
      }),
      execute: async ({ project }) =>
        call('truthrail_status', { project }),
    }),
    defineTool({
      name: 'truthrail_dispatch',
      description:
        'Plan the lowest-sufficient route and evaluate the reviewed operation admission gate. Never executes the operation.',
      parameters: z.object({
        project: z.string().min(1),
        requirement: z.enum([
          'read',
          'direct_mutation',
          'privileged_mutation',
          'runtime',
          'coding_agent',
          'machine_bound',
        ]),
        capability: z.string().min(1),
        operation: z.string().min(1).optional(),
        acceptance_proof: z.array(z.string().min(1)).min(1),
      }),
      execute: async (args) => call('truthrail_dispatch', args),
    }),
    defineTool({
      name: 'truthrail_approve',
      description:
        'Resolve a pending Truthrail manual-approval gate. Approval releases a handoff but does not execute the privileged operation.',
      parameters: z.object({
        approval_id: z.string().min(1),
        approve: z.boolean(),
      }),
      execute: async ({ approval_id, approve }) =>
        call('truthrail_approve', { approval_id, approve }),
    }),
  ];
}
