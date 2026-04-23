import type { ResearchStory } from "../types/story";

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function listStories(): Promise<ResearchStory[]> {
  const response = await fetch("/api/stories");
  return parseJson<ResearchStory[]>(response);
}

export async function saveStory(story: ResearchStory): Promise<ResearchStory> {
  const response = await fetch("/api/stories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(story),
  });
  return parseJson<ResearchStory>(response);
}
