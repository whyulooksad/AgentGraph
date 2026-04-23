export interface ExperimentSpec {
  experiment_id: string;
  name: string;
  setup: string;
  dataset: string;
  metrics: string[];
  result_summary: string;
}

export interface ReferenceSpec {
  reference_id: string;
  title: string;
  authors: string[];
  year: number | null;
  venue: string | null;
  notes: string | null;
}

export interface ArtifactSeed {
  artifact_id: string;
  kind: string;
  title: string;
  description: string;
  target_sections: string[];
}

export interface ResearchStory {
  story_id: string;
  title_hint: string | null;
  topic: string;
  problem_statement: string;
  motivation: string;
  core_idea: string;
  method_summary: string;
  contributions: string[];
  experiments: ExperimentSpec[];
  baselines: string[];
  findings: string[];
  limitations: string[];
  references: ReferenceSpec[];
  assets: ArtifactSeed[];
  metadata: Record<string, unknown>;
}
