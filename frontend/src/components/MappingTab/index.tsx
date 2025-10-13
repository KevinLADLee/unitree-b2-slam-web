import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  Alert,
  CircularProgress,
} from '@mui/material';
import { mappingAPI } from '../../services/api';
import type { Feedback } from '../../types';

export default function MappingTab() {
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleStartMapping = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await mappingAPI.start();
      setFeedback(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求失败');
    } finally {
      setLoading(false);
    }
  };

  const handleStopMapping = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await mappingAPI.stop();
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
        SLAM 建图控制
      </Typography>

      <Stack spacing={3}>
        {/* 控制按钮 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              建图操作
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleStartMapping}
                disabled={loading}
              >
                开始建图
              </Button>
              <Button
                variant="contained"
                color="warning"
                size="large"
                onClick={handleStopMapping}
                disabled={loading}
              >
                停止建图
              </Button>
              {loading && <CircularProgress size={24} />}
            </Stack>
          </CardContent>
        </Card>

        {/* 说明 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              操作说明
            </Typography>
            <Typography variant="body2" component="div" sx={{ color: 'text.secondary' }}>
              <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                <li>
                  <strong>开始建图</strong>: 自动启动建图节点，开始 SLAM 建图
                </li>
                <li>
                  <strong>停止建图</strong>: 自动保存 3D 地图并关闭建图节点
                </li>
              </ul>
            </Typography>
          </CardContent>
        </Card>

        {/* 反馈信息 */}
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
                  <strong>命令 ID:</strong> {feedback.index}
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
