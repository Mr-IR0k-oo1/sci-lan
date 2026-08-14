import { get, post } from './client';
import type { AnalysisRecord, MitigationCandidate, MitigationTestResult } from '../types';

export const stressApi = {
  runStress(gridId: string): Promise<AnalysisRecord> {
    return post<AnalysisRecord>(`/grids/${gridId}/stress`, {});
  },

  getAnalysis(analysisId: string): Promise<AnalysisRecord> {
    return get<AnalysisRecord>(`/analyses/${analysisId}/stress`);
  },

  getMitigationCandidates(analysisId: string): Promise<MitigationCandidate[]> {
    return get<MitigationCandidate[]>(`/analyses/${analysisId}/mitigation-candidates`);
  },

  runMitigationTests(analysisId: string, mitigationId?: string): Promise<MitigationTestResult[]> {
    return post<MitigationTestResult[]>(`/analyses/${analysisId}/mitigation-tests`, {
      mitigation_id: mitigationId,
      run_all: mitigationId == null,
    });
  },
};
