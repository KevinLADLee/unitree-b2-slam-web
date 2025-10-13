import { Box, Button, ButtonGroup, Paper, Typography, Stack } from '@mui/material';
import {
  ArrowUpward,
  ArrowDownward,
  ArrowBack,
  ArrowForward,
  RotateLeft,
  RotateRight,
  RestartAlt,
} from '@mui/icons-material';
import { rosSimAPI } from '../../services/api';

interface MapControlsProps {
  onSimulateMotion: (linear: number, angular: number) => void;
  onResetPose: () => void;
}

export default function MapControls({ onSimulateMotion, onResetPose }: MapControlsProps) {
  const handleMove = (linear: number, angular: number) => {
    onSimulateMotion(linear, angular);
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        机器人控制
      </Typography>

      <Stack spacing={2}>
        {/* 移动控制 */}
        <Box>
          <Typography variant="caption" color="text.secondary" gutterBottom display="block">
            移动控制
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, alignItems: 'center' }}>
            <Button
              variant="contained"
              size="small"
              onClick={() => handleMove(0.5, 0)}
              startIcon={<ArrowUpward />}
            >
              前进
            </Button>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                size="small"
                onClick={() => handleMove(0, 0.5)}
                startIcon={<RotateLeft />}
              >
                左转
              </Button>
              <Button
                variant="contained"
                size="small"
                onClick={() => handleMove(-0.5, 0)}
                startIcon={<ArrowDownward />}
              >
                后退
              </Button>
              <Button
                variant="contained"
                size="small"
                onClick={() => handleMove(0, -0.5)}
                startIcon={<RotateRight />}
              >
                右转
              </Button>
            </Box>
          </Box>
        </Box>

        {/* 重置 */}
        <Button
          variant="outlined"
          color="warning"
          fullWidth
          onClick={onResetPose}
          startIcon={<RestartAlt />}
        >
          重置位姿
        </Button>

        {/* 说明 */}
        <Box sx={{ mt: 2, p: 1, backgroundColor: 'rgba(33, 150, 243, 0.1)', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">
            使用控制按钮模拟机器人运动，观察实时地图更新
          </Typography>
        </Box>
      </Stack>
    </Paper>
  );
}
