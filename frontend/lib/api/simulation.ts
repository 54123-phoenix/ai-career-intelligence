/** Simulation API — 职业模拟与演化 */

import { apiFetch } from './client';
import type { SimulationResult, StrategyComparison } from '@/types/simulation';

export interface RunSimulationRequest {
  resume_id: string;
  job_id: string;
  strategy?: 'aggressive' | 'balanced' | 'conservative';
}

export interface CompareStrategiesRequest {
  resume_id: string;
  job_id: string;
  strategies: ('aggressive' | 'balanced' | 'conservative')[];
}

export async function runSimulation(params: RunSimulationRequest): Promise<SimulationResult> {
  return apiFetch<SimulationResult>('/simulation/run', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function compareStrategies(
  params: CompareStrategiesRequest
): Promise<StrategyComparison> {
  return apiFetch<StrategyComparison>('/simulation/compare', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getSimulationSamples(): Promise<{
  resumes: Record<string, string>;
  jobs: Record<string, string>;
}> {
  return apiFetch('/simulation/samples');
}
