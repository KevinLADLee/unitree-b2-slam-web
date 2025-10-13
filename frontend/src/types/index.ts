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

// ==================== ROS Message Types ====================

export interface ROSHeader {
  seq: number;
  stamp: number;
  frame_id: string;
}

export interface Position {
  x: number;
  y: number;
  z: number;
}

export interface Orientation {
  x: number;
  y: number;
  z: number;
  w: number;
}

export interface Pose {
  position: Position;
  orientation: Orientation;
}

export interface PoseWithCovariance {
  pose: Pose;
  covariance: number[];
}

export interface Twist {
  linear: Position;
  angular: Position;
}

export interface TwistWithCovariance {
  twist: Twist;
  covariance: number[];
}

// OccupancyGrid (nav_msgs/OccupancyGrid)
export interface OccupancyGrid {
  header: ROSHeader;
  info: MapMetaData;
  data: number[];  // -1=unknown, 0-100=probability
}

export interface MapMetaData {
  map_load_time: number;
  resolution: number;
  width: number;
  height: number;
  origin: Pose;
}

// LaserScan (sensor_msgs/LaserScan)
export interface LaserScan {
  header: ROSHeader;
  angle_min: number;
  angle_max: number;
  angle_increment: number;
  time_increment: number;
  scan_time: number;
  range_min: number;
  range_max: number;
  ranges: number[];
  intensities: number[];
}

// Odometry (nav_msgs/Odometry)
export interface Odometry {
  header: ROSHeader;
  child_frame_id: string;
  pose: PoseWithCovariance;
  twist: TwistWithCovariance;
}

// Trajectory Point
export interface TrajectoryPoint {
  x: number;
  y: number;
}

export interface Trajectory {
  points: TrajectoryPoint[];
  count: number;
}
