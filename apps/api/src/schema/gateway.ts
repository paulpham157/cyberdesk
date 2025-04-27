import { z } from 'zod';

// Schema for Gateway Execute Command Request
export const GatewayExecuteCommandRequestSchema = z.object({
    command: z.string()
});

// Schema for Gateway Execute Command Response
export const GatewayExecuteCommandResponseSchema = z.object({
    status: z.string(),
    vm_status_code: z.number().int(),
    vm_response: z.object({
        args: z.array(z.string()).optional(),
        return_code: z.number().int(),
        stdout: z.string(),
        stderr: z.string(),
        duration_s: z.number().optional(),
    })
});
