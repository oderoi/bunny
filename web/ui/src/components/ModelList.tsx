import React, { useState, useEffect } from 'react'

interface Model {
  name: string
  installed: boolean
  size?: number
  path?: string
}

interface DownloadJob {
  id: string
  model: string
  status: string
  downloaded: number
  size?: number
  error?: string
  started_at?: number
}

export default function ModelList({models}:{models:Model[]}){
  const [downloads, setDownloads] = useState<DownloadJob[]>([])
  const [downloading, setDownloading] = useState<Set<string>>(new Set())

  // Fetch active downloads
  useEffect(() => {
    const fetchDownloads = async () => {
      try {
        const response = await fetch('/api/downloads/active')
        const data = await response.json()
        setDownloads(Object.values(data))
        
        // Update downloading state
        const downloadingModels = new Set(
          Object.values(data)
            .filter((job: any) => job.status === 'running')
            .map((job: any) => job.model)
        )
        setDownloading(downloadingModels)
      } catch (error) {
        console.error('Failed to fetch downloads:', error)
      }
    }

    fetchDownloads()
    const interval = setInterval(fetchDownloads, 2000) // Poll every 2 seconds
    return () => clearInterval(interval)
  }, [])

  const startDownload = async (modelName: string) => {
    try {
      const response = await fetch('/api/models/pull', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelName })
      })
      const data = await response.json()
      
      if (data.ok) {
        setDownloading(prev => new Set([...prev, modelName]))
      }
    } catch (error) {
      console.error('Failed to start download:', error)
    }
  }

  const cancelDownload = async (modelName: string) => {
    try {
      // Find the job for this model
      const job = downloads.find(job => job.model === modelName && job.status === 'running')
      if (job) {
        await fetch(`/api/models/pull/cancel`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_id: job.id })
        })
        setDownloading(prev => {
          const newSet = new Set(prev)
          newSet.delete(modelName)
          return newSet
        })
      }
    } catch (error) {
      console.error('Failed to cancel download:', error)
    }
  }

  const formatSize = (bytes?: number) => {
    if (!bytes) return ''
    if (bytes < 1e6) return `${(bytes / 1e3).toFixed(1)}KB`
    if (bytes < 1e9) return `${(bytes / 1e6).toFixed(1)}MB`
    return `${(bytes / 1e9).toFixed(1)}GB`
  }

  const formatSpeed = (bytesPerSecond: number) => {
    if (bytesPerSecond < 1e6) return `${(bytesPerSecond / 1e3).toFixed(1)}KB/s`
    if (bytesPerSecond < 1e9) return `${(bytesPerSecond / 1e6).toFixed(1)}MB/s`
    return `${(bytesPerSecond / 1e9).toFixed(1)}GB/s`
  }

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`
    return `${Math.round(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`
  }

  const getDownloadProgress = (modelName: string) => {
    const job = downloads.find(job => job.model === modelName)
    if (!job || !job.size) return null
    
    const percent = (job.downloaded / job.size) * 100
    
    // Calculate download speed and ETA
    let speed = 0
    let eta = 0
    if (job.started_at && job.downloaded > 0) {
      const elapsed = (Date.now() / 1000) - job.started_at
      if (elapsed > 0) {
        speed = job.downloaded / elapsed
        const remaining = job.size - job.downloaded
        eta = remaining / speed
      }
    }
    
    return { 
      percent, 
      downloaded: job.downloaded, 
      size: job.size,
      speed,
      eta,
      status: job.status
    }
  }

  return (
    <div>
      {models.length === 0 && <div>No models found</div>}
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {models.map(model => {
          const isDownloading = downloading.has(model.name)
          const progress = getDownloadProgress(model.name)
          
          return (
            <li key={model.name} style={{ 
              marginBottom: 16, 
              padding: 12, 
              border: '1px solid #ddd', 
              borderRadius: 8,
              backgroundColor: model.installed ? '#f0f8f0' : '#f8f8f8'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <strong>{model.name}</strong>
                  <div style={{ fontSize: '0.9em', color: '#666' }}>
                    {model.installed ? (
                      <>✓ Installed {formatSize(model.size)}</>
                    ) : (
                      <>○ Not installed</>
                    )}
                  </div>
                  {progress && (
                    <div style={{ marginTop: 8 }}>
                      <div style={{ 
                        width: '100%', 
                        height: 8, 
                        backgroundColor: '#e0e0e0', 
                        borderRadius: 4,
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${progress.percent}%`,
                          height: '100%',
                          backgroundColor: progress.status === 'running' ? '#4CAF50' : '#ff9800',
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                      <div style={{ fontSize: '0.8em', color: '#666', marginTop: 4 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span>
                            {formatSize(progress.downloaded)} / {formatSize(progress.size)} ({progress.percent.toFixed(1)}%)
                          </span>
                          <span style={{ color: progress.status === 'running' ? '#4CAF50' : '#ff9800' }}>
                            {progress.status === 'running' ? 'Downloading...' : progress.status}
                          </span>
                        </div>
                        {progress.speed > 0 && (
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
                            <span>Speed: {formatSpeed(progress.speed)}</span>
                            <span>ETA: {formatTime(progress.eta)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
                
                <div>
                  {model.installed ? (
                    <span style={{ color: 'green', fontSize: '0.9em' }}>Ready</span>
                  ) : isDownloading ? (
                    <button 
                      onClick={() => cancelDownload(model.name)}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#ff4444',
                        color: 'white',
                        border: 'none',
                        borderRadius: 4,
                        cursor: 'pointer'
                      }}
                    >
                      Cancel
                    </button>
                  ) : (
                    <button 
                      onClick={() => startDownload(model.name)}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#4CAF50',
                        color: 'white',
                        border: 'none',
                        borderRadius: 4,
                        cursor: 'pointer'
                      }}
                    >
                      Download
                    </button>
                  )}
                </div>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
