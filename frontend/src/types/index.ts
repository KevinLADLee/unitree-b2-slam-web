// API 类型定义

export interface Feedback {
  index: string;
  feedback: number; // 0=failure, 1=success, 2=waiting
  state: number;    // 0=idle, 2=mapping, 3=navigation, 4=relocation_open, etc.
  notice: string;
}

export interface Node {
  name: string;
  x: number;
  y: number;
  z: number;
  yaw: number;
}

export interface Edge {
  name: string;
  start_node: string;
  end_node: string;
  length: number;
  speed: number;
  avoid_method?: number;
}

export interface SystemStatus {
  state: number;
  state_name: string;
  node_count: number;
  edge_count: number;
}

export interface PoseInput {
  x: number;
  y: number;
  yaw: number;
}

export interface NavigationTarget {
  node_name: string;
}

export interface NavigationTargets {
  node_names: string[];
  mode: 'loop' | 'once';
}

export interface NavigationTask {
  id: string;
  name: string;
  node_names: string[];
  mode: 'loop' | 'once';
  created_at: string;
  updated_at?: string;
}

export interface CurrentPosition {
  x: number;
  y: number;
  z: number;
  yaw: number;
  timestamp: string;
}

export interface TopologyMap {
  nodes: Node[];
  edges: Edge[];
  metadata?: Record<string, any>;
}

export enum SystemState {
  IDLE = 0,
  ERROR = -1,
  MAPPING = 2,
  NAVIGATION = 3,
  RELOCATION_OPEN = 4,
  LOCALIZATION_COMPLETE = 5,
  NAVIGATION_NODE_OPEN = 6,
}

export const SystemStateNames: Record<number, string> = {
  0: '空闲',
  '-1': '错误',
  2: '建图中',
  3: '导航中',
  4: '重定位开启',
  5: '定位完成',
  6: '导航节点开启',
};
