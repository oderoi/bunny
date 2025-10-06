import React, { useEffect, useState } from 'react'
import { Box, Drawer, IconButton, Typography, Tabs, Tab, Stack, TextField, Button, Switch, FormControlLabel, Divider, MenuItem, Select, InputLabel } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'

export default function SettingsDrawer({open, onClose}:{open:boolean, onClose:()=>void}){
  const [tab, setTab] = useState<number>(0)
  const [settings, setSettings] = useState<any>(null)
  const [saving, setSaving] = useState<boolean>(false)

  useEffect(()=>{
    if(!open) return
    ;(async()=>{
      try{
        const r = await fetch('/api/settings')
        const j = await r.json()
        setSettings(j)
      }catch(e){ setSettings({}) }
    })()
  },[open])

  async function save(){
    setSaving(true)
    try{
      await fetch('/api/settings', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(settings||{}) })
      onClose()
    }catch(e){
      setSaving(false)
    }
  }

  if(!settings) return null

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{width:{xs:'100vw', sm: 520}, p:2}}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Settings</Typography>
          <IconButton onClick={onClose} size="small"><CloseIcon fontSize="small"/></IconButton>
        </Stack>
        <Tabs value={tab} onChange={(_e,v)=>setTab(v)} sx={{mt:1}}>
          <Tab label="Server" />
          <Tab label="Runtime" />
          <Tab label="Generation" />
          <Tab label="UI" />
          <Tab label="Privacy" />
          <Tab label="Advanced" />
        </Tabs>

        {tab===0 && (
          <Box sx={{mt:2}}>
            <Stack spacing={2}>
              <TextField label="UI Port" size="small" type="number" value={settings.ui?.port||''} onChange={(e)=> setSettings((s:any)=> ({...s, ui:{...s.ui, port: Number(e.target.value)||0}}))} />
              <TextField label="Inference Port" size="small" type="number" value={settings.server?.inference_port||''} onChange={(e)=> setSettings((s:any)=> ({...s, server:{...s.server, inference_port: Number(e.target.value)||0}}))} />
              <TextField label="Host Binding" size="small" value={settings.server?.host||''} onChange={(e)=> setSettings((s:any)=> ({...s, server:{...s.server, host: e.target.value}}))} />
              <FormControlLabel control={<Switch checked={!!settings.server?.auto_restart} onChange={(e)=> setSettings((s:any)=> ({...s, server:{...s.server, auto_restart: e.target.checked}}))} />} label="Auto-restart on crash" />
            </Stack>
          </Box>
        )}

        {tab===1 && (
          <Box sx={{mt:2}}>
            <Stack spacing={2}>
              <TextField label="Context Size" size="small" type="number" value={settings.runtime?.ctx_size||''} onChange={(e)=> setSettings((s:any)=> ({...s, runtime:{...s.runtime, ctx_size: Number(e.target.value)||0}}))} />
              <TextField label="Threads" size="small" type="number" value={settings.runtime?.threads||''} onChange={(e)=> setSettings((s:any)=> ({...s, runtime:{...s.runtime, threads: Number(e.target.value)||0}}))} />
              <TextField label="GPU Layers (-ngl)" size="small" type="number" value={settings.runtime?.ngl||''} onChange={(e)=> setSettings((s:any)=> ({...s, runtime:{...s.runtime, ngl: Number(e.target.value)||0}}))} />
            </Stack>
          </Box>
        )}

        {tab===2 && (
          <Box sx={{mt:2}}>
            <Stack spacing={2}>
              <TextField label="Temperature" size="small" type="number" value={settings.generation?.temperature||0} onChange={(e)=> setSettings((s:any)=> ({...s, generation:{...s.generation, temperature: Number(e.target.value)}}))} />
              <TextField label="Top-p" size="small" type="number" value={settings.generation?.top_p||1} onChange={(e)=> setSettings((s:any)=> ({...s, generation:{...s.generation, top_p: Number(e.target.value)}}))} />
              <TextField label="Top-k" size="small" type="number" value={settings.generation?.top_k||40} onChange={(e)=> setSettings((s:any)=> ({...s, generation:{...s.generation, top_k: Number(e.target.value)}}))} />
              <TextField label="Max tokens" size="small" type="number" value={settings.generation?.max_tokens||256} onChange={(e)=> setSettings((s:any)=> ({...s, generation:{...s.generation, max_tokens: Number(e.target.value)}}))} />
              <TextField label="Seed" size="small" type="number" value={settings.generation?.seed||''} onChange={(e)=> setSettings((s:any)=> ({...s, generation:{...s.generation, seed: e.target.value? Number(e.target.value): null}}))} />
              <TextField label="Stop sequences (comma-separated)" size="small" value={(settings.generation?.stop||[]).join(', ')} onChange={(e)=> setSettings((s:any)=> ({...s, generation:{...s.generation, stop: e.target.value.split(',').map((x:string)=>x.trim()).filter(Boolean)}}))} />
              <TextField label="System prompt" size="small" value={settings.system_prompt||''} onChange={(e)=> setSettings((s:any)=> ({...s, system_prompt: e.target.value}))} multiline minRows={2} />
            </Stack>
          </Box>
        )}

        {tab===3 && (
          <Box sx={{mt:2}}>
            <Stack spacing={2}>
              <Select size="small" value={settings.ui?.theme||'dark'} onChange={(e)=> setSettings((s:any)=> ({...s, ui:{...s.ui, theme: e.target.value}}))}>
                <MenuItem value="light">Light</MenuItem>
                <MenuItem value="dark">Dark</MenuItem>
                <MenuItem value="system">System</MenuItem>
              </Select>
              <TextField label="Font size" size="small" type="number" value={settings.ui?.font_size||14} onChange={(e)=> setSettings((s:any)=> ({...s, ui:{...s.ui, font_size: Number(e.target.value)||14}}))} />
              <FormControlLabel control={<Switch checked={!!settings.ui?.streaming} onChange={(e)=> setSettings((s:any)=> ({...s, ui:{...s.ui, streaming: e.target.checked}}))} />} label="Streaming responses" />
            </Stack>
          </Box>
        )}

        {tab===4 && (
          <Box sx={{mt:2}}>
            <Stack spacing={2}>
              <FormControlLabel control={<Switch checked={false} />} label="Telemetry (always off)" />
              <FormControlLabel control={<Switch checked={false} />} label="History retention (todo)" />
              <FormControlLabel control={<Switch checked={false} />} label="PII redaction (todo)" />
            </Stack>
          </Box>
        )}

        {tab===5 && (
          <Box sx={{mt:2}}>
            <Stack spacing={2}>
              <TextField label="Log level" size="small" value={settings.server?.log_level||'info'} onChange={(e)=> setSettings((s:any)=> ({...s, server:{...s.server, log_level: e.target.value}}))} />
            </Stack>
          </Box>
        )}

        <Divider sx={{my:2}} />
        <Stack direction="row" spacing={1} justifyContent="flex-end">
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="contained" onClick={save} disabled={saving}>Save</Button>
        </Stack>
      </Box>
    </Drawer>
  )
}
