import type { RunDetail, RunItem } from "../types/run";
import type { ResearchStory } from "../types/story";

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function listRuns(): Promise<RunItem[]> {
  const response = await fetch("/api/runs");
  return parseJson<RunItem[]>(response);
}

export async function getRunDetail(runId: string): Promise<RunDetail> {
  const response = await fetch(`/api/runs/${runId}`);
  return parseJson<RunDetail>(response);
}

export async function createRunFromStory(story: ResearchStory, model = "qwen-plus"): Promise<RunDetail> {
  const response = await fetch("/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ story, model }),
  });
  return parseJson<RunDetail>(response);
}
