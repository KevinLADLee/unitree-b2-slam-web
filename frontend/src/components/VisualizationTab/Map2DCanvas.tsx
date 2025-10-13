import { useRef, useEffect } from 'react';
import type { OccupancyGrid, Odometry, Trajectory, LaserScan } from '../../types';

interface Map2DCanvasProps {
  occupancyGrid: OccupancyGrid | null;
  odometry: Odometry | null;
  trajectory: Trajectory | null;
  laserScan: LaserScan | null;
  width: number;
  height: number;
  showLaserScan: boolean;
}

export default function Map2DCanvas({
  occupancyGrid,
  odometry,
  trajectory,
  laserScan,
  width,
  height,
  showLaserScan,
}: Map2DCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 清空画布
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, width, height);

    if (!occupancyGrid) {
      // 显示等待文字
      ctx.fillStyle = '#666';
      ctx.font = '16px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('Loading map data...', width / 2, height / 2);
      return;
    }

    // 绘制 OccupancyGrid 地图
    drawOccupancyGrid(ctx, occupancyGrid, width, height);

    // 绘制激光扫描
    if (showLaserScan && laserScan && odometry) {
      drawLaserScan(ctx, laserScan, odometry, occupancyGrid, width, height);
    }

    // 绘制轨迹
    if (trajectory && trajectory.points.length > 0) {
      drawTrajectory(ctx, trajectory, occupancyGrid, width, height);
    }

    // 绘制机器人位置
    if (odometry) {
      drawRobot(ctx, odometry, occupancyGrid, width, height);
    }
  }, [occupancyGrid, odometry, trajectory, laserScan, width, height, showLaserScan]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{
        border: '1px solid #333',
        borderRadius: '4px',
      }}
    />
  );
}

// 绘制 OccupancyGrid
function drawOccupancyGrid(
  ctx: CanvasRenderingContext2D,
  grid: OccupancyGrid,
  canvasWidth: number,
  canvasHeight: number
) {
  const { width: gridWidth, height: gridHeight } = grid.info;
  const { data } = grid;

  // 计算缩放比例（保持宽高比）
  const scaleX = canvasWidth / gridWidth;
  const scaleY = canvasHeight / gridHeight;
  const scale = Math.min(scaleX, scaleY);

  // 计算居中偏移
  const offsetX = (canvasWidth - gridWidth * scale) / 2;
  const offsetY = (canvasHeight - gridHeight * scale) / 2;

  // 使用 ImageData 批量绘制像素（性能优化）
  const imageData = ctx.createImageData(gridWidth, gridHeight);
  const pixels = imageData.data;

  for (let y = 0; y < gridHeight; y++) {
    for (let x = 0; x < gridWidth; x++) {
      const idx = y * gridWidth + x;
      const value = data[idx];

      // 计算像素索引
      const pixelIdx = (y * gridWidth + x) * 4;

      if (value === -1) {
        // 未知区域：深灰色
        pixels[pixelIdx] = 50;
        pixels[pixelIdx + 1] = 50;
        pixels[pixelIdx + 2] = 50;
        pixels[pixelIdx + 3] = 255;
      } else if (value === 0) {
        // 自由空间：浅灰色
        pixels[pixelIdx] = 200;
        pixels[pixelIdx + 1] = 200;
        pixels[pixelIdx + 2] = 200;
        pixels[pixelIdx + 3] = 255;
      } else {
        // 障碍物：黑色（value 越大越黑）
        const intensity = Math.max(0, 255 - value * 2.55);
        pixels[pixelIdx] = intensity;
        pixels[pixelIdx + 1] = intensity;
        pixels[pixelIdx + 2] = intensity;
        pixels[pixelIdx + 3] = 255;
      }
    }
  }

  // 创建临时画布来缩放 ImageData
  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = gridWidth;
  tempCanvas.height = gridHeight;
  const tempCtx = tempCanvas.getContext('2d');
  if (!tempCtx) return;

  tempCtx.putImageData(imageData, 0, 0);

  // 绘制到主画布（翻转Y轴以匹配ROS坐标系）
  ctx.save();
  ctx.translate(offsetX, offsetY + gridHeight * scale);
  ctx.scale(scale, -scale);
  ctx.drawImage(tempCanvas, 0, 0);
  ctx.restore();

  // 保存变换参数供后续绘制使用
  (ctx as any).mapScale = scale;
  (ctx as any).mapOffsetX = offsetX;
  (ctx as any).mapOffsetY = offsetY;
  (ctx as any).gridWidth = gridWidth;
  (ctx as any).gridHeight = gridHeight;
  (ctx as any).gridResolution = grid.info.resolution;
  (ctx as any).gridOrigin = grid.info.origin;
}

// 世界坐标转换为画布坐标
function worldToCanvas(
  worldX: number,
  worldY: number,
  ctx: any,
  grid: OccupancyGrid
): { x: number; y: number } {
  const { origin, resolution, width, height } = grid.info;

  // 世界坐标 -> 地图坐标（像素）
  const mapX = (worldX - origin.position.x) / resolution;
  const mapY = (worldY - origin.position.y) / resolution;

  // 地图坐标 -> 画布坐标（考虑缩放和翻转）
  const canvasX = ctx.mapOffsetX + mapX * ctx.mapScale;
  const canvasY = ctx.mapOffsetY + (height - mapY) * ctx.mapScale;

  return { x: canvasX, y: canvasY };
}

// 绘制机器人
function drawRobot(
  ctx: CanvasRenderingContext2D,
  odom: Odometry,
  grid: OccupancyGrid,
  canvasWidth: number,
  canvasHeight: number
) {
  const { x, y } = odom.pose.pose.position;
  const { z: qz, w: qw } = odom.pose.pose.orientation;

  // 计算 yaw 角度
  const yaw = Math.atan2(2 * qw * qz, 1 - 2 * qz * qz);

  const pos = worldToCanvas(x, y, ctx, grid);

  // 绘制机器人本体（圆形）
  ctx.fillStyle = '#2196f3';
  ctx.beginPath();
  ctx.arc(pos.x, pos.y, 8, 0, Math.PI * 2);
  ctx.fill();

  // 绘制朝向箭头
  ctx.strokeStyle = '#ff5722';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(pos.x, pos.y);
  const arrowLength = 15;
  const arrowX = pos.x + Math.cos(yaw) * arrowLength;
  const arrowY = pos.y - Math.sin(yaw) * arrowLength; // 注意Y轴翻转
  ctx.lineTo(arrowX, arrowY);
  ctx.stroke();

  // 绘制外圈高亮
  ctx.strokeStyle = '#2196f3';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(pos.x, pos.y, 12, 0, Math.PI * 2);
  ctx.stroke();
}

// 绘制轨迹
function drawTrajectory(
  ctx: CanvasRenderingContext2D,
  trajectory: Trajectory,
  grid: OccupancyGrid,
  canvasWidth: number,
  canvasHeight: number
) {
  if (trajectory.points.length < 2) return;

  ctx.strokeStyle = '#4caf50';
  ctx.lineWidth = 2;
  ctx.beginPath();

  const firstPoint = worldToCanvas(trajectory.points[0].x, trajectory.points[0].y, ctx, grid);
  ctx.moveTo(firstPoint.x, firstPoint.y);

  for (let i = 1; i < trajectory.points.length; i++) {
    const point = worldToCanvas(trajectory.points[i].x, trajectory.points[i].y, ctx, grid);
    ctx.lineTo(point.x, point.y);
  }

  ctx.stroke();

  // 绘制轨迹点
  ctx.fillStyle = '#4caf50';
  for (const point of trajectory.points) {
    const pos = worldToCanvas(point.x, point.y, ctx, grid);
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 2, 0, Math.PI * 2);
    ctx.fill();
  }
}

// 绘制激光扫描
function drawLaserScan(
  ctx: CanvasRenderingContext2D,
  scan: LaserScan,
  odom: Odometry,
  grid: OccupancyGrid,
  canvasWidth: number,
  canvasHeight: number
) {
  const { x: robotX, y: robotY } = odom.pose.pose.position;
  const { z: qz, w: qw } = odom.pose.pose.orientation;
  const robotYaw = Math.atan2(2 * qw * qz, 1 - 2 * qz * qz);

  const robotPos = worldToCanvas(robotX, robotY, ctx, grid);

  // 绘制激光扫描点
  ctx.fillStyle = 'rgba(255, 0, 0, 0.6)';
  ctx.strokeStyle = 'rgba(255, 0, 0, 0.3)';
  ctx.lineWidth = 1;

  for (let i = 0; i < scan.ranges.length; i++) {
    const range = scan.ranges[i];

    // 过滤无效点
    if (range < scan.range_min || range > scan.range_max || !isFinite(range)) {
      continue;
    }

    // 计算激光点的角度
    const angle = scan.angle_min + i * scan.angle_increment;

    // 转换到世界坐标系
    const worldAngle = robotYaw + angle;
    const pointX = robotX + range * Math.cos(worldAngle);
    const pointY = robotY + range * Math.sin(worldAngle);

    const pointPos = worldToCanvas(pointX, pointY, ctx, grid);

    // 绘制激光线（可选，半透明）
    ctx.beginPath();
    ctx.moveTo(robotPos.x, robotPos.y);
    ctx.lineTo(pointPos.x, pointPos.y);
    ctx.stroke();

    // 绘制激光点
    ctx.beginPath();
    ctx.arc(pointPos.x, pointPos.y, 2, 0, Math.PI * 2);
    ctx.fill();
  }
}
