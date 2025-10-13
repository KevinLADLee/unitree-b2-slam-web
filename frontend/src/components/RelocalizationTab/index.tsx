import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Stack,
  Alert,
  CircularProgress,
  Grid,
} from '@mui/material';
import { relocalizationAPI } from '../../services/api';
import type { Feedback, PoseInput } from '../../types';

export default function RelocalizationTab() {
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pose, setPose] = useState<PoseInput>({ x: 0, y: 0, yaw: 0 });

  const handleStartReloc = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await relocalizationAPI.start();
      setFeedback(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求失败');
    } finally {
      setLoading(false);
    }
  };

  const handleInitPose = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await relocalizationAPI.init(pose);
      setFeedback(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography
        variant="h5"
        gutterBottom
        sx={{
          fontWeight: 600,
          letterSpacing: '0.02em',
          borderBottom: '2px solid #2196f3',
          pb: 1,
          mb: 3,
        }}
      >
        RELOCALIZATION CONTROL
      </Typography>

      <Stack spacing={3}>
        {/* 开始重定位 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              重定位操作
            </Typography>
            <Button
              variant="contained"
              color="primary"
              size="large"
              onClick={handleStartReloc}
              disabled={loading}
              fullWidth
            >
              开始重定位
            </Button>
          </CardContent>
        </Card>

        {/* 初始化位姿 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              重定位初始化
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              给定初始位姿进行重定位
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="X 坐标 (m)"
                  type="number"
                  value={pose.x}
                  onChange={(e) =>
                    setPose({ ...pose, x: parseFloat(e.target.value) || 0 })
                  }
                  inputProps={{ step: 0.1 }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Y 坐标 (m)"
                  type="number"
                  value={pose.y}
                  onChange={(e) =>
                    setPose({ ...pose, y: parseFloat(e.target.value) || 0 })
                  }
                  inputProps={{ step: 0.1 }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Yaw 角 (rad)"
                  type="number"
                  value={pose.yaw}
                  onChange={(e) =>
                    setPose({ ...pose, yaw: parseFloat(e.target.value) || 0 })
                  }
                  inputProps={{ step: 0.1 }}
                />
              </Grid>
            </Grid>

            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                color="secondary"
                onClick={handleInitPose}
                disabled={loading}
                fullWidth
              >
                设置初始位姿
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* 反馈 */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            错误: {error}
          </Alert>
        )}

        {feedback && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                最新反馈
              </Typography>
              <Stack spacing={1}>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  <strong>命令ID:</strong> {feedback.index}
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  <strong>状态:</strong>{' '}
                  {feedback.feedback === 1 ? '成功' : '失败'}
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  <strong>系统状态:</strong> {feedback.state}
                </Typography>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  <strong>消息:</strong> {feedback.notice}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        )}
      </Stack>
    </Box>
  );
}
