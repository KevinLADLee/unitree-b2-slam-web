import { useState } from 'react';
import {
  AppBar,
  Box,
  Toolbar,
  Typography,
  Tabs,
  Tab,
  Container,
  Paper,
  Divider,
} from '@mui/material';
import MappingTab from '../MappingTab';
import RelocalizationTab from '../RelocalizationTab';
import TopologyAndTaskTab from '../TopologyAndTaskTab';
import VisualizationTab from '../VisualizationTab';
import StatusTab from '../StatusTab';
import GlobalStatusIndicator from '../GlobalStatusIndicator';

export default function AppLayout() {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Header */}
      <AppBar
        position="static"
        sx={{
          backgroundColor: '#1a2332',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.4)',
        }}
      >
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                letterSpacing: '0.05em',
                color: '#2196f3',
              }}
            >
              UNITREE B2
            </Typography>
            <Divider orientation="vertical" flexItem sx={{ borderColor: 'rgba(255, 255, 255, 0.2)' }} />
            <Typography
              variant="subtitle1"
              sx={{
                color: 'text.secondary',
                fontWeight: 400,
                letterSpacing: '0.02em',
              }}
            >
              SLAM 导航控制系统
            </Typography>
          </Box>
          <GlobalStatusIndicator />
        </Toolbar>
      </AppBar>

      {/* Tabs Navigation */}
      <Paper
        sx={{
          backgroundColor: '#0f1821',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        }}
        elevation={0}
      >
        <Container maxWidth="xl">
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              '& .MuiTab-root': {
                minHeight: 56,
                textTransform: 'none',
                fontWeight: 500,
                fontSize: '0.9rem',
                color: 'text.secondary',
                letterSpacing: '0.02em',
                '&.Mui-selected': {
                  color: '#2196f3',
                  fontWeight: 600,
                },
              },
              '& .MuiTabs-indicator': {
                height: 3,
                backgroundColor: '#2196f3',
              },
            }}
          >
            <Tab label="建图" />
            <Tab label="重定位" />
            <Tab label="拓扑与任务" />
            <Tab label="可视化" />
            <Tab label="状态" />
          </Tabs>
        </Container>
      </Paper>

      {/* Main Content */}
      <Container
        maxWidth="xl"
        sx={{
          flex: 1,
          py: 4,
        }}
      >
        <Box role="tabpanel" hidden={tabValue !== 0}>
          {tabValue === 0 && <MappingTab />}
        </Box>
        <Box role="tabpanel" hidden={tabValue !== 1}>
          {tabValue === 1 && <RelocalizationTab />}
        </Box>
        <Box role="tabpanel" hidden={tabValue !== 2}>
          {tabValue === 2 && <TopologyAndTaskTab />}
        </Box>
        <Box role="tabpanel" hidden={tabValue !== 3}>
          {tabValue === 3 && <VisualizationTab />}
        </Box>
        <Box role="tabpanel" hidden={tabValue !== 4}>
          {tabValue === 4 && <StatusTab />}
        </Box>
      </Container>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 2,
          px: 2,
          backgroundColor: '#0f1821',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        }}
      >
        <Container maxWidth="xl">
          <Typography
            variant="body2"
            align="center"
            sx={{
              color: 'text.secondary',
              fontFamily: 'monospace',
              fontSize: '0.75rem',
            }}
          >
            后端: http://localhost:8000 | 前端: http://localhost:5173 | 阶段一: 开发模式
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}
