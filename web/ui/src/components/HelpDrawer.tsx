import React, { useEffect, useState } from 'react'
import { Box, Drawer, IconButton, Typography, Tabs, Tab, Stack, Button, Divider, TextField, CircularProgress } from '@mui/material'
import CloseIcon from '@mui/icons-material/Close'

export default function HelpDrawer({open, onClose}:{open:boolean, onClose:()=>void}){
  const [tab, setTab] = useState(0)
  const [diag, setDiag] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  async function runDiagnostics(){
    setLoading(true)
    try{
      const r = await fetch('/api/diagnostics/run')
      setDiag(await r.json())
    }catch(e){ setDiag({ error: String(e) }) }
    setLoading(false)
  }

  async function pickFreePortAndRetry(){
    try{
      const r = await fetch('/api/ports/free')
      const j = await r.json()
      const s = (window as any).__bunny_settings || {}
      s.server = s.server || {}
      s.server.inference_port = j.port
      await fetch('/api/settings', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(s) })
      await fetch('/api/server/stop', { method:'POST' }).catch(()=>{})
      await fetch('/api/server/start', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ model: localStorage.getItem('bunny:selected'), port: j.port, ctx_size: (s.runtime?.ctx_size||2048) }) })
      runDiagnostics()
    }catch(e){ /* ignore */ }
  }

  return (
    <Drawer anchor="right" open={open} onClose={onClose}>
      <Box sx={{width:{xs:'100vw', sm: 700}, p:2}}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Help</Typography>
          <IconButton onClick={onClose} size="small"><CloseIcon fontSize="small"/></IconButton>
        </Stack>
        <Tabs value={tab} onChange={(_e,v)=>setTab(v)} sx={{mt:1}}>
          <Tab label="Quick Start" />
          <Tab label="Troubleshoot" />
          <Tab label="Models" />
          <Tab label="Performance" />
          <Tab label="Privacy" />
          <Tab label="Workspace" />
          <Tab label="Prompting" />
          <Tab label="Diagnostics" />
        </Tabs>

        {tab===0 && (
          <Box sx={{mt:2}}>
            <Typography variant="subtitle2">2-minute setup</Typography>
            <ol>
              <li>Pick a model (Settings → Models).</li>
              <li>Start the server (AppBar → Start/auto).</li>
              <li>Send your first message.</li>
            </ol>
          </Box>
        )}

        {tab===1 && (
          <Box sx={{mt:2}}>
            <Typography variant="subtitle2">Common issues</Typography>
            <ul>
              <li>Model not found → download via Settings/Models, or place into ~/.bunny/models.</li>
              <li>Port in use → use Pick a free port below.</li>
              <li>Server not ready → retry start with different port.</li>
            </ul>
            <Stack direction="row" spacing={1}>
              <Button variant="outlined" onClick={pickFreePortAndRetry}>Pick a free port & Restart</Button>
              <Button variant="outlined" onClick={runDiagnostics}>Run diagnostics</Button>
            </Stack>
          </Box>
        )}

        {tab===2 && (
          <Box sx={{mt:2}}>
            <Typography variant="subtitle2">Model guide</Typography>
            <ul>
              <li>Supported chat formats: chatml, llama3</li>
              <li>Add custom GGUF: repo_id + filename; files at ~/.bunny/models</li>
            </ul>
          </Box>
        )}

        {tab===3 && (
          <Box sx={{mt:2}}>
            <Typography variant="subtitle2">Performance tuning</Typography>
            <ul>
              <li>OOM → Reduce ctx_size, lower -ngl</li>
              <li>Slow tokens → Increase threads, reduce ctx_size</li>
              <li>Unstable → Lower temperature, adjust top-p/top-k</li>
            </ul>
          </Box>
        )}

        {tab===4 && (
          <Box sx={{mt:2}}>
            <Typography variant="subtitle2">Privacy & security</Typography>
            <ul>
              <li>Local-only mode; retention and export in Settings</li>
              <li>Expose on LAN: host 0.0.0.0, set API token, CORS</li>
            </ul>
          </Box>
        )}

        {tab===5 && (
          <Box sx={{mt:2}}>
            <Typography variant="subtitle2">Workspace concepts</Typography>
            <ul>
              <li>Workspaces → Projects → Shared prompts/presets/files</li>
              <li>Roles: Owner, Admin, Editor, Viewer</li>
            </ul>
          </Box>
        )}

        {tab===6 && (
          <Box sx={{mt:2}}>
            <Typography variant="subtitle2">Prompting best practices</Typography>
            <ul>
              <li>Use clear system prompt; add few-shot examples</li>
              <li>JSON mode: add stop sequences and schema hints</li>
            </ul>
          </Box>
        )}

        {tab===7 && (
          <Box sx={{mt:2}}>
            <Stack direction="row" spacing={1}>
              <Button variant="contained" onClick={runDiagnostics} disabled={loading}>{loading? 'Running...' : 'Run diagnostics'}</Button>
              <Button variant="outlined" onClick={pickFreePortAndRetry}>Pick free port & restart</Button>
            </Stack>
            <Box sx={{ mt:2, p:1.5, border:'1px solid var(--border)', borderRadius:1, maxHeight: 260, overflow:'auto', fontFamily:'monospace', fontSize:12 }}>
              {diag? <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(diag, null, 2)}</pre> : 'No diagnostics yet.'}
            </Box>
          </Box>
        )}
      </Box>
    </Drawer>
  )
}


