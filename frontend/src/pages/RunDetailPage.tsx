import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { ArtifactViewer } from "../features/artifacts/ArtifactViewer";
import { EventLogPanel } from "../features/logs/EventLogPanel";
import { RunStatusBadge } from "../features/runs/RunStatusBadge";
import { SectionStatusList } from "../features/workflow/SectionStatusList";
import { WorkflowPanel } from "../features/workflow/WorkflowPanel";
import { getRunDetail } from "../services/runs";

export function RunDetailPage() {
  const { runId = "" } = useParams();
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => getRunDetail(runId),
    enabled: Boolean(runId),
    refetchInterval: (query) => {
      const run = query.state.data;
      if (!runId || !run) {
        return false;
      }
      return run.status === "running" ? 2500 : false;
    },
    refetchIntervalInBackground: true,
  });

  if (isLoading) {
    return (
      <div className="page-stack">
        <section className="run-hero">
          <div className="run-hero-copy">
            <div className="eyebrow">Run</div>
            <h1>加载中</h1>
            <p>正在读取运行详情。</p>
          </div>
        </section>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="page-stack">
        <section className="run-hero">
          <div className="run-hero-copy">
            <div className="eyebrow">Run</div>
            <h1>未找到 Run</h1>
            <p>{runId}</p>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="page-stack">
      <section className="run-hero">
        <div className="run-hero-copy">
          <div className="eyebrow">Run</div>
          <h1>{data.id}</h1>
          <p>{data.storyId}</p>
        </div>
        <div className="run-hero-meta">
          <div className="run-chip">
            <span>状态</span>
            <RunStatusBadge status={data.status} />
          </div>
          <div className="run-chip">
            <span>模型</span>
            <strong>{data.model}</strong>
          </div>
          <div className="run-chip">
            <span>当前章节</span>
            <strong>{data.currentSectionId ?? "-"}</strong>
          </div>
          <div className="run-chip">
            <span>下一节点</span>
            <strong>{data.nextNode ?? "-"}</strong>
          </div>
          <div className="run-chip">
            <span>刷新状态</span>
            <strong>{data.status === "running" ? (isFetching ? "同步中" : "自动轮询中") : "已停止轮询"}</strong>
          </div>
          <div className="run-chip">
            <span>更新时间</span>
            <strong>{data.updatedAt}</strong>
          </div>
        </div>
      </section>

      <div className="run-shell">
        <aside className="run-shell-side">
          <section className="panel">
            <div className="panel-header">
              <h2>运行摘要</h2>
            </div>
            <ul className="summary-list">
              {data.summary.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
          <SectionStatusList sections={data.sections} />
          <EventLogPanel run={data} />
        </aside>

        <section className="run-shell-main">
          <WorkflowPanel run={data} />
          <ArtifactViewer run={data} />
        </section>
      </div>
    </div>
  );
}
