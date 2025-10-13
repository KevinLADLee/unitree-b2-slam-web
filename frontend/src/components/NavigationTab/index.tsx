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
  Grid,
  FormControl,
  FormLabel,
  RadioGroup,
  Radio,
  FormControlLabel,
} from '@mui/material';
import { navigationAPI } from '../../services/api';
import type { Feedback } from '../../types';

export default function NavigationTab() {
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [singleNode, setSingleNode] = useState('');
  const [multiNodes, setMultiNodes] = useState('');
  const [mode, setMode] = useState<'loop' | 'once'>('loop');
  const [file, setFile] = useState<File | null>(null);

  const handleAPI = async (apiCall: () => Promise<any>) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiCall();
      setFeedback(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadFile = async () => {
    if (!file) {
      setError('请选择文件');
      return;
    }
    await handleAPI(() => navigationAPI.uploadWaypoints(file));
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        🚀 导航控制
      </Typography>

      <Stack spacing={3}>
        {/* 基础控制 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              基础控制
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={4} md={2}>
                <Button
                  fullWidth
                  variant="contained"
                  onClick={() => handleAPI(navigationAPI.start)}
                  disabled={loading}
                >
                  开始 (8)
                </Button>
              </Grid>
              <Grid item xs={6} sm={4} md={2}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={() => handleAPI(navigationAPI.pause)}
                  disabled={loading}
                >
                  暂停 (13)
                </Button>
              </Grid>
              <Grid item xs={6} sm={4} md={2}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={() => handleAPI(navigationAPI.resume)}
                  disabled={loading}
                >
                  恢复 (14)
                </Button>
              </Grid>
              <Grid item xs={6} sm={4} md={2}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={() => handleAPI(navigationAPI.returnToStart)}
                  disabled={loading}
                >
                  返回 (15)
                </Button>
              </Grid>
              <Grid item xs={12} sm={8} md={4}>
                <Button
                  fullWidth
                  variant="contained"
                  color="error"
                  onClick={() => handleAPI(navigationAPI.stop)}
                  disabled={loading}
                >
                  紧急停止 (99)
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* 单节点导航 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              单节点导航 (Cmd: 9)
            </Typography>
            <Stack direction="row" spacing={2}>
              <TextField
                fullWidth
                label="节点名称"
                value={singleNode}
                onChange={(e) => setSingleNode(e.target.value)}
                placeholder="例如: node_1"
              />
              <Button
                variant="contained"
                onClick={() =>
                  handleAPI(() =>
                    navigationAPI.single({ node_name: singleNode })
                  )
                }
                disabled={loading || !singleNode}
              >
                导航
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* 多节点导航 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              多节点导航
            </Typography>
            <Stack spacing={2}>
              <TextField
                fullWidth
                label="节点列表 (逗号分隔)"
                value={multiNodes}
                onChange={(e) => setMultiNodes(e.target.value)}
                placeholder="例如: node_1,node_2,node_3"
              />
              <FormControl>
                <FormLabel>模式</FormLabel>
                <RadioGroup
                  row
                  value={mode}
                  onChange={(e) => setMode(e.target.value as 'loop' | 'once')}
                >
                  <FormControlLabel
                    value="loop"
                    control={<Radio />}
                    label="循环 (Cmd: 10)"
                  />
                  <FormControlLabel
                    value="once"
                    control={<Radio />}
                    label="单次 (Cmd: 11)"
                  />
                </RadioGroup>
              </FormControl>
              <Button
                variant="contained"
                onClick={() => {
                  const node_names = multiNodes.split(',').map((n) => n.trim());
                  const apiCall =
                    mode === 'loop'
                      ? navigationAPI.multiLoop
                      : navigationAPI.multiOnce;
                  handleAPI(() => apiCall({ node_names, mode }));
                }}
                disabled={loading || !multiNodes}
              >
                开始多节点导航
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* JSON 文件上传 */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📁 JSON 路点文件上传
            </Typography>
            <Stack direction="row" spacing={2} alignItems="center">
              <Button variant="outlined" component="label">
                选择文件
                <input
                  type="file"
                  accept=".json"
                  hidden
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
              </Button>
              {file && <Typography variant="body2">{file.name}</Typography>}
              <Button
                variant="contained"
                onClick={handleUploadFile}
                disabled={loading || !file}
              >
                上传并导航
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* 反馈 */}
        {error && <Alert severity="error">{error}</Alert>}
        {feedback && (
          <Alert severity={feedback.feedback === 1 ? 'success' : 'error'}>
            {feedback.notice}
          </Alert>
        )}
      </Stack>
    </Box>
  );
}
