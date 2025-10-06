import React, { useEffect, useState } from 'react'
import { Box, Typography, TextField, Button, Paper } from '@mui/material'
import ModelList from './ModelList'

export default function RightPanel({models, selected}:{models?:any[], selected?:string|null}){
  const [status, setStatus] = useState<any>({running:false})
  const [logs, setLogs] = useState<string[]>([])
  const [filter, setFilter] = useState<string>('')

  useEffect(()=>{
    let es: EventSource | null = null
    try{
      es = new EventSource('/api/logs/stream')
      es.onmessage = (ev)=>{
        try{
          const d = JSON.parse(ev.data)
          setLogs(prev => [...prev.slice(-200), d.line])
        }catch(e){/*ignore*/}
      }
    }catch(e){/*ignore*/}
    return ()=>{ if(es) es.close() }
  },[])

  useEffect(()=>{
    let mounted = true
    async function poll(){
      try{
        const r = await fetch('/api/server/status')
        if(!mounted) return
        if(r.ok){
          const j = await r.json()
          setStatus(j)
        }
      }catch(e){
        if(mounted) setStatus({running:false})
      }
    }
    poll()
    const id = setInterval(poll, 2000)
    return ()=>{ mounted=false; clearInterval(id) }
  },[])

  const model = (models||[]).find((m:any)=>m.name===selected)

  return (
    <Box>
      <Typography variant="h6">Server</Typography>
      <Paper sx={{p:1, mt:1}}>
        <Typography variant="body2">Status: {status.running? <span style={{color:'#7cfc9a'}}>Running</span>: <span style={{color:'#f88'}}>Stopped</span>}</Typography>
        {status.running && <Typography variant="body2">PID: {status.pid} Port: {status.port}</Typography>}
      </Paper>

      <Typography variant="h6" sx={{mt:2}}>Model</Typography>
      <Paper sx={{p:1, mt:1}}>
        {model ? (
          <Box>
            <Typography variant="subtitle1">{model.name}</Typography>
            <Typography variant="caption" display="block">{model.installed? 'Installed':'Not installed'}</Typography>
            {model.size && <Typography variant="caption" display="block">Size: {(model.size/1e6).toFixed(1)} MB</Typography>}
            {model.path && <Typography variant="caption" display="block">{model.path}</Typography>}
          </Box>
        ) : <Typography variant="caption">No model selected</Typography>}
      </Paper>

      <Typography variant="h6" sx={{mt:2}}>Models</Typography>
      <Paper sx={{p:1, mt:1}}>
        {Array.isArray(models) && models.length > 0 ? (
          <ModelList models={models as any[]} />
        ) : (
          <Typography variant="caption">No models loaded</Typography>
        )}
      </Paper>

      <Typography variant="h6" sx={{mt:2}}>Logs</Typography>
      <Box sx={{display:'flex', gap:1, mt:1}}>
  <TextField placeholder="Filter" size="small" value={filter} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setFilter(e.target.value)} fullWidth />
        <Button variant="outlined" onClick={async ()=>{
          try{
            const r = await fetch('/api/logs/download')
            const text = await r.text()
            const blob = new Blob([text], {type:'text/plain'})
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url; a.download = 'bunny-server.log'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url)
          }catch(e){console.error(e)}
        }}>Download</Button>
      </Box>
      <Paper sx={{p:1, mt:1, height:220, overflow:'auto', background:'#04131b'}}>
        {logs.filter(l=> filter? l.toLowerCase().includes(filter.toLowerCase()): true).map((l,i)=> <div key={i} style={{fontSize:12, color:'#cfe'}}>{l}</div>)}
      </Paper>
    </Box>
  )
}
