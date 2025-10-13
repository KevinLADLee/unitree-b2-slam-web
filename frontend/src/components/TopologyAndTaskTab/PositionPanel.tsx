import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  TextField,
  Grid,
  Divider,
  Stack,
  Chip,
} from '@mui/material';
import { MyLocation, AddLocation } from '@mui/icons-material';
import type { CurrentPosition } from '../../types';

interface PositionPanelProps {
  currentPosition: CurrentPosition | null;
  onRecordWaypoint: (name: string) => void;
  loading: boolean;
}

const PositionPanel: React.FC<PositionPanelProps> = ({
  currentPosition,
  onRecordWaypoint,
  loading,
}) => {
  const [waypointName, setWaypointName] = useState('');

  const handleRecordWaypoint = () => {
    if (waypointName.trim()) {
      onRecordWaypoint(waypointName.trim());
      setWaypointName('');
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString();
    } catch {
      return timestamp;
    }
  };

  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <MyLocation color="primary" />
        <Typography variant="h6">
          Real-time Position
        </Typography>
      </Box>

      {currentPosition ? (
        <>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  X Position (m)
                </Typography>
                <Typography variant="h6" fontFamily="monospace">
                  {currentPosition.x.toFixed(3)}
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={6}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Y Position (m)
                </Typography>
                <Typography variant="h6" fontFamily="monospace">
                  {currentPosition.y.toFixed(3)}
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={6}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Z Position (m)
                </Typography>
                <Typography variant="h6" fontFamily="monospace">
                  {currentPosition.z.toFixed(3)}
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={6}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Yaw Angle (rad)
                </Typography>
                <Typography variant="h6" fontFamily="monospace">
                  {currentPosition.yaw.toFixed(3)}
                </Typography>
              </Box>
            </Grid>
          </Grid>

          <Box sx={{ mb: 2 }}>
            <Chip
              label={`Updated: ${formatTimestamp(currentPosition.timestamp)}`}
              size="small"
              variant="outlined"
              color="success"
            />
          </Box>

          <Divider sx={{ mb: 2 }} />

          <Typography variant="subtitle2" gutterBottom>
            Record Current Position
          </Typography>

          <Stack spacing={2}>
            <TextField
              label="Waypoint Name"
              size="small"
              fullWidth
              value={waypointName}
              onChange={(e) => setWaypointName(e.target.value)}
              placeholder="e.g., waypoint_1"
              disabled={loading}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && waypointName.trim()) {
                  handleRecordWaypoint();
                }
              }}
            />

            <Button
              variant="contained"
              startIcon={<AddLocation />}
              onClick={handleRecordWaypoint}
              disabled={loading || !waypointName.trim()}
              fullWidth
            >
              Record Waypoint
            </Button>
          </Stack>
        </>
      ) : (
        <Box sx={{ textAlign: 'center', color: 'text.secondary', py: 4 }}>
          <Typography variant="body2">
            Waiting for position data...
          </Typography>
          <Typography variant="caption">
            Make sure relocalization is active
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default PositionPanel;
