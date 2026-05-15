export type TaskPriority = "alta" | "media" | "bassa";
export type TaskStatus = "todo" | "doing" | "done" | "cancelled";

export interface Task {
  id: string;
  lead_id: string | null;
  title: string;
  notes: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  due_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  position: number;
}

export interface TaskCreatePayload {
  lead_id?: string | null;
  title: string;
  notes?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  due_at?: string | null;
}

export type TaskUpdatePayload = Partial<TaskCreatePayload> & {
  completed_at?: string | null;
};
