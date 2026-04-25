import type { ResearchStory } from "../types/story";

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Ignore JSON parse failures and keep the fallback message.
    }
    throw new Error(detail);
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

export async function deleteStory(storyId: string): Promise<void> {
  const response = await fetch(`/api/stories/${encodeURIComponent(storyId)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Ignore JSON parse failures and keep the fallback message.
    }
    throw new Error(detail);
  }
}
