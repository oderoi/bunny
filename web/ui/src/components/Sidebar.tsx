import React, { useEffect, useMemo, useState } from 'react'
import { Box, List, ListItemButton, ListItemText, Typography, Button, TextField, Stack, Divider, IconButton, Tooltip, Menu, MenuItem, Chip } from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import SearchIcon from '@mui/icons-material/Search'
import MoreVertIcon from '@mui/icons-material/MoreVert'
import PushPinIcon from '@mui/icons-material/PushPin'
import PushPinOutlinedIcon from '@mui/icons-material/PushPinOutlined'
import FolderIcon from '@mui/icons-material/Folder'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import RestoreFromTrashIcon from '@mui/icons-material/RestoreFromTrash'
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import WorkspacePremiumOutlinedIcon from '@mui/icons-material/WorkspacePremiumOutlined'

type Conversation = { id: string, title: string, pinned?: boolean, folderId?: string|null, ts: number }
type Folder = { id: string, name: string }

export default function Sidebar({models: initialModels, selected, onSelect, onNewChat, onOpenSettings, onOpenWorkspace, onOpenHelp}:{models?:any[], selected?:string|null, onSelect?:(m:string|null)=>void, onNewChat?:()=>void, onOpenSettings?:()=>void, onOpenWorkspace?:()=>void, onOpenHelp?:()=>void}){
  const [hfToken, setHfToken] = useState<string>('')

  // ChatGPT-like sidebar state (stored locally)
  const [search, setSearch] = useState<string>('')
  const [conversations, setConversations] = useState<Conversation[]>(()=>{
    try{ const raw = localStorage.getItem('bunny:conversations'); return raw? JSON.parse(raw): [] }catch(e){ return [] }
  })
  const [folders, setFolders] = useState<Folder[]>(()=>{
    try{ const raw = localStorage.getItem('bunny:folders'); return raw? JSON.parse(raw): [] }catch(e){ return [] }
  })
  const [trash, setTrash] = useState<Conversation[]>(()=>{
    try{ const raw = localStorage.getItem('bunny:trash'); return raw? JSON.parse(raw): [] }catch(e){ return [] }
  })
  // UI for item menu
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null)
  const [menuConvId, setMenuConvId] = useState<string| null>(null)

  useEffect(()=>{ try{ localStorage.setItem('bunny:conversations', JSON.stringify(conversations)) }catch(e){} }, [conversations])
  useEffect(()=>{ try{ localStorage.setItem('bunny:folders', JSON.stringify(folders)) }catch(e){} }, [folders])
  useEffect(()=>{ try{ localStorage.setItem('bunny:trash', JSON.stringify(trash)) }catch(e){} }, [trash])

  const pinnedConversations = useMemo(()=> conversations.filter(c=>c.pinned).sort((a,b)=> b.ts - a.ts), [conversations])
  const otherConversations = useMemo(()=> conversations.filter(c=>!c.pinned).sort((a,b)=> b.ts - a.ts), [conversations])
  const filtered = useMemo(()=>{
    const q = search.trim().toLowerCase()
    if(!q) return { pinned: pinnedConversations, others: otherConversations }
    const f = (arr:Conversation[])=> arr.filter(c=> c.title.toLowerCase().includes(q))
    return { pinned: f(pinnedConversations), others: f(otherConversations) }
  }, [search, pinnedConversations, otherConversations])

  function createConversation(){
    const id = Math.random().toString(36).slice(2)
    const conv: Conversation = { id, title: 'New chat', ts: Date.now(), folderId: null }
    setConversations(prev => [conv, ...prev])
    onNewChat?.()
  }

  function renameConversation(id:string){
    const title = prompt('Rename conversation')
    if(title && title.trim()) setConversations(prev => prev.map(c=> c.id===id? {...c, title: title.trim() }: c))
  }
  function togglePin(id:string){ setConversations(prev => prev.map(c=> c.id===id? {...c, pinned: !c.pinned}: c)) }
  function moveToFolder(id:string, folderId:string|null){ setConversations(prev => prev.map(c=> c.id===id? {...c, folderId }: c)) }
  function deleteConversation(id:string){
    setConversations(prev => {
      const idx = prev.findIndex(c=>c.id===id)
      if(idx>=0){ const copy = [...prev]; const [removed] = copy.splice(idx,1); setTrash(t=> [{...removed}, ...t]); return copy }
      return prev
    })
  }
  function restoreConversation(id:string){
    setTrash(prev => {
      const idx = prev.findIndex(c=>c.id===id)
      if(idx>=0){ const copy = [...prev]; const [rest] = copy.splice(idx,1); setConversations(c=> [rest, ...c]); return copy }
      return prev
    })
  }
  function createFolder(){
    const name = prompt('Folder name')
    if(name && name.trim()) setFolders(prev => [...prev, {id: Math.random().toString(36).slice(2), name: name.trim()}])
  }
  function removeFolder(id:string){
    // Move items out of folder, then remove folder
    setConversations(prev => prev.map(c=> c.folderId===id? {...c, folderId: null}: c))
    setFolders(prev => prev.filter(f=> f.id!==id))
  }
  function openMenu(e: React.MouseEvent<HTMLElement>, id:string){ setMenuAnchor(e.currentTarget); setMenuConvId(id) }
  function closeMenu(){ setMenuAnchor(null); setMenuConvId(null) }

  // Model section removed
  // Pull/server controls removed

  return (
    <Box>
      {/* Header actions */}
      <Stack direction="row" spacing={1} sx={{mb:1}}>
        <Button size="small" variant="contained" startIcon={<AddIcon />} onClick={createConversation} fullWidth sx={{borderRadius:9999}}>New chat</Button>
      </Stack>
      <TextField size="small" fullWidth placeholder="Search" value={search} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setSearch(e.target.value)}
        InputProps={{ startAdornment: <SearchIcon fontSize="small" style={{opacity:0.7}} /> as any }} sx={{ mb:1, '& .MuiInputBase-root':{ borderRadius:9999, px:1.5 } }} />

      {/* Pinned */}
      {(filtered.pinned.length>0) && (
        <Box sx={{ mb:1.5 }}>
          <Typography variant="subtitle2" sx={{ opacity:0.75, mb:0.5 }}>Pinned</Typography>
          <List dense>
            {filtered.pinned.map(c=> (
              <ListItemButton key={c.id} sx={{ borderRadius:1 }}>
                <ListItemText primary={c.title} secondary={new Date(c.ts).toLocaleDateString()} />
                <Tooltip title={c.pinned? 'Unpin':'Pin'}>
                  <IconButton size="small" onClick={()=>togglePin(c.id)} sx={{mr:0.5}}>
                    {c.pinned? <PushPinIcon fontSize="inherit" />: <PushPinOutlinedIcon fontSize="inherit" />}
                  </IconButton>
                </Tooltip>
                <IconButton size="small" onClick={(e)=>openMenu(e, c.id)}>
                  <MoreVertIcon fontSize="inherit" />
                </IconButton>
              </ListItemButton>
            ))}
          </List>
        </Box>
      )}

      {/* Conversations */}
      <Typography variant="subtitle2" sx={{ opacity:0.75, mb:0.5 }}>Conversations</Typography>
      <Box sx={{ maxHeight: 160, overflow:'auto', mb:1.5, border:'1px solid var(--border)', borderRadius:1 }}>
        <List dense>
          {filtered.others.map(c=> (
            <ListItemButton key={c.id} sx={{ borderRadius:0 }}>
              <ListItemText primary={c.title} secondary={new Date(c.ts).toLocaleDateString()} />
              <Tooltip title={c.pinned? 'Unpin':'Pin'}>
                <IconButton size="small" onClick={()=>togglePin(c.id)} sx={{mr:0.5}}>
                  {c.pinned? <PushPinIcon fontSize="inherit" />: <PushPinOutlinedIcon fontSize="inherit" />}
                </IconButton>
              </Tooltip>
              <IconButton size="small" onClick={(e)=>openMenu(e, c.id)}>
                <MoreVertIcon fontSize="inherit" />
              </IconButton>
            </ListItemButton>
          ))}
          {filtered.others.length===0 && (
            <ListItemButton disabled>
              <ListItemText primary="No conversations" />
            </ListItemButton>
          )}
        </List>
      </Box>

      {/* Folders */}
      <Typography variant="subtitle2" sx={{ opacity:0.75, mb:0.5 }}>Folders</Typography>
      <Stack direction="row" spacing={1} sx={{ mb:1 }}>
        <Button size="small" variant="outlined" startIcon={<FolderIcon />} onClick={createFolder} sx={{borderRadius:9999}}>New folder</Button>
      </Stack>
      {folders.length>0 && (
        <Stack spacing={0.5} sx={{ mb:1.5 }}>
          {folders.map(f=> (
            <Stack key={f.id} direction="row" spacing={1} alignItems="center" sx={{ px:1 }}>
              <Chip size="small" icon={<FolderIcon />} label={f.name} sx={{borderRadius:9999}} />
              <Button size="small" variant="text" onClick={()=>removeFolder(f.id)}>Remove</Button>
            </Stack>
          ))}
        </Stack>
      )}

      {/* Trash */}
      <Typography variant="subtitle2" sx={{ opacity:0.75, mb:0.5 }}>Trash</Typography>
      <Box sx={{ maxHeight: 100, overflow:'auto', mb:1.5, border:'1px solid var(--border)', borderRadius:1 }}>
        <List dense>
          {trash.map(c=> (
            <ListItemButton key={c.id}>
              <ListItemText primary={c.title} />
              <IconButton size="small" onClick={()=>restoreConversation(c.id)} sx={{mr:0.5}}>
                <RestoreFromTrashIcon fontSize="inherit" />
              </IconButton>
            </ListItemButton>
          ))}
          {trash.length===0 && (
            <ListItemButton disabled>
              <ListItemText primary="Empty" />
            </ListItemButton>
          )}
        </List>
        </Box>
      {/* Models & server controls removed */}

      <Divider sx={{my:2}} />

      {/* Workspace & Settings */}
      <Stack direction="row" spacing={1} sx={{ mb:1 }}>
        <Button size="small" startIcon={<WorkspacePremiumOutlinedIcon />} variant="outlined" fullWidth sx={{borderRadius:9999}} onClick={onOpenWorkspace}>Workspace</Button>
      </Stack>
      <Stack direction="row" spacing={1}>
        <Button size="small" startIcon={<SettingsOutlinedIcon />} variant="text" sx={{borderRadius:9999}} onClick={onOpenSettings}>Settings</Button>
        <Button size="small" startIcon={<HelpOutlineIcon />} variant="text" sx={{borderRadius:9999}} onClick={onOpenHelp}>Help</Button>
      </Stack>

      {/* Conversation item menu */}
      <Menu anchorEl={menuAnchor} open={!!menuAnchor} onClose={closeMenu}>
        <MenuItem onClick={()=>{ if(menuConvId) renameConversation(menuConvId); closeMenu() }}>Rename</MenuItem>
        <MenuItem onClick={()=>{ if(menuConvId) togglePin(menuConvId); closeMenu() }}>{conversations.find(c=>c.id===menuConvId)?.pinned? 'Unpin':'Pin'}</MenuItem>
        <MenuItem onClick={()=>{ if(menuConvId) deleteConversation(menuConvId); closeMenu() }}><DeleteOutlineIcon fontSize="small" style={{marginRight:8}}/>Delete</MenuItem>
        {folders.length>0 && (
          <>
            <Divider />
            {folders.map(f=> (
              <MenuItem key={f.id} onClick={()=>{ if(menuConvId) moveToFolder(menuConvId, f.id); closeMenu() }}>Move to {f.name}</MenuItem>
            ))}
            <MenuItem onClick={()=>{ if(menuConvId) moveToFolder(menuConvId, null); closeMenu() }}>Remove from folder</MenuItem>
          </>
        )}
      </Menu>
    </Box>
  )
}
