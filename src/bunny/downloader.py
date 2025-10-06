"""
Centralized download module for Bunny models.

This module provides a unified download interface for both CLI and web manager,
with support for resume, progress tracking, cancellation, and error handling.
"""

import os
import time
import shutil
import threading
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
import requests
from huggingface_hub import hf_hub_url


class DownloadJob:
    """Represents a download job with progress tracking."""
    
    def __init__(self, job_id: str, model_name: str, repo_id: str, filename: str, 
                 local_dir: Path, hf_token: Optional[str] = None):
        self.job_id = job_id
        self.model_name = model_name
        self.repo_id = repo_id
        self.filename = filename
        self.local_dir = local_dir
        self.hf_token = hf_token
        
        # Status tracking
        self.status = "queued"  # queued, running, done, failed, cancelled
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.error: Optional[str] = None
        
        # Progress tracking
        self.downloaded = 0
        self.size: Optional[int] = None
        self.path: Optional[Path] = None
        
        # Control flags
        self.cancel = False
        
        # Callbacks
        self.progress_callback: Optional[Callable[[int, int], None]] = None
        self.status_callback: Optional[Callable[[str], None]] = None


class ModelDownloader:
    """Centralized download manager for model files."""
    
    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.jobs: Dict[str, DownloadJob] = {}
        self.jobs_lock = threading.Lock()
    
    def create_job(self, model_name: str, repo_id: str, filename: str, 
                   hf_token: Optional[str] = None) -> str:
        """Create a new download job and return its ID."""
        job_id = str(uuid.uuid4())
        job = DownloadJob(
            job_id=job_id,
            model_name=model_name,
            repo_id=repo_id,
            filename=filename,
            local_dir=self.model_dir,
            hf_token=hf_token
        )
        
        with self.jobs_lock:
            self.jobs[job_id] = job
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[DownloadJob]:
        """Get a download job by ID."""
        with self.jobs_lock:
            return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[DownloadJob]:
        """Get all download jobs."""
        with self.jobs_lock:
            return list(self.jobs.values())
    
    def get_active_jobs(self) -> List[DownloadJob]:
        """Get all active (queued or running) download jobs."""
        with self.jobs_lock:
            return [job for job in self.jobs.values() 
                   if job.status in ("queued", "running")]
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a download job."""
        with self.jobs_lock:
            job = self.jobs.get(job_id)
            if job and job.status in ("queued", "running"):
                job.cancel = True
                job.status = "cancelled"
                job.finished_at = time.time()
                return True
        return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a completed or failed job."""
        with self.jobs_lock:
            job = self.jobs.get(job_id)
            if job and job.status in ("done", "failed", "cancelled"):
                del self.jobs[job_id]
                return True
        return False
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove old completed jobs."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        removed_count = 0
        
        with self.jobs_lock:
            to_remove = []
            for job_id, job in self.jobs.items():
                if (job.status in ("done", "failed", "cancelled") and 
                    job.finished_at and job.finished_at < cutoff_time):
                    to_remove.append(job_id)
            
            for job_id in to_remove:
                del self.jobs[job_id]
                removed_count += 1
        
        return removed_count
    
    def start_download(self, job_id: str) -> bool:
        """Start downloading a job in a background thread."""
        with self.jobs_lock:
            job = self.jobs.get(job_id)
            if not job or job.status != "queued":
                return False
        
        thread = threading.Thread(target=self._download_worker, args=(job,), daemon=True)
        thread.start()
        return True
    
    def _download_worker(self, job: DownloadJob):
        """Background worker for downloading files."""
        job.status = "running"
        job.started_at = time.time()
        
        if job.status_callback:
            job.status_callback("running")
        
        try:
            self._perform_download(job)
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.finished_at = time.time()
            if job.status_callback:
                job.status_callback("failed")
    
    def _perform_download(self, job: DownloadJob):
        """Perform the actual download with resume support."""
        max_attempts = 4
        attempt = 0
        
        while attempt < max_attempts and not job.cancel:
            attempt += 1
            backoff = (2 ** (attempt - 1))
            
            try:
                # Get download URL
                url = hf_hub_url(repo_id=job.repo_id, filename=job.filename)
                
                # Prepare headers
                headers = {}
                if job.hf_token:
                    headers['authorization'] = f'Bearer {job.hf_token}'
                
                # Check disk space
                if not self._check_disk_space(job, url, headers):
                    job.status = "failed"
                    job.error = "Insufficient disk space"
                    job.finished_at = time.time()
                    return
                
                # Determine resume point
                part_path = job.local_dir / f"{job.filename}.part"
                final_path = job.local_dir / job.filename
                resume_from = 0
                
                if part_path.exists():
                    resume_from = part_path.stat().st_size
                
                # Download with resume support
                if self._download_with_resume(job, url, headers, part_path, final_path, resume_from):
                    job.status = "done"
                    job.finished_at = time.time()
                    job.path = final_path
                    if job.status_callback:
                        job.status_callback("done")
                    return
                
            except Exception as e:
                if attempt >= max_attempts:
                    raise
                time.sleep(backoff)
                continue
        
        if job.cancel:
            job.status = "cancelled"
            job.finished_at = time.time()
        else:
            job.status = "failed"
            job.error = "Max attempts exceeded"
            job.finished_at = time.time()
    
    def _check_disk_space(self, job: DownloadJob, url: str, headers: Dict[str, str]) -> bool:
        """Check if there's enough disk space for the download."""
        try:
            # Probe for file size
            with requests.head(url, headers=headers, timeout=30) as resp:
                resp.raise_for_status()
                content_length = resp.headers.get('content-length')
                if content_length:
                    required_space = int(content_length) * 1.2  # 20% buffer
                    free_space = shutil.disk_usage(str(job.local_dir)).free
                    return free_space >= required_space
        except Exception:
            pass
        return True  # If we can't determine size, proceed
    
    def _download_with_resume(self, job: DownloadJob, url: str, headers: Dict[str, str],
                            part_path: Path, final_path: Path, resume_from: int) -> bool:
        """Download file with resume support."""
        headers_with_range = dict(headers)
        if resume_from > 0:
            headers_with_range['Range'] = f'bytes={resume_from}-'
        
        try:
            with requests.get(url, stream=True, headers=headers_with_range, timeout=300) as resp:
                resp.raise_for_status()
                
                # Update total size
                content_length = resp.headers.get('content-length')
                if content_length:
                    job.size = resume_from + int(content_length)
                
                # Download with progress tracking
                mode = 'ab' if resume_from else 'wb'
                with open(part_path, mode) as f:
                    for chunk in resp.iter_content(chunk_size=64*1024):
                        if job.cancel:
                            return False
                        
                        if chunk:
                            f.write(chunk)
                            job.downloaded += len(chunk)
                            
                            if job.progress_callback:
                                job.progress_callback(job.downloaded, job.size or 0)
                
                # Move part file to final location
                shutil.move(str(part_path), str(final_path))
                job.downloaded = final_path.stat().st_size
                job.size = job.downloaded
                
                return True
                
        except Exception as e:
            job.error = str(e)
            return False
    
    def download_model(self, model_name: str, repo_id: str, filename: str,
                      hf_token: Optional[str] = None,
                      progress_callback: Optional[Callable[[int, int], None]] = None,
                      status_callback: Optional[Callable[[str], None]] = None) -> str:
        """Download a model with progress tracking."""
        job_id = self.create_job(model_name, repo_id, filename, hf_token)
        job = self.get_job(job_id)
        
        if job:
            job.progress_callback = progress_callback
            job.status_callback = status_callback
            self.start_download(job_id)
        
        return job_id


# Global downloader instance
_downloader: Optional[ModelDownloader] = None


def get_downloader(model_dir: Optional[Path] = None) -> ModelDownloader:
    """Get the global downloader instance."""
    global _downloader
    if _downloader is None:
        if model_dir is None:
            model_dir = Path.home() / ".bunny" / "models"
        _downloader = ModelDownloader(model_dir)
    return _downloader


def download_model(model_name: str, repo_id: str, filename: str,
                  hf_token: Optional[str] = None,
                  progress_callback: Optional[Callable[[int, int], None]] = None,
                  status_callback: Optional[Callable[[str], None]] = None) -> str:
    """Convenience function to download a model."""
    downloader = get_downloader()
    return downloader.download_model(model_name, repo_id, filename, hf_token,
                                   progress_callback, status_callback)