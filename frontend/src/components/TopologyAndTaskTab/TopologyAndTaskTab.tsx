import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Alert,
} from '@mui/material';
import type { Node, Edge, TopologyMap, NavigationTask, CurrentPosition } from '../../types';
import { topologyAPI, positionAPI, taskAPI } from '../../services/api';
import TopologyMapPanel from './TopologyMapPanel';
import PositionPanel from './PositionPanel';
import TaskPanel from './TaskPanel';

const TopologyAndTaskTab: React.FC = () => {
  // State management
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [tasks, setTasks] = useState<NavigationTask[]>([]);
  const [currentPosition, setCurrentPosition] = useState<CurrentPosition | null>(null);
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  // Load data on mount
  useEffect(() => {
    loadTopologyData();
    loadTasks();
    loadPosition();
  }, []);

  // Auto-refresh position every 2 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadPosition();
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const loadTopologyData = async () => {
    try {
      const [nodesRes, edgesRes] = await Promise.all([
        topologyAPI.getAllNodes(),
        topologyAPI.getAllEdges(),
      ]);
      setNodes(nodesRes.data);
      setEdges(edgesRes.data);
    } catch (err: any) {
      setError(`Failed to load topology data: ${err.message}`);
    }
  };

  const loadTasks = async () => {
    try {
      const res = await taskAPI.getAll();
      setTasks(res.data);
    } catch (err: any) {
      setError(`Failed to load tasks: ${err.message}`);
    }
  };

  const loadPosition = async () => {
    try {
      const res = await positionAPI.getCurrent();
      setCurrentPosition(res.data);
    } catch (err: any) {
      // Silently fail for position updates
      console.error('Failed to load position:', err);
    }
  };

  const handleSaveMap = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const res = await topologyAPI.getMap();
      const map = res.data;
      const blob = new Blob([JSON.stringify(map, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `topology_map_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setSuccess('Topology map saved successfully');
    } catch (err: any) {
      setError(`Failed to save map: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMap = async (file: File) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const text = await file.text();
      const map: TopologyMap = JSON.parse(text);
      await topologyAPI.loadMap(map);
      await loadTopologyData();
      setSuccess(`Loaded ${map.nodes.length} nodes and ${map.edges.length} edges`);
    } catch (err: any) {
      setError(`Failed to load map: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClearMap = async () => {
    if (!window.confirm('Are you sure you want to clear the entire topology map?')) {
      return;
    }
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await topologyAPI.clearMap();
      await loadTopologyData();
      setSelectedNodes([]);
      setSuccess('Topology map cleared successfully');
    } catch (err: any) {
      setError(`Failed to clear map: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteNode = async (name: string) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await topologyAPI.deleteItem(name);
      await loadTopologyData();
      setSelectedNodes(selectedNodes.filter((n) => n !== name));
      setSuccess(`Node '${name}' deleted successfully`);
    } catch (err: any) {
      setError(`Failed to delete node: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRecordWaypoint = async (name: string) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const res = await positionAPI.recordWaypoint(name);
      await loadTopologyData();
      setSuccess(res.data.notice);
    } catch (err: any) {
      setError(`Failed to record waypoint: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async (task: NavigationTask) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const res = await taskAPI.create(task);
      await loadTasks();
      setSuccess(res.data.notice);
    } catch (err: any) {
      setError(`Failed to create task: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTask = async (taskId: string, task: NavigationTask) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const res = await taskAPI.update(taskId, task);
      await loadTasks();
      setSuccess(res.data.notice);
    } catch (err: any) {
      setError(`Failed to update task: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const res = await taskAPI.delete(taskId);
      await loadTasks();
      setSuccess(res.data.notice);
    } catch (err: any) {
      setError(`Failed to delete task: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteTask = async (taskId: string) => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const res = await taskAPI.execute(taskId);
      setSuccess(res.data.notice);
    } catch (err: any) {
      setError(`Failed to execute task: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Topology & Task Management
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess('')} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Grid container spacing={2}>
        {/* Left: Topology Map Panel */}
        <Grid item xs={12} md={4}>
          <TopologyMapPanel
            nodes={nodes}
            edges={edges}
            selectedNodes={selectedNodes}
            onSelectedNodesChange={setSelectedNodes}
            onSaveMap={handleSaveMap}
            onLoadMap={handleLoadMap}
            onClearMap={handleClearMap}
            onDeleteNode={handleDeleteNode}
            loading={loading}
          />
        </Grid>

        {/* Center: Real-time Position Panel */}
        <Grid item xs={12} md={4}>
          <PositionPanel
            currentPosition={currentPosition}
            onRecordWaypoint={handleRecordWaypoint}
            loading={loading}
          />
        </Grid>

        {/* Right: Task Management Panel */}
        <Grid item xs={12} md={4}>
          <TaskPanel
            tasks={tasks}
            nodes={nodes}
            selectedNodes={selectedNodes}
            onCreateTask={handleCreateTask}
            onUpdateTask={handleUpdateTask}
            onDeleteTask={handleDeleteTask}
            onExecuteTask={handleExecuteTask}
            loading={loading}
          />
        </Grid>
      </Grid>
    </Box>
  );
};

export default TopologyAndTaskTab;
