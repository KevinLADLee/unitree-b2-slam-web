import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Stack,
  Alert,
  Grid,
  List,
  ListItem,
  ListItemText,
  IconButton,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { topologyAPI } from '../../services/api';
import type { Feedback, Node, Edge } from '../../types';

export default function TopologyTab() {
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  const [newNode, setNewNode] = useState<Node>({
    name: '',
    x: 0,
    y: 0,
    z: 0,
    yaw: 0,
  });

  const [newEdge, setNewEdge] = useState<Edge>({
    name: '',
    start_node: '',
    end_node: '',
    length: 0,
    speed: 0.5,
  });

  const loadTopology = async () => {
    try {
      const [nodesRes, edgesRes] = await Promise.all([
        topologyAPI.getAllNodes(),
        topologyAPI.getAllEdges(),
      ]);
      setNodes(nodesRes.data);
      setEdges(edgesRes.data);
    } catch (err) {
      console.error('Failed to load topology:', err);
    }
  };

  useEffect(() => {
    loadTopology();
  }, []);

  const handleAddNode = async () => {
    if (!newNode.name) {
      setError('请输入节点名称');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await topologyAPI.addNode(newNode);
      setFeedback(response.data);
      setNewNode({ name: '', x: 0, y: 0, z: 0, yaw: 0 });
      await loadTopology();
    } catch (err) {
      setError(err instanceof Error ? err.message : '添加失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAddEdge = async () => {
    if (!newEdge.name || !newEdge.start_node || !newEdge.end_node) {
      setError('请填写完整的边信息');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await topologyAPI.addEdge(newEdge);
      setFeedback(response.data);
      setNewEdge({ name: '', start_node: '', end_node: '', length: 0, speed: 0.5 });
      await loadTopology();
    } catch (err) {
      setError(err instanceof Error ? err.message : '添加失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`确定删除 ${name}?`)) return;
    setLoading(true);
    setError(null);
    try {
      const response = await topologyAPI.deleteItem(name);
      setFeedback(response.data);
      await loadTopology();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        🗺️ 拓扑地图管理
      </Typography>

      <Grid container spacing={3}>
        {/* 节点管理 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                节点管理
              </Typography>
              <Stack spacing={2}>
                <TextField
                  fullWidth
                  label="节点名称"
                  value={newNode.name}
                  onChange={(e) => setNewNode({ ...newNode, name: e.target.value })}
                />
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="X (m)"
                      type="number"
                      value={newNode.x}
                      onChange={(e) =>
                        setNewNode({ ...newNode, x: parseFloat(e.target.value) || 0 })
                      }
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Y (m)"
                      type="number"
                      value={newNode.y}
                      onChange={(e) =>
                        setNewNode({ ...newNode, y: parseFloat(e.target.value) || 0 })
                      }
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Z (m)"
                      type="number"
                      value={newNode.z}
                      onChange={(e) =>
                        setNewNode({ ...newNode, z: parseFloat(e.target.value) || 0 })
                      }
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Yaw (rad)"
                      type="number"
                      value={newNode.yaw}
                      onChange={(e) =>
                        setNewNode({ ...newNode, yaw: parseFloat(e.target.value) || 0 })
                      }
                    />
                  </Grid>
                </Grid>
                <Button
                  variant="contained"
                  onClick={handleAddNode}
                  disabled={loading}
                  fullWidth
                >
                  添加节点
                </Button>

                <Typography variant="subtitle2" sx={{ mt: 2 }}>
                  现有节点 ({nodes.length})
                </Typography>
                <List dense>
                  {nodes.map((node) => (
                    <ListItem
                      key={node.name}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          onClick={() => handleDelete(node.name)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      }
                    >
                      <ListItemText
                        primary={node.name}
                        secondary={`(${node.x.toFixed(2)}, ${node.y.toFixed(2)}, ${node.yaw.toFixed(2)})`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* 边管理 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                边管理
              </Typography>
              <Stack spacing={2}>
                <TextField
                  fullWidth
                  label="边名称"
                  value={newEdge.name}
                  onChange={(e) => setNewEdge({ ...newEdge, name: e.target.value })}
                />
                <TextField
                  fullWidth
                  label="起点节点"
                  value={newEdge.start_node}
                  onChange={(e) =>
                    setNewEdge({ ...newEdge, start_node: e.target.value })
                  }
                />
                <TextField
                  fullWidth
                  label="终点节点"
                  value={newEdge.end_node}
                  onChange={(e) => setNewEdge({ ...newEdge, end_node: e.target.value })}
                />
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="长度 (m)"
                      type="number"
                      value={newEdge.length}
                      onChange={(e) =>
                        setNewEdge({ ...newEdge, length: parseFloat(e.target.value) || 0 })
                      }
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="速度 (0-1)"
                      type="number"
                      value={newEdge.speed}
                      onChange={(e) =>
                        setNewEdge({ ...newEdge, speed: parseFloat(e.target.value) || 0.5 })
                      }
                      inputProps={{ min: 0, max: 1, step: 0.1 }}
                    />
                  </Grid>
                </Grid>
                <Button
                  variant="contained"
                  onClick={handleAddEdge}
                  disabled={loading}
                  fullWidth
                >
                  添加边
                </Button>

                <Typography variant="subtitle2" sx={{ mt: 2 }}>
                  现有边 ({edges.length})
                </Typography>
                <List dense>
                  {edges.map((edge) => (
                    <ListItem
                      key={edge.name}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          onClick={() => handleDelete(edge.name)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      }
                    >
                      <ListItemText
                        primary={edge.name}
                        secondary={`${edge.start_node} → ${edge.end_node}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 反馈 */}
      <Box sx={{ mt: 2 }}>
        {error && <Alert severity="error">{error}</Alert>}
        {feedback && (
          <Alert severity={feedback.feedback === 1 ? 'success' : 'error'}>
            {feedback.notice}
          </Alert>
        )}
      </Box>
    </Box>
  );
}
