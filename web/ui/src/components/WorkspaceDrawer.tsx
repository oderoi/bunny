import React, { useEffect, useState } from 'react'
import { Box, Drawer, IconButton, Typography, Stack, TextField, Button, List, ListItemButton, ListItemText, Divider } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'

type Workspace = { id: string, name: string, projects: { id: string, name: string, description?: string, visibility?: string }[] }

export default function WorkspaceDrawer({open, onClose, onChanged}:{open:boolean, onClose:()=>void, onChanged?: (active:{workspace_id:string, project_id:string})=>void}){
  const [data, setData] = useState<any>(null)
  const [wsName, setWsName] = useState('')
  const [prjName, setPrjName] = useState('')

  useEffect(()=>{
    if(!open) return
    ;(async()=>{
      try{ const r = await fetch('/api/workspaces'); setData(await r.json()) }catch(e){ setData(null) }
    })()
  },[open])

  function pick(wsId:string, prjId:string){
    if(!data) return
    const next = {...data, active:{workspace_id: wsId, project_id: prjId}}
    setData(next)
  }

  async function save(){
    if(!data) return
    await fetch('/api/workspaces', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data) })
    onChanged?.(data.active)
    onClose()
  }

  function addWorkspace(){
    if(!wsName.trim()) return
    const id = wsName.trim().toLowerCase().replace(/\s+/g,'-') + '-' + Math.random().toString(36).slice(2,6)
    const ws: Workspace = { id, name: wsName.trim(), projects: [] }
    setData((d:any)=> ({...d, workspaces:[...(d?.workspaces||[]), ws]}))
    setWsName('')
  }

  function addProject(wsId:string){
    if(!prjName.trim()) return
    const id = prjName.trim().toLowerCase().replace(/\s+/g,'-') + '-' + Math.random().toString(36).slice(2,6)
    setData((d:any)=> ({...d, workspaces: (d.workspaces||[]).map((w:any)=> w.id===wsId? ({...w, projects:[...(w.projects||[]), {id, name: prjName.trim()}]}): w)}))
    setPrjName('')
  }

  if(!data) return null

  const activeWs = data.active?.workspace_id
  const activePrj = data.active?.project_id

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{width:{xs:'100vw', sm:520}, p:2}}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Workspace</Typography>
          <IconButton size="small" onClick={onClose}><CloseIcon fontSize="small"/></IconButton>
        </Stack>
        <Box sx={{ mt:2 }}>
          <Typography variant="subtitle2" sx={{ opacity:0.75, mb:1 }}>Workspaces</Typography>
          <Stack direction="row" spacing={1} sx={{ mb:1 }}>
            <TextField size="small" placeholder="New workspace name" value={wsName} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setWsName(e.target.value)} />
            <Button variant="outlined" onClick={addWorkspace}>Add</Button>
          </Stack>
          <List dense>
            {(data.workspaces||[]).map((w:any)=> (
              <Box key={w.id} sx={{ border:'1px solid var(--border)', borderRadius:1, mb:1 }}>
                <ListItemButton selected={activeWs===w.id} onClick={()=> pick(w.id, (w.projects?.[0]?.id)||'')}>
                  <ListItemText primary={w.name} secondary={`${w.projects?.length||0} projects`} />
                </ListItemButton>
                <Divider />
                <Box sx={{ p:1 }}>
                  <Typography variant="caption" sx={{ opacity:0.7 }}>Projects</Typography>
                  <Stack direction="row" spacing={1} sx={{ my:1 }}>
                    <TextField size="small" placeholder="New project name" value={prjName} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setPrjName(e.target.value)} />
                    <Button size="small" variant="outlined" onClick={()=>addProject(w.id)}>Add</Button>
                  </Stack>
                  <List dense>
                    {(w.projects||[]).map((p:any)=> (
                      <ListItemButton key={p.id} selected={activeWs===w.id && activePrj===p.id} onClick={()=> pick(w.id, p.id)} sx={{ borderRadius:1 }}>
                        <ListItemText primary={p.name} />
                      </ListItemButton>
                    ))}
                    {(!w.projects || w.projects.length===0) && (
                      <ListItemButton disabled><ListItemText primary="No projects" /></ListItemButton>
                    )}
                  </List>
                </Box>
              </Box>
            ))}
          </List>
        </Box>
        <Divider sx={{my:2}} />
        <Stack direction="row" spacing={1} justifyContent="flex-end">
          <Button onClick={onClose}>Close</Button>
          <Button variant="contained" onClick={save}>Save</Button>
        </Stack>
      </Box>
    </Drawer>
  )
}


