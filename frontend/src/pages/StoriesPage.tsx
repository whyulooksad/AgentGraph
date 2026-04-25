import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { ConfirmDialog } from "../components/ConfirmDialog";
import { StoryWorkbench } from "../features/stories/StoryWorkbench";
import { createRunFromStory } from "../services/runs";
import { deleteStory, listStories, saveStory } from "../services/stories";
import type { ResearchStory } from "../types/story";

export function StoriesPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [storyPendingDelete, setStoryPendingDelete] = useState<ResearchStory | null>(null);

  const { data = [] } = useQuery({
    queryKey: ["stories"],
    queryFn: listStories,
  });

  const saveMutation = useMutation({
    mutationFn: (story: ResearchStory) => saveStory(story),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["stories"] });
    },
  });

  const createRunMutation = useMutation({
    mutationFn: (story: ResearchStory) => createRunFromStory(story),
    onSuccess: async (run) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["stories"] }),
        queryClient.invalidateQueries({ queryKey: ["runs"] }),
      ]);
      navigate(`/runs/${run.id}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (storyId: string) => deleteStory(storyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["stories"] });
      setStoryPendingDelete(null);
    },
  });

  return (
    <>
      <div className="page-stack">
        <div className="page-heading">
          <div>
            <div className="eyebrow">Story</div>
            <h1>ResearchStory 配置</h1>
          </div>
        </div>
        <StoryWorkbench
          stories={data}
          onSave={async (story) => {
            await saveMutation.mutateAsync(story);
          }}
          onRun={async (story) => {
            const saved = await saveMutation.mutateAsync(story);
            await createRunMutation.mutateAsync(saved);
          }}
          onDelete={(story) => {
            setStoryPendingDelete(story);
          }}
        />
      </div>

      <ConfirmDialog
        open={storyPendingDelete !== null}
        title="删除 Story"
        body={
          storyPendingDelete
            ? `将删除 Story “${storyPendingDelete.title_hint || storyPendingDelete.story_id}”。此操作不会删除已存在的 runs。`
            : ""
        }
        confirmLabel={deleteMutation.isPending ? "删除中..." : "确认删除"}
        onCancel={() => {
          if (!deleteMutation.isPending) {
            setStoryPendingDelete(null);
          }
        }}
        onConfirm={() => {
          if (!storyPendingDelete) {
            return;
          }
          void deleteMutation.mutateAsync(storyPendingDelete.story_id);
        }}
      />
    </>
  );
}
