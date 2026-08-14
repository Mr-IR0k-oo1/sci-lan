import { get, post } from './client';
import type { WhatIfRequest } from '../types';

export interface CaseStudySummary {
  id: string;
  name: string;
  description: string;
  grid_id: string;
  scenario: Partial<WhatIfRequest>;
  expected_issues: string[];
  expected_mitigation: string;
}

export interface CaseStudyRunStep {
  name: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'SKIPPED';
  message: string;
}

export interface CaseStudyRunResponse {
  case_id: string;
  status: 'SUCCESS' | 'FAILED';
  steps: CaseStudyRunStep[];
  analysis: any;
  issues: any[];
  recommendations: any[];
}

export const getCaseStudies = async (): Promise<CaseStudySummary[]> => {
  return get<CaseStudySummary[]>('/case-studies');
};

export const runCaseStudy = async (caseId: string, engine: string = 'auto'): Promise<CaseStudyRunResponse> => {
  return post<CaseStudyRunResponse>(`/case-studies/${caseId}/run?engine=${engine}`, {});
};
