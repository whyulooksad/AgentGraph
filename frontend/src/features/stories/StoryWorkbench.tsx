import { useEffect, useMemo, useState } from "react";

import type { ArtifactSeed, ExperimentSpec, ResearchStory } from "../../types/story";

type StoryWorkbenchProps = {
  stories: ResearchStory[];
  onSave: (story: ResearchStory) => Promise<void>;
  onRun: (story: ResearchStory) => Promise<void>;
};

function createEmptyExperiment(): ExperimentSpec {
  return {
    experiment_id: "exp_1",
    name: "",
    setup: "",
    dataset: "",
    metrics: [],
    result_summary: "",
  };
}

function createEmptyAsset(): ArtifactSeed {
  return {
    artifact_id: "fig_1",
    kind: "figure",
    title: "",
    description: "",
    target_sections: [],
  };
}

function createEmptyStory(): ResearchStory {
  return {
    story_id: "new_story",
    title_hint: "",
    topic: "",
    problem_statement: "",
    motivation: "",
    core_idea: "",
    method_summary: "",
    contributions: [],
    experiments: [createEmptyExperiment()],
    baselines: [],
    findings: [],
    limitations: [],
    references: [],
    assets: [createEmptyAsset()],
    metadata: {},
  };
}

function toText(value: string[]): string {
  return value.join("\n");
}

function fromText(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function StoryWorkbench({ stories, onSave, onRun }: StoryWorkbenchProps) {
  const [selectedId, setSelectedId] = useState<string>(stories[0]?.story_id ?? "new_story");
  const [story, setStory] = useState<ResearchStory>(stories[0] ?? createEmptyStory());

  const selectedStory = useMemo(
    () => stories.find((item) => item.story_id === selectedId) ?? null,
    [selectedId, stories],
  );

  useEffect(() => {
    if (!stories.length) {
      return;
    }
    if (!selectedStory) {
      setSelectedId(stories[0].story_id);
      setStory(stories[0]);
    }
  }, [selectedStory, stories]);

  function syncStory(nextId: string) {
    setSelectedId(nextId);
    const next = stories.find((item) => item.story_id === nextId);
    setStory(next ?? createEmptyStory());
  }

  function patch<K extends keyof ResearchStory>(key: K, value: ResearchStory[K]) {
    setStory((current) => ({ ...current, [key]: value }));
  }

  function patchExperiment(index: number, next: ExperimentSpec) {
    setStory((current) => ({
      ...current,
      experiments: current.experiments.map((item, i) => (i === index ? next : item)),
    }));
  }

  function patchAsset(index: number, next: ArtifactSeed) {
    setStory((current) => ({
      ...current,
      assets: current.assets.map((item, i) => (i === index ? next : item)),
    }));
  }

  async function handleImportFile(file: File | null) {
    if (!file) {
      return;
    }
    const text = await file.text();
    const parsed = JSON.parse(text) as ResearchStory;
    setStory(parsed);
    setSelectedId(parsed.story_id);
  }

  return (
    <div className="story-shell">
      <aside className="story-shell-side">
        <section className="panel">
          <div className="panel-header">
            <h2>Story 列表</h2>
          </div>
          <div className="story-list-stack">
            {stories.map((item) => (
              <button
                key={item.story_id}
                type="button"
                className={item.story_id === selectedId ? "story-list-item active" : "story-list-item"}
                onClick={() => syncStory(item.story_id)}
              >
                <span className="story-list-title">{item.title_hint || item.story_id}</span>
                <span className="story-list-meta">{item.story_id}</span>
              </button>
            ))}
            <button
              type="button"
              className={selectedId === "new_story" ? "story-list-item active" : "story-list-item"}
              onClick={() => syncStory("new_story")}
            >
              <span className="story-list-title">新建 Story</span>
              <span className="story-list-meta">ResearchStory</span>
            </button>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>当前概览</h2>
          </div>
          <div className="story-glance">
            <div className="story-glance-row">
              <span>Story ID</span>
              <strong>{story.story_id || "-"}</strong>
            </div>
            <div className="story-glance-row">
              <span>标题</span>
              <strong>{story.title_hint || "-"}</strong>
            </div>
            <div className="story-glance-row">
              <span>主题</span>
              <strong>{story.topic || "-"}</strong>
            </div>
            <div className="story-glance-row">
              <span>Experiments</span>
              <strong>{story.experiments.length}</strong>
            </div>
          </div>
        </section>
      </aside>

      <section className="panel story-editor-panel">
        <div className="story-editor-top">
          <div>
            <div className="eyebrow">Editor</div>
            <h2>ResearchStory 编辑</h2>
          </div>
          <div className="story-editor-actions">
            <label className="ghost-button file-button">
              导入 JSON
              <input
                type="file"
                accept="application/json"
                hidden
                onChange={(event) => {
                  void handleImportFile(event.target.files?.[0] ?? null);
                }}
              />
            </label>
            <button className="ghost-button" type="button" onClick={() => void onSave(story)}>
              保存 Story
            </button>
            <button className="primary-button" type="button" onClick={() => void onRun(story)}>
              创建 Run
            </button>
          </div>
        </div>

        <div className="form-grid story-form-grid">
          <label className="field">
            <span>story_id</span>
            <input value={story.story_id} onChange={(e) => patch("story_id", e.target.value)} />
          </label>
          <label className="field">
            <span>title_hint</span>
            <input value={story.title_hint ?? ""} onChange={(e) => patch("title_hint", e.target.value)} />
          </label>
          <label className="field field-wide">
            <span>topic</span>
            <input value={story.topic} onChange={(e) => patch("topic", e.target.value)} />
          </label>
          <label className="field field-wide">
            <span>problem_statement</span>
            <textarea value={story.problem_statement} onChange={(e) => patch("problem_statement", e.target.value)} />
          </label>
          <label className="field field-wide">
            <span>motivation</span>
            <textarea value={story.motivation} onChange={(e) => patch("motivation", e.target.value)} />
          </label>
          <label className="field field-wide">
            <span>core_idea</span>
            <textarea value={story.core_idea} onChange={(e) => patch("core_idea", e.target.value)} />
          </label>
          <label className="field field-wide">
            <span>method_summary</span>
            <textarea value={story.method_summary} onChange={(e) => patch("method_summary", e.target.value)} />
          </label>
          <label className="field field-wide">
            <span>contributions</span>
            <textarea
              value={toText(story.contributions)}
              onChange={(e) => patch("contributions", fromText(e.target.value))}
            />
          </label>
          <label className="field field-wide">
            <span>baselines</span>
            <textarea value={toText(story.baselines)} onChange={(e) => patch("baselines", fromText(e.target.value))} />
          </label>
          <label className="field field-wide">
            <span>findings</span>
            <textarea value={toText(story.findings)} onChange={(e) => patch("findings", fromText(e.target.value))} />
          </label>
          <label className="field field-wide">
            <span>limitations</span>
            <textarea
              value={toText(story.limitations)}
              onChange={(e) => patch("limitations", fromText(e.target.value))}
            />
          </label>
        </div>

        <section className="nested-panel">
          <div className="panel-header">
            <h2>experiments</h2>
            <button
              className="ghost-button"
              type="button"
              onClick={() => patch("experiments", [...story.experiments, createEmptyExperiment()])}
            >
              新增 experiment
            </button>
          </div>
          <div className="nested-grid">
            {story.experiments.map((experiment, index) => (
              <div className="nested-card" key={`${experiment.experiment_id}-${index}`}>
                <label className="field">
                  <span>experiment_id</span>
                  <input
                    value={experiment.experiment_id}
                    onChange={(e) => patchExperiment(index, { ...experiment, experiment_id: e.target.value })}
                  />
                </label>
                <label className="field">
                  <span>name</span>
                  <input value={experiment.name} onChange={(e) => patchExperiment(index, { ...experiment, name: e.target.value })} />
                </label>
                <label className="field field-wide">
                  <span>setup</span>
                  <textarea value={experiment.setup} onChange={(e) => patchExperiment(index, { ...experiment, setup: e.target.value })} />
                </label>
                <label className="field">
                  <span>dataset</span>
                  <input
                    value={experiment.dataset}
                    onChange={(e) => patchExperiment(index, { ...experiment, dataset: e.target.value })}
                  />
                </label>
                <label className="field">
                  <span>metrics</span>
                  <input
                    value={experiment.metrics.join(", ")}
                    onChange={(e) =>
                      patchExperiment(index, {
                        ...experiment,
                        metrics: e.target.value.split(",").map((item) => item.trim()).filter(Boolean),
                      })
                    }
                  />
                </label>
                <label className="field field-wide">
                  <span>result_summary</span>
                  <textarea
                    value={experiment.result_summary}
                    onChange={(e) => patchExperiment(index, { ...experiment, result_summary: e.target.value })}
                  />
                </label>
              </div>
            ))}
          </div>
        </section>

        <section className="nested-panel">
          <div className="panel-header">
            <h2>assets</h2>
            <button
              className="ghost-button"
              type="button"
              onClick={() => patch("assets", [...story.assets, createEmptyAsset()])}
            >
              新增 asset
            </button>
          </div>
          <div className="nested-grid">
            {story.assets.map((asset, index) => (
              <div className="nested-card" key={`${asset.artifact_id}-${index}`}>
                <label className="field">
                  <span>artifact_id</span>
                  <input
                    value={asset.artifact_id}
                    onChange={(e) => patchAsset(index, { ...asset, artifact_id: e.target.value })}
                  />
                </label>
                <label className="field">
                  <span>kind</span>
                  <input value={asset.kind} onChange={(e) => patchAsset(index, { ...asset, kind: e.target.value })} />
                </label>
                <label className="field field-wide">
                  <span>title</span>
                  <input value={asset.title} onChange={(e) => patchAsset(index, { ...asset, title: e.target.value })} />
                </label>
                <label className="field field-wide">
                  <span>description</span>
                  <textarea
                    value={asset.description}
                    onChange={(e) => patchAsset(index, { ...asset, description: e.target.value })}
                  />
                </label>
                <label className="field field-wide">
                  <span>target_sections</span>
                  <input
                    value={asset.target_sections.join(", ")}
                    onChange={(e) =>
                      patchAsset(index, {
                        ...asset,
                        target_sections: e.target.value.split(",").map((item) => item.trim()).filter(Boolean),
                      })
                    }
                  />
                </label>
              </div>
            ))}
          </div>
        </section>
      </section>

      <aside className="story-shell-preview">
        <section className="panel story-preview-panel">
          <div className="panel-header">
            <h2>结构预览</h2>
            <div className="panel-kicker">{selectedStory ? selectedStory.story_id : "new_story"}</div>
          </div>
          <pre className="artifact-content compact-tall">{JSON.stringify(story, null, 2)}</pre>
        </section>
      </aside>
    </div>
  );
}
