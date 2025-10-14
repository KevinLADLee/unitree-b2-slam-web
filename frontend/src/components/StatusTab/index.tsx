import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  Alert,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { statusAPI } from '../../services/api';
import { useSystemStatus } from '../../contexts/SystemStatusContext';
import type { Feedback } from '../../types';

export default function StatusTab() {
  const { systemStatus, refetch } = useSystemStatus();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackHistory, setFeedbackHistory] = useState<Feedback[]>([]);

  const loadFeedbackHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const historyRes = await statusAPI.getFeedback();
      setFeedbackHistory(historyRes.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载反馈历史失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    await Promise.all([refetch(), loadFeedbackHistory()]);
  };

  useEffect(() => {
    loadFeedbackHistory();
    // 自动刷新反馈历史间隔 (每5秒)
    const interval = setInterval(loadFeedbackHistory, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStateLabel = (state: number): string => {
    const stateMap: Record<number, string> = {
      0: 'IDLE',
      '-1': 'ERROR',
      2: 'MAPPING',
      3: 'NAVIGATION',
      4: 'RELOCATION_OPEN',
      5: 'LOCALIZATION_COMPLETE',
      6: 'NAVIGATION_NODE_OPEN',
    };
    return stateMap[state] || `UNKNOWN (${state})`;
  };

  const getStateColor = (state: number): 'default' | 'primary' | 'success' | 'error' | 'warning' => {
    if (state === 0) return 'default';
    if (state === -1) return 'error';
    if (state === 2 || state === 3) return 'primary';
    if (state === 5) return 'success';
    return 'warning';
  };

  const getFeedbackColor = (feedback: number): 'success' | 'error' | 'warning' => {
    if (feedback === 1) return 'success';
    if (feedback === 0) return 'error';
    return 'warning';
  };

  const getFeedbackLabel = (feedback: number): string => {
    if (feedback === 1) return '成功';
    if (feedback === 0) return '失败';
    return '等待中';
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography
          variant="h5"
          sx={{
            fontWeight: 600,
            letterSpacing: '0.02em',
            borderBottom: '2px solid #2196f3',
            pb: 1,
          }}
        >
          系统状态监控
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={loading}
        >
          刷新
        </Button>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }}>错误: {error}</Alert>}

      <Stack spacing={3}>
        {/* 当前系统状态 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              当前系统状态
            </Typography>
            {systemStatus ? (
              <Stack spacing={2}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom sx={{ fontFamily: 'monospace' }}>
                    系统状态:
                  </Typography>
                  <Chip
                    label={getStateLabel(systemStatus.state)}
                    color={getStateColor(systemStatus.state)}
                    size="medium"
                    sx={{ fontFamily: 'monospace', fontWeight: 600 }}
                  />
                </Box>
                <Divider />
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                    <strong>命令 ID:</strong> {systemStatus.index}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                    <strong>反馈状态:</strong> {getFeedbackLabel(systemStatus.feedback)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                    <strong>消息:</strong> {systemStatus.notice}
                  </Typography>
                </Box>
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                加载中...
              </Typography>
            )}
          </CardContent>
        </Card>

        {/* 反馈历史 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              反馈历史 ({feedbackHistory.length})
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontFamily: 'monospace' }}>
              最近的命令反馈记录（按时间倒序）
            </Typography>
            {feedbackHistory.length > 0 ? (
              <List>
                {feedbackHistory.map((item, index) => (
                  <Box key={index}>
                    {index > 0 && <Divider />}
                    <ListItem>
                      <ListItemText
                        primary={
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                              命令 {item.index}
                            </Typography>
                            <Chip
                              label={getFeedbackLabel(item.feedback)}
                              color={getFeedbackColor(item.feedback)}
                              size="small"
                              sx={{ fontFamily: 'monospace', fontWeight: 600 }}
                            />
                            <Chip
                              label={getStateLabel(item.state)}
                              color={getStateColor(item.state)}
                              size="small"
                              variant="outlined"
                              sx={{ fontFamily: 'monospace', fontWeight: 600 }}
                            />
                          </Stack>
                        }
                        secondary={
                          <Typography variant="body2" component="span" sx={{ fontFamily: 'monospace' }}>
                            {item.notice}
                          </Typography>
                        }
                      />
                    </ListItem>
                  </Box>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                暂无反馈历史
              </Typography>
            )}
          </CardContent>
        </Card>

        {/* 说明 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              状态说明
            </Typography>
            <Typography variant="body2" component="div" sx={{ color: 'text.secondary', fontFamily: 'monospace' }}>
              <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                <li><strong>IDLE (0)</strong>: 系统空闲，等待指令</li>
                <li><strong>MAPPING (2)</strong>: 正在进行 SLAM 建图</li>
                <li><strong>NAVIGATION (3)</strong>: 正在执行导航任务</li>
                <li><strong>RELOCATION_OPEN (4)</strong>: 重定位功能已开启</li>
                <li><strong>LOCALIZATION_COMPLETE (5)</strong>: 定位完成</li>
                <li><strong>NAVIGATION_NODE_OPEN (6)</strong>: 节点导航已开启</li>
                <li><strong>ERROR (-1)</strong>: 系统错误</li>
              </ul>
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontFamily: 'monospace' }}>
              自动刷新间隔: 5 秒
            </Typography>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
