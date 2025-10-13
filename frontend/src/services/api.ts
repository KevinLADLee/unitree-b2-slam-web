import axios from 'axios';
import type {
  Feedback,
  Node,
  Edge,
  SystemStatus,
  PoseInput,
  NavigationTarget,
  NavigationTargets,
  NavigationTask,
  CurrentPosition,
  TopologyMap,
  OccupancyGrid,
  LaserScan,
  Odometry,
  Trajectory,
} from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==================== 建图 API ====================

export const mappingAPI = {
  start: () => apiClient.post<Feedback>('/mapping/start'),
  stop: () => apiClient.post<Feedback>('/mapping/stop'),
};

// ==================== 重定位 API ====================

export const relocalizationAPI = {
  start: () => apiClient.post<Feedback>('/reloc/start'),
  init: (pose: PoseInput) => apiClient.post<Feedback>('/reloc/init', pose),
};

// ==================== 导航 API ====================

export const navigationAPI = {
  start: () => apiClient.post<Feedback>('/nav/start'),
  single: (target: NavigationTarget) =>
    apiClient.post<Feedback>('/nav/single', target),
  multiLoop: (targets: NavigationTargets) =>
    apiClient.post<Feedback>('/nav/multi-loop', targets),
  multiOnce: (targets: NavigationTargets) =>
    apiClient.post<Feedback>('/nav/multi-once', targets),
  pause: () => apiClient.post<Feedback>('/nav/pause'),
  resume: () => apiClient.post<Feedback>('/nav/resume'),
  returnToStart: () => apiClient.post<Feedback>('/nav/return'),
  stop: () => apiClient.post<Feedback>('/nav/stop'),
  uploadWaypoints: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post<Feedback>('/nav/waypoints', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// ==================== 拓扑 API ====================

export const topologyAPI = {
  addNode: (node: Node) => apiClient.post<Feedback>('/topo/node', node),
  addEdge: (edge: Edge) => apiClient.post<Feedback>('/topo/edge', edge),
  deleteItem: (name: string) => apiClient.delete<Feedback>(`/topo/${name}`),
  queryItem: (name: string) => apiClient.get(`/topo/query/${name}`),
  getAllNodes: () => apiClient.get<Node[]>('/topo/nodes'),
  getAllEdges: () => apiClient.get<Edge[]>('/topo/edges'),
  // 拓扑地图文件操作
  getMap: () => apiClient.get<TopologyMap>('/topo/map'),
  loadMap: (map: TopologyMap) => apiClient.post<Feedback>('/topo/map/load', map),
  clearMap: () => apiClient.post<Feedback>('/topo/map/clear'),
};

// ==================== 状态 API ====================

export const statusAPI = {
  getStatus: () => apiClient.get<SystemStatus>('/status'),
  getFeedback: (limit = 20) =>
    apiClient.get<Feedback[]>('/feedback', { params: { limit } }),
};

// ==================== 实时位置 API ====================

export const positionAPI = {
  getCurrent: () => apiClient.get<CurrentPosition>('/position/current'),
  recordWaypoint: (name: string) =>
    apiClient.post<Feedback>('/position/record-waypoint', null, { params: { name } }),
};

// ==================== 导航任务 API ====================

export const taskAPI = {
  create: (task: NavigationTask) => apiClient.post<Feedback>('/task/create', task),
  getAll: () => apiClient.get<NavigationTask[]>('/task/list'),
  getById: (taskId: string) => apiClient.get<NavigationTask>(`/task/${taskId}`),
  update: (taskId: string, task: NavigationTask) =>
    apiClient.put<Feedback>(`/task/${taskId}`, task),
  delete: (taskId: string) => apiClient.delete<Feedback>(`/task/${taskId}`),
  execute: (taskId: string) => apiClient.post<Feedback>(`/task/${taskId}/execute`),
};

// ==================== ROS 模拟 API ====================

export const rosSimAPI = {
  getMap: () => apiClient.get<OccupancyGrid>('/ros/map'),
  getScan: () => apiClient.get<LaserScan>('/ros/scan'),
  getOdom: () => apiClient.get<Odometry>('/ros/odom'),
  simulateMotion: (linear: number, angular: number, dt = 0.1) =>
    apiClient.post('/ros/simulate-motion', null, {
      params: { linear, angular, dt },
    }),
  getTrajectory: () => apiClient.get<Trajectory>('/ros/trajectory'),
  resetPose: () => apiClient.post('/ros/reset-pose'),
};

export default apiClient;
