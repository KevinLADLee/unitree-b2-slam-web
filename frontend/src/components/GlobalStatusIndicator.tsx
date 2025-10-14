import { Box, Chip, CircularProgress, keyframes } from '@mui/material';
import {
  CheckCircle,
  MapOutlined,
  Navigation,
  MyLocation,
  CheckCircleOutline,
  Error,
  HelpOutline,
} from '@mui/icons-material';
import { useSystemStatus } from '../contexts/SystemStatusContext';
import { SystemStateNames } from '../types';

// 脉冲动画
const pulse = keyframes`
  0% {
    box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(33, 150, 243, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(33, 150, 243, 0);
  }
`;

export default function GlobalStatusIndicator() {
  const { systemStatus, loading } = useSystemStatus();

  if (loading && !systemStatus) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={20} />
      </Box>
    );
  }

  if (!systemStatus) {
    return (
      <Chip
        icon={<HelpOutline />}
        label="未知状态"
        size="medium"
        sx={{
          fontWeight: 600,
          backgroundColor: 'rgba(158, 158, 158, 0.2)',
          color: '#9e9e9e',
        }}
      />
    );
  }

  const state = systemStatus.state;
  const stateName = SystemStateNames[state] || `未知 (${state})`;

  // 根据状态返回不同的图标
  const getIcon = () => {
    switch (state) {
      case 0: // IDLE
        return <CheckCircle />;
      case 2: // MAPPING
        return <MapOutlined />;
      case 3: // NAVIGATION
        return <Navigation />;
      case 4: // RELOCATION_OPEN
        return <MyLocation />;
      case 5: // LOCALIZATION_COMPLETE
        return <CheckCircleOutline />;
      case -1: // ERROR
        return <Error />;
      default:
        return <HelpOutline />;
    }
  };

  // 根据状态返回不同的颜色和样式
  const getStatusStyle = () => {
    switch (state) {
      case 0: // IDLE - 绿色
        return {
          backgroundColor: 'rgba(76, 175, 80, 0.2)',
          color: '#4caf50',
          border: '1px solid rgba(76, 175, 80, 0.5)',
        };
      case 2: // MAPPING - 蓝色 + 脉冲动画
        return {
          backgroundColor: 'rgba(33, 150, 243, 0.2)',
          color: '#2196f3',
          border: '1px solid rgba(33, 150, 243, 0.5)',
          animation: `${pulse} 2s infinite`,
        };
      case 3: // NAVIGATION - 橙色 + 脉冲动画
        return {
          backgroundColor: 'rgba(255, 152, 0, 0.2)',
          color: '#ff9800',
          border: '1px solid rgba(255, 152, 0, 0.5)',
          animation: `${pulse} 2s infinite`,
        };
      case 4: // RELOCATION_OPEN - 紫色
        return {
          backgroundColor: 'rgba(156, 39, 176, 0.2)',
          color: '#9c27b0',
          border: '1px solid rgba(156, 39, 176, 0.5)',
        };
      case 5: // LOCALIZATION_COMPLETE - 青色
        return {
          backgroundColor: 'rgba(0, 188, 212, 0.2)',
          color: '#00bcd4',
          border: '1px solid rgba(0, 188, 212, 0.5)',
        };
      case -1: // ERROR - 红色
        return {
          backgroundColor: 'rgba(244, 67, 54, 0.2)',
          color: '#f44336',
          border: '1px solid rgba(244, 67, 54, 0.5)',
        };
      default:
        return {
          backgroundColor: 'rgba(158, 158, 158, 0.2)',
          color: '#9e9e9e',
          border: '1px solid rgba(158, 158, 158, 0.5)',
        };
    }
  };

  return (
    <Chip
      icon={getIcon()}
      label={stateName}
      size="medium"
      sx={{
        fontWeight: 600,
        fontSize: '0.875rem',
        ...getStatusStyle(),
      }}
    />
  );
}
