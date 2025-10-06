import React, { useState, useRef } from 'react'
import { Box, Paper, TextField, IconButton, Tooltip, Avatar, Divider, Stack, Typography, Snackbar, Alert } from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import StopIcon from '@mui/icons-material/Stop'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import ReplayIcon from '@mui/icons-material/Replay'

function escapeHtml(s:string){
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
}

function renderSimpleMarkdown(s:string){
  if(!s) return ''
  let out = escapeHtml(s)
  out = out.replace(/```([\s\S]*?)```/g, (_m, p1) => `<pre><code>${escapeHtml(p1)}</code></pre>`)
  out = out.replace(/`([^`]+)`/g, (_m,p1) => `<code>${escapeHtml(p1)}</code>`)
  out = out.replace(/\*\*([^*]+)\*\*/g, (_m,p1) => `<strong>${escapeHtml(p1)}</strong>`)
  out = out.replace(/\n/g, '<br/>')
  return out
}

type ChatMessage = { role: 'user' | 'assistant' | 'system'; content: string }

function MessageRow({ msg, onCopy }:{ msg: ChatMessage, onCopy: (text:string)=>void }){
  const isUser = msg.role === 'user'
  const isAssistant = msg.role === 'assistant'
  // ChatGPT-like: full-width row; assistant rows have a subtle alt background
  return (
    <Box sx={{ bgcolor: isAssistant? 'rgba(255,255,255,0.02)':'transparent', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
      <Box sx={{ maxWidth: 900, mx: 'auto', px: 2, py: 2.25, display: 'flex', gap: 1.5, flexDirection: isUser? 'row-reverse':'row', justifyContent: isUser? 'flex-end':'flex-start' }}>
        <Avatar sx={{ bgcolor: isUser? 'primary.main':'#e5e7eb', color: isUser? '#fff':'#111', width: 28, height: 28 }}>
          {isUser? 'U':'A'}
        </Avatar>
        <Box sx={{ flex: 1, display:'flex', justifyContent: isUser? 'flex-end':'flex-start' }}>
          <Box sx={{ maxWidth: '85%', px:1.5, py:1, borderRadius: 2, bgcolor: isUser? 'rgba(16,163,127,0.12)':'transparent', boxShadow: isUser? '0 0 0 1px rgba(16,163,127,0.35) inset' : 'none' }}>
            <Typography component="div" variant="body1" className="chat-content" sx={{ lineHeight: 1.7, fontSize: 15, textAlign: isUser? 'right':'left' }} dangerouslySetInnerHTML={{__html: renderSimpleMarkdown(msg.content || '')}} />
          </Box>
          <Box sx={{ display:'flex', justifyContent: isUser? 'flex-start':'flex-end', alignItems:'flex-start', mt:0.5, mx:1 }}>
            <Tooltip title="Copy">
              <IconButton size="small" onClick={()=>onCopy(msg.content)} sx={{ color:'text.secondary' }}>
                <ContentCopyIcon fontSize="inherit" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Box>
    </Box>
  )
}

export default function ChatPanel({selectedModel}:{selectedModel?:any}){
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const chatRef = useRef<HTMLDivElement|null>(null)
  const [controller, setController] = useState<AbortController|null>(null)
  const [toast, setToast] = useState<{open:boolean, msg:string, sev:'success'|'error'|'info'}>({open:false, msg:'', sev:'info'})
  const [atBottom, setAtBottom] = useState(true)

  // Typewriter queue for smooth streaming
  const typingQueueRef = useRef<string>('')
  const typingTimerRef = useRef<any>(null)

  function startTypingTimer(){
    if(typingTimerRef.current) return
    typingTimerRef.current = setInterval(()=>{
      const step = 3 // chars per tick
      const q = typingQueueRef.current
      if(!q){
        clearInterval(typingTimerRef.current)
        typingTimerRef.current = null
        return
      }
      const emit = q.slice(0, step)
      typingQueueRef.current = q.slice(step)
      if(emit){
        setMessages(prev => {
          const copy = [...prev]
          for(let i=copy.length-1;i>=0;i++){
            if(copy[i].role==='assistant'){
              copy[i].content = (copy[i].content || '') + emit
              break
            }
          }
          return copy
        })
        // keep view scrolled
        if(chatRef.current){
          chatRef.current.scrollTo({top: chatRef.current.scrollHeight})
        }
      }
    }, 18)
  }

  function enqueueTypewriter(text:string){
    if(!text) return
    typingQueueRef.current += text
    startTypingTimer()
  }

  async function send(){
    if(!input) return
    if(!selectedModel){ setToast({open:true, msg:'Select a model', sev:'error'}); return }
    // Preflight: ensure selected model is installed, otherwise block and inform
    try{
      const modelsResp = await fetch('/api/models')
      if(modelsResp.ok){
        const list = await modelsResp.json()
        const found = Array.isArray(list)? list.find((m:any)=> m && m.name === selectedModel) : null
        if(found && found.installed === false){
          setToast({open:true, msg:`Model "${selectedModel}" is not installed`, sev:'error'})
          return
        }
      }
    }catch(_e){ /* ignore preflight errors */ }
    const payload = { messages: [{role:'user', content: input}], max_tokens: 256, temperature:0.7, stream:true }
    setMessages(prev => [...prev, {role:'user', content: input}, {role:'assistant', content: ''}])
    setInput('')

    try{
      // Ensure backend server is running for the selected model before streaming
      if(selectedModel){
        try {
          await fetch('/api/server/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: selectedModel?.name.name, port: 8081, ctx_size: 2048 })
          })
        } catch (e) { /* ignore; we'll still attempt to stream and show any error */ }
      }

      const ac = new AbortController()
      setController(ac)
      const res = await fetch('/api/chat/stream', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({...payload, model: selectedModel?.name}), signal: ac.signal})
      if(!res.ok){
        let errText = ''
        try { errText = await res.text() } catch(_e) {}
        throw new Error(errText || `HTTP ${res.status}`)
      }
      if(!res.body) throw new Error('No stream')
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      let done = false
      let appendedAny = false

      function tryExtractTextFromJSON(obj:any){
        // OpenAI-like: choices[*].delta.content or choices[*].message.content
        try{
          if(obj && typeof obj === 'object'){
            if(Array.isArray(obj.choices)){
              const parts:string[] = []
              for(const ch of obj.choices){
                if(ch && ch.delta && typeof ch.delta.content === 'string') parts.push(ch.delta.content)
                else if(ch && ch.message && typeof ch.message.content === 'string') parts.push(ch.message.content)
                else if(typeof ch.text === 'string') parts.push(ch.text)
              }
              if(parts.length) return parts.join('')
            }
            if(typeof obj.text === 'string') return obj.text
            if(typeof obj.content === 'string') return obj.content
          }
        }catch(e){/* ignore */}
        return null
      }

      while(!done){
        const {value, done:d} = await reader.read()
        done = d
        if(value){
          const chunk = decoder.decode(value)
          // Accumulate
          buf += chunk

          // If the chunk looks like SSE 'data:' frames, handle each line
          if(buf.includes('\n')){
            const lines = buf.split(/\r?\n/)
            // keep last partial line in buffer
            buf = lines.pop() || ''
            for(const line of lines){
              if(!line) continue
              let payload = line
              if(payload.startsWith('data:')) payload = payload.slice(5).trim()
              if(payload === '[DONE]' || payload === '"[DONE]"'){
                // finish
                done = true
                break
              }

              // try parse JSON
              let appended = false
              if(payload.startsWith('{') || payload.startsWith('[')){
                try{
                  const j = JSON.parse(payload)
                  const txt = tryExtractTextFromJSON(j)
                  if(txt){
                    enqueueTypewriter(txt)
                    appendedAny = true
                    appended = true
                  }
                }catch(e){
                  // not valid JSON, fall through to raw append
                }
              }

              if(!appended){
                // raw text
                enqueueTypewriter(payload)
                appendedAny = true
              }
            }
          } else {
            // No newline found — likely plain text token chunk; append directly
            enqueueTypewriter(chunk)
            if(chunk && chunk.trim().length){ appendedAny = true }
          }

          chatRef.current?.scrollTo({top: chatRef.current.scrollHeight, behavior:'smooth'})
        }
      }
      setController(null)
      // Fallback: if stream produced no content, try non-streaming once
      if(!appendedAny){
        try{
          const r2 = await fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ ...payload, stream:false, model: selectedModel?.name }) })
          if(r2.ok){
            const j = await r2.json()
            const txt = (j && j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || ''
            if(txt){
              enqueueTypewriter(txt)
            }
          } else {
            const err = await r2.text().catch(()=> '')
            setMessages(prev => [...prev, {role:'assistant', content: err || 'No response'}])
          }
        }catch(_e){ /* ignore */ }
      }
    }catch(e){
      setController(null)
      setMessages(prev => [...prev, {role:'assistant', content: 'Error: '+String(e)}])
    }
  }

  function cancel(){
    controller?.abort()
    setController(null)
    try{ fetch('/api/generation/cancel', {method:'POST'}) }catch(e){console.warn('cancel',e)}
  }

  async function regenerate(){
    if(controller) return
    // find last user message
    let lastPrompt: string | null = null
    for(let i=messages.length-1;i>=0;i--){
      if(messages[i].role==='user'){
        lastPrompt = messages[i].content
        break
      }
    }
    if(!lastPrompt){ setToast({open:true, msg:'No previous prompt to regenerate', sev:'info'}); return }
    if(!selectedModel){ setToast({open:true, msg:'Select a model', sev:'error'}); return }

    // prepare placeholder assistant bubble
    setMessages(prev => {
      const copy = [...prev]
      if(copy.length && copy[copy.length-1].role==='assistant'){
        copy[copy.length-1] = { role:'assistant', content: '' }
      } else {
        copy.push({ role:'assistant', content: '' })
      }
      return copy
    })

    // reset typing queue
    typingQueueRef.current = ''

    // ensure server running
    try {
      await fetch('/api/server/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel?.name, port: 8081, ctx_size: 2048 })
      })
    } catch (e) { /* ignore */ }

    const payload = { messages: [{role:'user', content: lastPrompt}], max_tokens: 256, temperature:0.7, stream:true }

    try{
      const ac = new AbortController()
      setController(ac)
      const res = await fetch('/api/chat/stream', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({...payload, model: selectedModel?.name}), signal: ac.signal})
      if(!res.ok){
        let errText = ''
        try { errText = await res.text() } catch(_e) {}
        throw new Error(errText || `HTTP ${res.status}`)
      }
      if(!res.body) throw new Error('No stream')
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      let done = false
      let appendedAny = false

      function tryExtractTextFromJSON(obj:any){
        try{
          if(obj && typeof obj === 'object'){
            if(Array.isArray(obj.choices)){
              const parts:string[] = []
              for(const ch of obj.choices){
                if(ch && ch.delta && typeof ch.delta.content === 'string') parts.push(ch.delta.content)
                else if(ch && ch.message && typeof ch.message.content === 'string') parts.push(ch.message.content)
                else if(typeof ch.text === 'string') parts.push(ch.text)
              }
              if(parts.length) return parts.join('')
            }
            if(typeof obj.text === 'string') return obj.text
            if(typeof obj.content === 'string') return obj.content
          }
        }catch(e){/* ignore */}
        return null
      }

      while(!done){
        const {value, done:d} = await reader.read()
        done = d
        if(value){
          const chunk = decoder.decode(value)
          buf += chunk
          if(buf.includes('\n')){
            const lines = buf.split(/\r?\n/)
            buf = lines.pop() || ''
            for(const line of lines){
              if(!line) continue
              let payloadLine = line
              if(payloadLine.startsWith('data:')) payloadLine = payloadLine.slice(5).trim()
              if(payloadLine === '[DONE]' || payloadLine === '"[DONE]"'){
                done = true
                break
              }
              let appended = false
              if(payloadLine.startsWith('{') || payloadLine.startsWith('[')){
                try{
                  const j = JSON.parse(payloadLine)
                  const txt = tryExtractTextFromJSON(j)
                  if(txt){
                    enqueueTypewriter(txt)
                    appendedAny = true
                    appended = true
                  }
                }catch(e){ }
              }
              if(!appended){
                enqueueTypewriter(payloadLine)
                appendedAny = true
              }
            }
          } else {
            enqueueTypewriter(chunk)
            if(chunk && chunk.trim().length){ appendedAny = true }
          }
          chatRef.current?.scrollTo({top: chatRef.current.scrollHeight, behavior:'smooth'})
        }
      }
      setController(null)
      if(!appendedAny){
        try{
          const r2 = await fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ ...payload, stream:false, model: selectedModel?.name }) })
          if(r2.ok){
            const j = await r2.json()
            const txt = (j && j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || ''
            if(txt){ enqueueTypewriter(txt) }
          } else {
            const err = await r2.text().catch(()=> '')
            setMessages(prev => [...prev, {role:'assistant', content: err || 'No response'}])
          }
        }catch(_e){ }
      }
    }catch(e){
      setController(null)
      setMessages(prev => [...prev, {role:'assistant', content: 'Error: '+String(e)}])
    }
  }

  async function copyToClipboard(text:string){
    try{ await navigator.clipboard.writeText(text); setToast({open:true, msg:'Copied', sev:'success'}) }catch(e){ setToast({open:true, msg:'Copy failed', sev:'error'}) }
  }

  return (
    <Box sx={{height:'100%', display:'flex', flexDirection:'column'}}>
      <Box sx={{flex:1, overflow:'auto', position:'relative'}} ref={chatRef as any} onScroll={(e:any)=>{
        const el = e.currentTarget as HTMLDivElement
        const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60
        setAtBottom(nearBottom)
      }}>
        {messages.length === 0 && (
          <Box sx={{ maxWidth: 900, mx:'auto', px:2, py:4, color:'text.secondary', fontSize:13, textAlign:'center' }}>Start a conversation with your model.</Box>
        )}
        {messages.map((m, i)=> (
          <React.Fragment key={i}>
            <MessageRow msg={m} onCopy={copyToClipboard} />
            {(i === messages.length - 1 && m.role === 'assistant' && !controller) && (
              <Box sx={{ maxWidth: 900, mx:'auto', px:2, pb:1, display:'flex', justifyContent:'flex-end' }}>
                <Tooltip title="Regenerate using last prompt">
                  <span>
                    <IconButton onClick={regenerate} size="small" sx={{borderRadius:9999}}>
                      <ReplayIcon />
                    </IconButton>
                  </span>
                </Tooltip>
              </Box>
            )}
          </React.Fragment>
        ))}
        {!atBottom && (
          <Box sx={{position:'sticky', bottom:8, display:'flex', justifyContent:'center'}}>
            <IconButton size="small" onClick={()=>{ if(chatRef.current) chatRef.current.scrollTo({top: chatRef.current.scrollHeight, behavior:'smooth'}) }} sx={{borderRadius:9999, background:'#111', color:'#fff'}}>
              Jump to latest
            </IconButton>
          </Box>
        )}
      </Box>

      <Divider />
      <Box sx={{ position:'sticky', bottom:0, bgcolor:'background.default', py:1.25, px:2 }}>
        <Box sx={{ maxWidth: 900, mx: 'auto' }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <TextField size="small" multiline minRows={1} maxRows={3} value={input} onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>)=>setInput(e.target.value)}
              onKeyDown={(e)=>{
                if(e.key==='Enter' && !e.shiftKey && !e.altKey && !e.isComposing){ e.preventDefault(); send() }
                if(e.key==='Escape'){ e.preventDefault(); cancel() }
              }}
              fullWidth placeholder={selectedModel? (selectedModel.installed? `Message ${selectedModel.name}`:'Model not installed - download it first'):'Select a model to chat'} disabled={!selectedModel || !selectedModel?.installed} sx={{
                '& .MuiInputBase-root':{ borderRadius:9999, boxShadow:'0 1px 0 rgba(255,255,255,0.06) inset, 0 0 0 1px rgba(255,255,255,0.06)', px:1.5 },
                '& .MuiInputBase-inputMultiline': { paddingTop:0.5, paddingBottom:0.5, textIndent:'10px' },
                '& textarea': { fontSize:13, lineHeight:1.5 },
                '& textarea::placeholder': { opacity:0.7 }
              }} />
            {controller ? (
              <Tooltip title="Stop">
                <span>
                  <IconButton color="error" onClick={cancel} size="small" sx={{borderRadius:9999}}>
                    <StopIcon />
                  </IconButton>
                </span>
              </Tooltip>
            ) : (
              <Tooltip title="Send">
                <span>
                  <IconButton color="primary" onClick={send} size="small" disabled={!selectedModel || !input} sx={{borderRadius:9999}}>
                    <SendIcon />
                  </IconButton>
                </span>
              </Tooltip>
            )}
          </Stack>
        </Box>
      </Box>

      <Snackbar open={toast.open} autoHideDuration={1600} onClose={()=>setToast(t=>({...t, open:false}))} anchorOrigin={{vertical:'bottom', horizontal:'left'}}>
        <Alert onClose={()=>setToast(t=>({...t, open:false}))} severity={toast.sev} variant="filled" sx={{ borderRadius:9999 }}>
          {toast.msg}
        </Alert>
      </Snackbar>
    </Box>
  )
}
