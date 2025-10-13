import React, { useRef } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Checkbox,
  Divider,
  Stack,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  SaveAlt,
  FolderOpen,
  Delete,
  DeleteForever,
} from '@mui/icons-material';
import type { Node, Edge } from '../../types';

interface TopologyMapPanelProps {
  nodes: Node[];
  edges: Edge[];
  selectedNodes: string[];
  onSelectedNodesChange: (nodes: string[]) => void;
  onSaveMap: () => void;
  onLoadMap: (file: File) => void;
  onClearMap: () => void;
  onDeleteNode: (name: string) => void;
  loading: boolean;
}

const TopologyMapPanel: React.FC<TopologyMapPanelProps> = ({
  nodes,
  edges,
  selectedNodes,
  onSelectedNodesChange,
  onSaveMap,
  onLoadMap,
  onClearMap,
  onDeleteNode,
  loading,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleToggleNode = (nodeName: string) => {
    if (selectedNodes.includes(nodeName)) {
      onSelectedNodesChange(selectedNodes.filter((n) => n !== nodeName));
    } else {
      onSelectedNodesChange([...selectedNodes, nodeName]);
    }
  };

  const handleSelectAll = () => {
    if (selectedNodes.length === nodes.length) {
      onSelectedNodesChange([]);
    } else {
      onSelectedNodesChange(nodes.map((n) => n.name));
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onLoadMap(file);
      event.target.value = '';
    }
  };

  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h6" gutterBottom>
        Topology Map
      </Typography>

      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <Tooltip title="Save Map">
          <Button
            size="small"
            startIcon={<SaveAlt />}
            onClick={onSaveMap}
            disabled={loading || nodes.length === 0}
            variant="outlined"
          >
            Save
          </Button>
        </Tooltip>

        <Tooltip title="Load Map">
          <Button
            size="small"
            startIcon={<FolderOpen />}
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            variant="outlined"
          >
            Load
          </Button>
        </Tooltip>

        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          style={{ display: 'none' }}
          onChange={handleFileSelect}
        />

        <Tooltip title="Clear All">
          <Button
            size="small"
            startIcon={<DeleteForever />}
            onClick={onClearMap}
            disabled={loading || nodes.length === 0}
            color="error"
            variant="outlined"
          >
            Clear
          </Button>
        </Tooltip>
      </Stack>

      <Divider sx={{ mb: 2 }} />

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Nodes: {nodes.length} | Edges: {edges.length}
        </Typography>
        {nodes.length > 0 && (
          <Button size="small" onClick={handleSelectAll}>
            {selectedNodes.length === nodes.length ? 'Deselect All' : 'Select All'}
          </Button>
        )}
      </Box>

      <Box sx={{ flexGrow: 1, overflow: 'auto', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
        {nodes.length === 0 ? (
          <Box sx={{ p: 2, textAlign: 'center', color: 'text.secondary' }}>
            No nodes in topology map
          </Box>
        ) : (
          <List dense>
            {nodes.map((node) => (
              <ListItem
                key={node.name}
                secondaryAction={
                  <Tooltip title="Delete Node">
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={() => onDeleteNode(node.name)}
                      disabled={loading}
                    >
                      <Delete fontSize="small" />
                    </IconButton>
                  </Tooltip>
                }
                disablePadding
              >
                <ListItemButton onClick={() => handleToggleNode(node.name)} dense>
                  <Checkbox
                    edge="start"
                    checked={selectedNodes.includes(node.name)}
                    tabIndex={-1}
                    disableRipple
                    size="small"
                  />
                  <ListItemText
                    primary={node.name}
                    secondary={`(${node.x.toFixed(2)}, ${node.y.toFixed(2)}, ${node.yaw.toFixed(2)})`}
                    primaryTypographyProps={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
                    secondaryTypographyProps={{ fontFamily: 'monospace', fontSize: '0.75rem' }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </Box>

      <Box sx={{ mt: 2 }}>
        <Typography variant="caption" color="text.secondary">
          Selected: {selectedNodes.length} nodes
        </Typography>
      </Box>
    </Paper>
  );
};

export default TopologyMapPanel;
