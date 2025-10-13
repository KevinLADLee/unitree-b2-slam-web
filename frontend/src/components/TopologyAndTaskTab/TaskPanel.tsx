import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  TextField,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Divider,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Add,
  Delete,
  Edit,
  PlayArrow,
  Assignment,
} from '@mui/icons-material';
import type { NavigationTask, Node } from '../../types';

interface TaskPanelProps {
  tasks: NavigationTask[];
  nodes: Node[];
  selectedNodes: string[];
  onCreateTask: (task: NavigationTask) => void;
  onUpdateTask: (taskId: string, task: NavigationTask) => void;
  onDeleteTask: (taskId: string) => void;
  onExecuteTask: (taskId: string) => void;
  loading: boolean;
}

const TaskPanel: React.FC<TaskPanelProps> = ({
  tasks,
  nodes,
  selectedNodes,
  onCreateTask,
  onUpdateTask,
  onDeleteTask,
  onExecuteTask,
  loading,
}) => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<NavigationTask | null>(null);
  const [taskName, setTaskName] = useState('');
  const [taskMode, setTaskMode] = useState<'loop' | 'once'>('loop');
  const [taskNodes, setTaskNodes] = useState<string[]>([]);

  const handleOpenDialog = (task?: NavigationTask) => {
    if (task) {
      setEditingTask(task);
      setTaskName(task.name);
      setTaskMode(task.mode as 'loop' | 'once');
      setTaskNodes(task.node_names);
    } else {
      setEditingTask(null);
      setTaskName('');
      setTaskMode('loop');
      setTaskNodes(selectedNodes);
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingTask(null);
    setTaskName('');
    setTaskMode('loop');
    setTaskNodes([]);
  };

  const handleSaveTask = () => {
    if (!taskName.trim() || taskNodes.length === 0) {
      return;
    }

    const now = new Date().toISOString();
    const task: NavigationTask = {
      id: editingTask?.id || `task_${Date.now()}`,
      name: taskName.trim(),
      node_names: taskNodes,
      mode: taskMode,
      created_at: editingTask?.created_at || now,
      updated_at: now,
    };

    if (editingTask) {
      onUpdateTask(editingTask.id, task);
    } else {
      onCreateTask(task);
    }

    handleCloseDialog();
  };

  const handleDeleteTask = (taskId: string) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      onDeleteTask(taskId);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleString();
    } catch {
      return dateStr;
    }
  };

  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <Assignment color="primary" />
        <Typography variant="h6">
          Navigation Tasks
        </Typography>
      </Box>

      <Button
        variant="contained"
        startIcon={<Add />}
        onClick={() => handleOpenDialog()}
        disabled={loading || selectedNodes.length === 0}
        fullWidth
        sx={{ mb: 2 }}
      >
        Create Task from Selected Nodes
      </Button>

      {selectedNodes.length === 0 && (
        <Typography variant="caption" color="text.secondary" sx={{ mb: 2, textAlign: 'center' }}>
          Select nodes from the topology map to create a task
        </Typography>
      )}

      <Divider sx={{ mb: 2 }} />

      <Typography variant="body2" color="text.secondary" gutterBottom>
        Saved Tasks: {tasks.length}
      </Typography>

      <Box sx={{ flexGrow: 1, overflow: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
        {tasks.length === 0 ? (
          <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
            No tasks created yet
          </Box>
        ) : (
          <List dense>
            {tasks.map((task) => (
              <ListItem
                key={task.id}
                sx={{
                  flexDirection: 'column',
                  alignItems: 'stretch',
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                  '&:last-child': { borderBottom: 'none' },
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="subtitle2" fontFamily="monospace">
                      {task.name}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                      <Chip
                        label={task.mode === 'loop' ? 'Loop' : 'Once'}
                        size="small"
                        color={task.mode === 'loop' ? 'primary' : 'secondary'}
                      />
                      <Chip label={`${task.node_names.length} nodes`} size="small" variant="outlined" />
                    </Box>
                  </Box>

                  <Stack direction="row" spacing={0.5}>
                    <Tooltip title="Execute Task">
                      <IconButton
                        size="small"
                        onClick={() => onExecuteTask(task.id)}
                        disabled={loading}
                        color="success"
                      >
                        <PlayArrow fontSize="small" />
                      </IconButton>
                    </Tooltip>

                    <Tooltip title="Edit Task">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(task)}
                        disabled={loading}
                      >
                        <Edit fontSize="small" />
                      </IconButton>
                    </Tooltip>

                    <Tooltip title="Delete Task">
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteTask(task.id)}
                        disabled={loading}
                        color="error"
                      >
                        <Delete fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </Box>

                <Typography variant="caption" color="text.secondary" fontFamily="monospace">
                  Nodes: {task.node_names.join(' → ')}
                </Typography>

                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                  Created: {formatDate(task.created_at)}
                </Typography>
              </ListItem>
            ))}
          </List>
        )}
      </Box>

      {/* Create/Edit Task Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingTask ? 'Edit Task' : 'Create New Task'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Task Name"
              fullWidth
              value={taskName}
              onChange={(e) => setTaskName(e.target.value)}
              placeholder="e.g., patrol_route_1"
            />

            <FormControl fullWidth>
              <InputLabel>Mode</InputLabel>
              <Select
                value={taskMode}
                onChange={(e) => setTaskMode(e.target.value as 'loop' | 'once')}
                label="Mode"
              >
                <MenuItem value="loop">Loop (循环)</MenuItem>
                <MenuItem value="once">Once (单次)</MenuItem>
              </Select>
            </FormControl>

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Navigation Sequence ({taskNodes.length} nodes)
              </Typography>
              <Box sx={{ p: 1.5, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="body2" fontFamily="monospace">
                  {taskNodes.length > 0 ? taskNodes.join(' → ') : 'No nodes selected'}
                </Typography>
              </Box>
            </Box>

            <Button
              variant="outlined"
              onClick={() => setTaskNodes(selectedNodes)}
              disabled={selectedNodes.length === 0}
            >
              Use Currently Selected Nodes ({selectedNodes.length})
            </Button>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSaveTask}
            variant="contained"
            disabled={!taskName.trim() || taskNodes.length === 0}
          >
            {editingTask ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default TaskPanel;
