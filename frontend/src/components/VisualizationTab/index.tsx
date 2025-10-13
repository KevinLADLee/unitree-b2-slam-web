import { useState, useEffect, useRef } from 'react';
import { Box, Typography, Grid, Paper, FormControlLabel, Switch } from '@mui/material';
import { rosSimAPI } from '../../services/api';
import Map2DCanvas from './Map2DCanvas';
import MapControls from './MapControls';
import type { OccupancyGrid, LaserScan, Odometry, Trajectory } from '../../types';

export default function VisualizationTab() {
  const [occupancyGrid, setOccupancyGrid] = useState<OccupancyGrid | null>(null);
  const [laserScan, setLaserScan] = useState<LaserScan | null>(null);
  const [odometry, setOdometry] = useState<Odometry | null>(null);
  const [trajectory, setTrajectory] = useState<Trajectory | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 600 });
  const [showLaserScan, setShowLaserScan] = useState(true);

  // 加载地图数据（一次性）
  useEffect(() => {
    loadMapData();
  }, []);

  // 响应式调整 Canvas 尺寸
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const width = containerRef.current.clientWidth - 32; // 减去 padding
        const height = 600 - 64; // 减去标题和 padding
        setCanvasSize({ width, height });
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // 定时刷新实时数据（激光扫描、里程计、轨迹）
  useEffect(() => {
    const interval = setInterval(() => {
      loadRealtimeData();
    }, 100); // 10 Hz

    return () => clearInterval(interval);
  }, []);

  const loadMapData = async () => {
    try {
      const response = await rosSimAPI.getMap();
      setOccupancyGrid(response.data);
    } catch (err) {
      console.error('Failed to load map:', err);
      setError('Failed to load map data');
    }
  };

  const loadRealtimeData = async () => {
    try {
      const [scanRes, odomRes, trajRes] = await Promise.all([
        rosSimAPI.getScan(),
        rosSimAPI.getOdom(),
        rosSimAPI.getTrajectory(),
      ]);

      setLaserScan(scanRes.data);
      setOdometry(odomRes.data);
      setTrajectory(trajRes.data);
    } catch (err) {
      console.error('Failed to load realtime data:', err);
    }
  };

  const handleSimulateMotion = async (linear: number, angular: number) => {
    try {
      await rosSimAPI.simulateMotion(linear, angular, 0.2);
      // 立即更新数据
      loadRealtimeData();
    } catch (err) {
      console.error('Failed to simulate motion:', err);
    }
  };

  const handleResetPose = async () => {
    try {
      await rosSimAPI.resetPose();
      // 立即更新数据
      loadRealtimeData();
    } catch (err) {
      console.error('Failed to reset pose:', err);
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
        2D 地图可视化
      </Typography>

      <Grid container spacing={2}>
        {/* 左侧：地图可视化区域 */}
        <Grid item xs={12} md={9}>
          <Paper ref={containerRef} sx={{ p: 2, height: '600px', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6">
                实时地图
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={showLaserScan}
                    onChange={(e) => setShowLaserScan(e.target.checked)}
                    color="error"
                  />
                }
                label="激光扫描"
              />
            </Box>
            <Box
              sx={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#1a1a1a',
                borderRadius: 1,
              }}
            >
              <Map2DCanvas
                occupancyGrid={occupancyGrid}
                odometry={odometry}
                trajectory={trajectory}
                laserScan={laserScan}
                width={canvasSize.width}
                height={canvasSize.height}
                showLaserScan={showLaserScan}
              />
            </Box>
          </Paper>
        </Grid>

        {/* 右侧：数据面板 */}
        <Grid item xs={12} md={3}>
          <MapControls
            onSimulateMotion={handleSimulateMotion}
            onResetPose={handleResetPose}
          />

          <Paper sx={{ p: 2, mb: 2, mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              机器人位姿
            </Typography>
            {odometry ? (
              <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                <Box>X: {odometry.pose.pose.position.x.toFixed(3)} m</Box>
                <Box>Y: {odometry.pose.pose.position.y.toFixed(3)} m</Box>
                <Box>
                  Yaw: {(Math.atan2(2 * odometry.pose.pose.orientation.w * odometry.pose.pose.orientation.z, 1 - 2 * odometry.pose.pose.orientation.z ** 2)).toFixed(3)} rad
                </Box>
                <Box sx={{ mt: 1 }}>
                  Linear: {odometry.twist.twist.linear.x.toFixed(2)} m/s
                </Box>
                <Box>Angular: {odometry.twist.twist.angular.z.toFixed(2)} rad/s</Box>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                等待数据...
              </Typography>
            )}
          </Paper>

          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              地图信息
            </Typography>
            {occupancyGrid ? (
              <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                <Box>尺寸: {occupancyGrid.info.width} × {occupancyGrid.info.height}</Box>
                <Box>分辨率: {occupancyGrid.info.resolution} m/pixel</Box>
                <Box>原点: ({occupancyGrid.info.origin.position.x.toFixed(1)}, {occupancyGrid.info.origin.position.y.toFixed(1)})</Box>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                等待数据...
              </Typography>
            )}
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              激光雷达
            </Typography>
            {laserScan ? (
              <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                <Box>扫描点数: {laserScan.ranges.length}</Box>
                <Box>角度范围: {laserScan.angle_min.toFixed(2)} ~ {laserScan.angle_max.toFixed(2)} rad</Box>
                <Box>距离范围: {laserScan.range_min.toFixed(2)} ~ {laserScan.range_max.toFixed(2)} m</Box>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                等待数据...
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
