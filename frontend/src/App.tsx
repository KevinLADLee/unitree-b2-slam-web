import AppLayout from './components/Layout/AppLayout'
import { SystemStatusProvider } from './contexts/SystemStatusContext'

function App() {
  return (
    <SystemStatusProvider>
      <AppLayout />
    </SystemStatusProvider>
  )
}

export default App
