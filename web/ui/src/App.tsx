import React, { useEffect, useRef, useState } from 'react'
import Sidebar from './components/Sidebar'
import SettingsIcon from '@mui/icons-material/Settings'
import SettingsDrawer from './components/SettingsDrawer'
import WorkspaceDrawer from './components/WorkspaceDrawer'
import WorkspacePremiumOutlinedIcon from '@mui/icons-material/WorkspacePremiumOutlined'
import ChatPanel from './components/ChatPanel'
import { Box, Drawer, Toolbar, AppBar, Typography, IconButton, Select, MenuItem, Chip, Snackbar, Alert, Button } from '@mui/material'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import HelpDrawer from './components/HelpDrawer'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import MenuIcon from '@mui/icons-material/Menu'
//

export default function App(){
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

  // Check if selected model is installed, if not show alert
  const selectedModel = models.find(m=>m.name===selected)
  const isSelectedModelInstalled = selectedModel?.installed || false

  useEffect(()=>{
    let mounted = true
    async function poll(){
      try{
        const r = await fetch('/api/server/status')
        if(!mounted) return
        if(r.ok){ setStatus(await r.json()) } else { setStatus({running:false}) }
      }catch(e){ if(mounted) setStatus({running:false}) }
    }
    poll()
    const id = setInterval(poll, 2500)
    return ()=>{ mounted=false; clearInterval(id) }
  },[])

  // Auto-start the server once per page load if a model is selected and installed
  const triedAutostartRef = useRef(false)
  useEffect(()=>{
    if(triedAutostartRef.current) return
    if(!status?.running && selected){
      // read preferred ports/ctx_size from settings
      const port = (window as any).__bunny_settings?.server?.inference_port || 8081
      const ctx = (window as any).__bunny_settings?.runtime?.ctx_size || 2048
      const sel = models.find(m=>m.name === selected)
      if(sel && sel.installed){
        triedAutostartRef.current = true
        fetch('/api/server/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: selected, port, ctx_size: ctx })
        }).catch(()=>{})
      }
    }
  }, [status?.running, selected, models])

  // Restart server only when the selected model path changes (avoid cancelling in-flight chats)
  const modelChangeInFlightRef = useRef(false)
  const lastDesiredPathRef = useRef<string | undefined>(undefined)
  useEffect(()=>{
    if(!selected) return
    const sel = models.find(m=>m.name === selected)
    if(!sel || !sel.installed) return
    const currentPath = status?.model as string | undefined
    const desiredPath = sel.path as string | undefined
    if(lastDesiredPathRef.current === desiredPath && status?.running && currentPath === desiredPath){
      return
    }
    // Start if not running; restart only if currentPath differs from desiredPath
    const needStart = !status?.running
    const needRestart = !!(status?.running && currentPath && desiredPath && currentPath !== desiredPath)
    if(!needStart && !needRestart) return
    if(modelChangeInFlightRef.current) return
    modelChangeInFlightRef.current = true
    lastDesiredPathRef.current = desiredPath
    ;(async ()=>{
      try{
        if(needRestart){
          try{ await fetch('/api/server/stop', { method: 'POST' }) }catch(e){}
          await new Promise(r=>setTimeout(r, 300))
        }
        const port = (window as any).__bunny_settings?.server?.inference_port || 8081
        const ctx = (window as any).__bunny_settings?.runtime?.ctx_size || 2048
        await fetch('/api/server/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: selected, port, ctx_size: ctx })
        })
      } finally {
        modelChangeInFlightRef.current = false
      }
    })()
  }, [selected, models, status?.running, status?.model])

  function onSelect(m:string|null){
    setSelected(m)
    try{ if(m) localStorage.setItem('bunny:selected', m); else localStorage.removeItem('bunny:selected') }catch(e){}
    
    // Show alert if uninstalled model is selected
    if(m) {
      const model = models.find(mod => mod.name === m)
      if(model && !model.installed) {
        setShowNotInstalledAlert(true)
      }
    }
  }

  function toggleSidebar(expanded?:boolean){
    const next = typeof expanded === 'boolean' ? expanded : !sidebarExpanded
    setSidebarExpanded(next)
    try{ localStorage.setItem('bunny:sidebarExpanded', String(next)) }catch(e){}
  }

  function handleNewChat(){
    setChatSessionId(id => id + 1)
  }

  async function downloadModel(modelName: string){
    try {
      const response = await fetch('/api/models/pull', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelName })
      })
      if(response.ok){
        // Refresh models list to update installed status
        fetch('/api/models').then(r=>r.json()).then(setModels).catch(()=>setModels([]))
      }
    } catch (e) {
      console.error('Failed to download model:', e)
    }
  }

  return (
    <Box sx={{display:'flex', height:'100vh'}}>
      <AppBar position="fixed" color="default" elevation={0} sx={{zIndex:1200, borderBottom:'1px solid rgba(255,255,255,0.06)'}}>
        <Toolbar variant="dense" sx={{gap:1, minHeight:52, pl:{ xs:0, md: sidebarExpanded? '300px' : 0 }}}>
          <Typography variant="subtitle1" component="div" sx={{fontWeight:700}}>Delta</Typography>
          <IconButton edge="start" onClick={()=>setOpenMenu(s=>!s)} sx={{ml:1, display:{ xs:'inline-flex', md:'none' }}} size="small" aria-label="menu">
            <MenuIcon fontSize="small" />
          </IconButton>
          <Box sx={{flex:1}} />
          <Box sx={{ display:'flex', alignItems:'center', gap:1, mx:'auto' }}>
            <Select size="small" value={selected || ''} displayEmpty onChange={(e)=> onSelect((e.target.value as string)||null)} sx={{minWidth:220, '.MuiSelect-select':{borderRadius:9999, paddingY:0.75, paddingLeft:2, paddingRight:4}, borderRadius:9999}}>
              <MenuItem value=""><em>Select model</em></MenuItem>
              {models.map(m=> (
                <MenuItem key={m.name} value={m.name}>
                  <Box sx={{display:'flex', alignItems:'center', justifyContent:'space-between', width:'100%'}}>
                    <span>{m.name} {m.installed? '• installed':'• not installed'}</span>
                    {!m.installed && (
                      <Button size="small" variant="outlined" onClick={(e)=>{e.stopPropagation(); downloadModel(m.name)}} sx={{ml:1, minWidth:'auto', px:1}}>
                        Download
                      </Button>
                    )}
                  </Box>
                </MenuItem>
              ))}
            </Select>
            <Chip size="small" label={status.running? 'Running':'Stopped'} color={status.running? 'success':'default'} sx={{ borderRadius:9999 }} />
          </Box>
          <Box sx={{flex:1, display:'flex', justifyContent:'flex-end', gap:1}}>
            {activeWP?.workspace_id && (
              <Chip size="small" label={`${activeWP.workspace_id}/${activeWP.project_id||''}`} sx={{ borderRadius:9999 }} />
            )}
            <IconButton size="small" onClick={()=>setOpenWorkspace(true)} sx={{borderRadius:9999}} aria-label="workspace">
              <WorkspacePremiumOutlinedIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={()=>setOpenHelp(true)} sx={{borderRadius:9999}} aria-label="help">
              <HelpOutlineIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={()=>setOpenSettings(true)} sx={{borderRadius:9999}} aria-label="settings">
              <SettingsIcon fontSize="small" />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Mobile: temporary drawer toggled by menu icon */}
      <Drawer open={openMenu} onClose={()=>setOpenMenu(false)} variant="temporary" sx={{ display:{ xs:'block', md:'none' } }}>
        <Box sx={{width:300,p:2}}>
          <Sidebar models={models} selected={selected} onSelect={onSelect} onNewChat={handleNewChat} onOpenSettings={()=>setOpenSettings(true)} onOpenWorkspace={()=>setOpenWorkspace(true)} onOpenHelp={()=>setOpenHelp(true)} />
        </Box>
      </Drawer>

      {/* Desktop: persistent drawer that squeezes chat to the right when open */}
      <Drawer variant="persistent" open={sidebarExpanded} sx={{ display:{ xs:'none', md:'block' }, '& .MuiDrawer-paper':{ width: 300, boxSizing:'border-box', borderRight:'1px solid rgba(255,255,255,0.06)' } }}>
        <Box sx={{ position:'relative', height:'100%', p:1.5 }}>
          <Toolbar variant="dense" sx={{ minHeight: 26 }} />
          <Box sx={{ display:'flex', justifyContent:'flex-end', mb:1 }}>
            <IconButton size="small" aria-label="collapse sidebar" onClick={()=>toggleSidebar(false)} sx={{borderRadius:9999}}>
              <ChevronLeftIcon fontSize="small" />
            </IconButton>
          </Box>
          <Sidebar models={models} selected={selected} onSelect={onSelect} onNewChat={handleNewChat} onOpenSettings={()=>setOpenSettings(true)} onOpenWorkspace={()=>setOpenWorkspace(true)} onOpenHelp={()=>setOpenHelp(true)} />
        </Box>
      </Drawer>

      {/* Desktop: floating expand button when persistent drawer is closed */}
      {!sidebarExpanded && (
        <Box sx={{ display:{ xs:'none', md:'block' } }}>
          <IconButton size="small" onClick={()=>toggleSidebar(true)} aria-label="expand sidebar" sx={{ position:'fixed', left:8, top:8, zIndex:1201, borderRadius:9999 }}>
            <ChevronRightIcon fontSize="small" />
          </IconButton>
        </Box>
      )}

      <Box component="main" sx={{flex:1, display:'flex', flexDirection:'column', pt:8, ml:{ xs:0, md: sidebarExpanded? '300px' : 0 }}}>
        <ChatPanel key={chatSessionId} selectedModel={selectedModel} />
      </Box>

      {/* Settings Drawer */}
      {openSettings && (
        <SettingsDrawer open={openSettings} onClose={()=>setOpenSettings(false)} />
      )}
      {openWorkspace && (
        <WorkspaceDrawer open={openWorkspace} onClose={()=>setOpenWorkspace(false)} onChanged={(a)=> setActiveWP(a)} />
      )}
      {openHelp && (
        <HelpDrawer open={openHelp} onClose={()=>setOpenHelp(false)} />
      )}

      {/* Alert for uninstalled model */}
      <Snackbar 
        open={showNotInstalledAlert} 
        autoHideDuration={6000} 
        onClose={()=>setShowNotInstalledAlert(false)}
        anchorOrigin={{vertical:'top', horizontal:'center'}}
      >
        <Alert 
          onClose={()=>setShowNotInstalledAlert(false)} 
          severity="warning" 
          sx={{ width: '100%' }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={()=>{
                if(selected) downloadModel(selected)
                setShowNotInstalledAlert(false)
              }}
            >
              Download
            </Button>
          }
        >
          Model "{selected}" is not installed. Click Download to install it.
        </Alert>
      </Snackbar>
    </Box>
  )
}
