import React, { useEffect, useRef, useState } from 'react'
import Sidebar from './components/Sidebar'
import SettingsIcon from '@mui/icons-material/Settings'
import SettingsDrawer from './components/SettingsDrawer'
import WorkspaceDrawer from './components/WorkspaceDrawer'
import WorkspacePremiumOutlinedIcon from '@mui/icons-material/WorkspacePremiumOutlined'
import ChatPanel from './components/ChatPanel'
import { 
  Box, 
  Drawer, 
  Toolbar, 
  AppBar, 
  Typography, 
  IconButton, 
  Select, 
  MenuItem, 
  Chip, 
  Snackbar, 
  Alert, 
  Button,
  useMediaQuery,
  useTheme,
  Fab,
  BottomNavigation,
  BottomNavigationAction,
  Paper
} from '@mui/material'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import HelpDrawer from './components/HelpDrawer'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import MenuIcon from '@mui/icons-material/Menu'
import ChatIcon from '@mui/icons-material/Chat'
import SettingsIcon from '@mui/icons-material/Settings'
import HelpIcon from '@mui/icons-material/Help'
import ModelList from './components/ModelList'
import RightPanel from './components/RightPanel'

export default function App(){
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const isTablet = useMediaQuery(theme.breakpoints.down('lg'))
  
  const [models, setModels] = useState<any[]>([])
  const [selected, setSelected] = useState<string | null>(()=>{
    try{ return localStorage.getItem('bunny:selected') }catch(e){return null}
  })
  const [chatSessionId, setChatSessionId] = useState<number>(1)
  const [openMenu, setOpenMenu] = useState(false)
  const [openSettings, setOpenSettings] = useState(false)
  const [openWorkspace, setOpenWorkspace] = useState(false)
  const [openHelp, setOpenHelp] = useState(false)
  const [activeWP, setActiveWP] = useState<{workspace_id?:string, project_id?:string}>(()=>{
    try{ return JSON.parse(localStorage.getItem('bunny:activeWP')||'{}') }catch(e){ return {} }
  })
  const [showNotInstalledAlert, setShowNotInstalledAlert] = useState(false)
  const [mobileTab, setMobileTab] = useState(0) // 0: Chat, 1: Models, 2: Settings
  
  useEffect(()=>{ try{ localStorage.setItem('bunny:activeWP', JSON.stringify(activeWP||{})) }catch(e){} }, [activeWP])
  const [status, setStatus] = useState<any>({running:false})
  const [sidebarExpanded, setSidebarExpanded] = useState<boolean>(()=>{
    try{ return localStorage.getItem('bunny:sidebarExpanded') !== 'false' }catch(e){ return true }
  })

  useEffect(()=>{
    fetch('/api/models').then(r=>r.json()).then(setModels).catch(()=>setModels([]))
  },[])

  // If nothing is selected, default to the first installed model once models load
  useEffect(()=>{
    if(!selected && models && models.length){
      const firstInstalled = models.find(m=>m.installed)
      if(firstInstalled){
        onSelect(firstInstalled.name)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [models])

  const onSelect = (name: string) => {
    const model = models.find(m => m.name === name)
    if (model && !model.installed) {
      setShowNotInstalledAlert(true)
      return
    }
    setSelected(name)
    try{ localStorage.setItem('bunny:selected', name) }catch(e){}
  }

  const selectedModel = models.find(m => m.name === selected)
  const isSelectedModelInstalled = selectedModel?.installed || false

  const downloadModel = async (modelName: string) => {
    try {
      const response = await fetch('/api/models/pull', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelName })
      })
      const data = await response.json()
      if (data.ok) {
        setShowNotInstalledAlert(false)
      }
    } catch (error) {
      console.error('Failed to download model:', error)
    }
  }

  // Mobile-optimized layout
  if (isMobile) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        {/* Mobile App Bar */}
        <AppBar position="static" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
          <Toolbar>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              onClick={() => setOpenMenu(!openMenu)}
              edge="start"
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
              Bunny AI
            </Typography>
            <IconButton color="inherit" onClick={() => setOpenSettings(true)}>
              <SettingsIcon />
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Mobile Content */}
        <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
          {mobileTab === 0 && (
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              {/* Model Selector */}
              <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                <Select
                  value={selected || ''}
                  onChange={(e) => onSelect(e.target.value)}
                  fullWidth
                  size="small"
                >
                  {models.map(model => (
                    <MenuItem key={model.name} value={model.name}>
                      <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                        <Typography variant="body2" sx={{ flexGrow: 1 }}>
                          {model.name}
                        </Typography>
                        <Chip 
                          label={model.installed ? "• installed" : "• not installed"} 
                          size="small" 
                          color={model.installed ? "success" : "default"}
                          sx={{ ml: 1 }}
                        />
                        {!model.installed && (
                          <Button 
                            size="small" 
                            onClick={(e) => {
                              e.stopPropagation()
                              downloadModel(model.name)
                            }}
                            sx={{ ml: 1 }}
                          >
                            Download
                          </Button>
                        )}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </Box>

              {/* Chat Panel */}
              <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
                <ChatPanel 
                  selectedModel={selectedModel}
                  sessionId={chatSessionId}
                  onNewSession={() => setChatSessionId(prev => prev + 1)}
                />
              </Box>
            </Box>
          )}

          {mobileTab === 1 && (
            <Box sx={{ height: '100%', overflow: 'auto', p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Models
              </Typography>
              <ModelList models={models} />
            </Box>
          )}

          {mobileTab === 2 && (
            <Box sx={{ height: '100%', overflow: 'auto', p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Settings
              </Typography>
              <RightPanel models={models} selected={selected} />
            </Box>
          )}
        </Box>

        {/* Mobile Bottom Navigation */}
        <Paper sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: theme.zIndex.appBar }}>
          <BottomNavigation
            value={mobileTab}
            onChange={(event, newValue) => setMobileTab(newValue)}
            showLabels
          >
            <BottomNavigationAction label="Chat" icon={<ChatIcon />} />
            <BottomNavigationAction label="Models" icon={<MenuIcon />} />
            <BottomNavigationAction label="Settings" icon={<SettingsIcon />} />
          </BottomNavigation>
        </Paper>

        {/* Mobile Drawers */}
        <Drawer
          variant="temporary"
          open={openMenu}
          onClose={() => setOpenMenu(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 280 },
          }}
        >
          <Sidebar 
            models={models} 
            selected={selected} 
            onSelect={onSelect}
            expanded={true}
            onToggle={() => {}}
          />
        </Drawer>

        <SettingsDrawer 
          open={openSettings} 
          onClose={() => setOpenSettings(false)}
          activeWP={activeWP}
          setActiveWP={setActiveWP}
        />

        {/* Mobile Snackbar */}
        <Snackbar
          open={showNotInstalledAlert}
          autoHideDuration={6000}
          onClose={() => setShowNotInstalledAlert(false)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert 
            onClose={() => setShowNotInstalledAlert(false)} 
            severity="warning"
            action={
              <Button 
                color="inherit" 
                size="small" 
                onClick={() => selected && downloadModel(selected)}
              >
                Download
              </Button>
            }
          >
            Model not installed - download it first
          </Alert>
        </Snackbar>
      </Box>
    )
  }

  // Tablet/Desktop layout (existing code)
  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* Desktop Sidebar */}
      <Sidebar 
        models={models} 
        selected={selected} 
        onSelect={onSelect}
        expanded={sidebarExpanded}
        onToggle={() => setSidebarExpanded(!sidebarExpanded)}
      />

      {/* Main Content */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Desktop App Bar */}
        <AppBar position="static" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
          <Toolbar>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              onClick={() => setSidebarExpanded(!sidebarExpanded)}
              edge="start"
            >
              {sidebarExpanded ? <ChevronLeftIcon /> : <ChevronRightIcon />}
            </IconButton>
            <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
              Bunny AI
            </Typography>
            <IconButton color="inherit" onClick={() => setOpenSettings(true)}>
              <SettingsIcon />
            </IconButton>
            <IconButton color="inherit" onClick={() => setOpenWorkspace(true)}>
              <WorkspacePremiumOutlinedIcon />
            </IconButton>
            <IconButton color="inherit" onClick={() => setOpenHelp(true)}>
              <HelpOutlineIcon />
            </IconButton>
          </Toolbar>
        </AppBar>

        {/* Desktop Content */}
        <Box sx={{ flexGrow: 1, display: 'flex' }}>
          <Box sx={{ flexGrow: 1 }}>
            <ChatPanel 
              selectedModel={selectedModel}
              sessionId={chatSessionId}
              onNewSession={() => setChatSessionId(prev => prev + 1)}
            />
          </Box>
          <Box sx={{ width: 300, borderLeft: 1, borderColor: 'divider' }}>
            <RightPanel models={models} selected={selected} />
          </Box>
        </Box>
      </Box>

      {/* Desktop Drawers */}
      <SettingsDrawer 
        open={openSettings} 
        onClose={() => setOpenSettings(false)}
        activeWP={activeWP}
        setActiveWP={setActiveWP}
      />
      <WorkspaceDrawer 
        open={openWorkspace} 
        onClose={() => setOpenWorkspace(false)}
        activeWP={activeWP}
        setActiveWP={setActiveWP}
      />
      <HelpDrawer 
        open={openHelp} 
        onClose={() => setOpenHelp(false)}
      />

      {/* Desktop Snackbar */}
      <Snackbar
        open={showNotInstalledAlert}
        autoHideDuration={6000}
        onClose={() => setShowNotInstalledAlert(false)}
      >
        <Alert 
          onClose={() => setShowNotInstalledAlert(false)} 
          severity="warning"
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={() => selected && downloadModel(selected)}
            >
              Download
            </Button>
          }
        >
          Model not installed - download it first
        </Alert>
      </Snackbar>
    </Box>
  )
}
