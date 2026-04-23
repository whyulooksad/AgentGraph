import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listRuns } from "../services/runs";
import { listStories } from "../services/stories";

export function HomePage() {
  const { data: stories = [] } = useQuery({
    queryKey: ["stories"],
    queryFn: listStories,
  });
  const { data: runs = [] } = useQuery({
    queryKey: ["runs"],
    queryFn: listRuns,
  });

  return (
    <div className="overview-page">
      <section className="home-hero">
        <div className="home-hero-copy">
          <div className="eyebrow">Story2Proposal</div>
          <h1>科研写作工作台</h1>
          <p>配置 Story，启动 Run，查看产物。</p>
        </div>
        <div className="home-hero-actions">
          <Link to="/stories" className="primary-button">
            新建 Story
          </Link>
          <Link to="/runs" className="ghost-button">
            查看 Runs
          </Link>
        </div>
      </section>

      <section className="home-grid">
        <article className="home-card">
          <div className="home-card-head">
            <span className="eyebrow">Stories</span>
            <Link to="/stories" className="inline-link">
              进入
            </Link>
          </div>
          <div className="home-list">
            {stories.length ? (
              stories.slice(0, 3).map((story) => (
                <div className="home-list-row" key={story.story_id}>
                  <div>
                    <div className="home-list-title">{story.story_id}</div>
                    <div className="home-list-subtle">{story.topic}</div>
                  </div>
                  <div className="home-list-time">{story.title_hint ?? "-"}</div>
                </div>
              ))
            ) : (
              <div className="home-list-row">
                <div className="home-list-subtle">还没有 Story。</div>
              </div>
            )}
          </div>
        </article>

        <article className="home-card">
          <div className="home-card-head">
            <span className="eyebrow">Runs</span>
            <Link to="/runs" className="inline-link">
              进入
            </Link>
          </div>
          <div className="home-list">
            {runs.length ? (
              runs.slice(0, 3).map((run) => (
                <div className="home-list-row" key={run.id}>
                  <div>
                    <div className="home-list-title">{run.id}</div>
                    <div className="home-list-subtle">
                      {run.model} · {run.status}
                    </div>
                  </div>
                  <div className="home-list-time">{run.updatedAt.slice(11, 16)}</div>
                </div>
              ))
            ) : (
              <div className="home-list-row">
                <div className="home-list-subtle">还没有 Run。</div>
              </div>
            )}
          </div>
        </article>

        <article className="home-card home-card-quiet">
          <div className="home-card-head">
            <span className="eyebrow">Status</span>
          </div>
          <div className="status-stack">
            <div className="status-line">
              <span>Stories</span>
              <strong>{stories.length}</strong>
            </div>
            <div className="status-line">
              <span>Runs</span>
              <strong>{runs.length}</strong>
            </div>
            <div className="status-line">
              <span>默认模型</span>
              <strong>qwen-plus</strong>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}
