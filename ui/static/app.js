// State
let logsPaused = false;
let logFilter = '';
const logs = [];
const MAX_LOGS = 300;

// window.localStorage.clear();

// API credentials (stored in localStorage)
let apiCredentials = localStorage.getItem('apiCredentials') || null;

// Animation state
let lastSnapshot = null;
let previousSnapshot = null;
let lastFrameTime = performance.now();
let animationId = null;

// Heartbeat state
let heartbeatOk = true;
let lastHeartbeatTick = null;
let heartbeatStuckCount = 0;

// DOM refs
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const logContainer = document.getElementById('log-container');
const clientsList = document.getElementById('clients-list');
const connDot = document.getElementById('conn-dot');
const connText = document.getElementById('conn-text');

// Log pause toggle
document.getElementById('log-pause-btn').addEventListener('click', () => {
  logsPaused = !logsPaused;
  document.getElementById('log-pause-btn').textContent = logsPaused ? '▶' : '⏸';
  document.getElementById('log-paused-indicator').innerHTML = logsPaused 
    ? '<span class="log-paused-badge">PAUSED</span>' : '';
});

// Log filter
document.getElementById('log-filter').addEventListener('input', (e) => {
  logFilter = e.target.value.toLowerCase();
  renderLogs();
});

function clearLogs() {
  logs.length = 0;
  renderLogs();
}

function post(path) {
  // Prompt for credentials if not set
  if (!apiCredentials) {
    promptForCredentials();
    if (!apiCredentials) return;
  }
  
  fetch(path, { 
    method: 'POST',
    headers: {
      'Authorization': 'Basic ' + apiCredentials
    }
  }).then(r => {
    if (r.status === 401) {
      apiCredentials = null;
      localStorage.removeItem('apiCredentials');
      addLog('error', 'Invalid API credentials');
      promptForCredentials();
    }
  });
}

function promptForCredentials() {
  const username = prompt('API Username:', 'admin');
  if (!username) return;
  const password = prompt('API Password:');
  if (!password) return;
  apiCredentials = btoa(username + ':' + password);
  localStorage.setItem('apiCredentials', apiCredentials);
}

function formatTime(ts) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('en-US', { hour12: false }) + '.' + String(d.getMilliseconds()).padStart(3, '0');
}

function addLog(type, msg, ts = Date.now() / 1000) {
  if (logsPaused) return;
  logs.unshift({ type, msg, ts });
  if (logs.length > MAX_LOGS) logs.pop();
  renderLogs();
}

function renderLogs() {
  const filtered = logFilter 
    ? logs.filter(l => l.msg.toLowerCase().includes(logFilter) || l.type.includes(logFilter))
    : logs;
  
  logContainer.innerHTML = filtered.slice(0, 200).map(l => `
    <div class="log-entry">
      <span class="log-time">${formatTime(l.ts)}</span>
      <span class="log-type ${l.type}">${l.type}</span>
      <span class="log-msg">${escapeHtml(l.msg)}</span>
    </div>
  `).join('');
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Animation loop using requestAnimationFrame with deltaTime
function animate(currentTime) {
  const deltaTime = (currentTime - lastFrameTime) / 1000; // seconds
  lastFrameTime = currentTime;
  
  if (lastSnapshot) {
    draw(lastSnapshot, deltaTime);
  }
  
  animationId = requestAnimationFrame(animate);
}

// Start animation loop
animationId = requestAnimationFrame(animate);

function draw(snapshot, deltaTime) {
  const w = canvas.width;
  const h = canvas.height;
  
  // Clear with gradient
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, '#0c1222');
  grad.addColorStop(1, '#1a1a2e');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);

  // Grid
  ctx.strokeStyle = '#1e293b';
  ctx.lineWidth = 1;
  for (let x = 0; x <= w; x += 45) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let y = 0; y <= h; y += 45) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  // World coords from config (default 100x60)
  const worldWidth = 100;
  const worldHeight = 60;
  const sx = w / worldWidth;
  const sy = h / worldHeight;

  // Draw particles with interpolation for smooth movement
  for (const p of snapshot.particles) {
    // Interpolate position using velocity and deltaTime for smoother rendering
    let px = p.x;
    let py = p.y;
    
    // Apply velocity-based interpolation (client-side prediction)
    if (deltaTime < 0.5) { // Only interpolate for reasonable frame times
      px += p.vx * deltaTime * 0.3; // Subtle smoothing
      py += p.vy * deltaTime * 0.3;
    }
    
    // Clamp to world bounds
    px = Math.max(0, Math.min(px, worldWidth));
    py = Math.max(0, Math.min(py, worldHeight));
    
    // Convert to screen coords
    const screenX = px * sx;
    const screenY = py * sy;
    
    // Glow effect
    const glow = ctx.createRadialGradient(screenX, screenY, 0, screenX, screenY, 20);
    glow.addColorStop(0, 'rgba(59, 130, 246, 0.4)');
    glow.addColorStop(1, 'rgba(59, 130, 246, 0)');
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(screenX, screenY, 20, 0, Math.PI * 2);
    ctx.fill();

    // Particle body
    ctx.beginPath();
    ctx.fillStyle = '#3b82f6';
    ctx.arc(screenX, screenY, 6, 0, Math.PI * 2);
    ctx.fill();
    
    // Inner highlight
    ctx.beginPath();
    ctx.fillStyle = '#93c5fd';
    ctx.arc(screenX - 2, screenY - 2, 2, 0, Math.PI * 2);
    ctx.fill();
  }
}

function updateStats(snapshot) {
  document.getElementById('stat-tick').textContent = snapshot.tick;
  document.getElementById('stat-time').textContent = snapshot.sim_time_s.toFixed(1) + 's';
  document.getElementById('stat-particles').textContent = snapshot.particles.length;
}

// SSE connection with exponential backoff
let es = null;
let sseReconnectDelay = 1000;
const SSE_MAX_DELAY = 30000;

function connectSSE() {
  if (es) {
    es.close();
  }
  
  es = new EventSource('/events');
  
  es.addEventListener('state', (e) => {
    const s = JSON.parse(e.data);
    previousSnapshot = lastSnapshot;
    lastSnapshot = s;
    updateStats(s);
    addLog('state', `tick=${s.tick} particles=${s.particles.length}`, s.sim_time_s);
  });
  
  es.addEventListener('event', (e) => {
    const data = JSON.parse(e.data);
    // Handle engine events
    if (data.kind === 'engine_stopped') {
      addLog('event', `Engine stopped at tick ${data.tick}`);
    } else if (data.kind === 'paused') {
      addLog('event', 'Simulation paused');
    } else if (data.kind === 'resumed') {
      addLog('event', 'Simulation resumed');
    } else if (data.kind === 'reset') {
      addLog('event', 'Simulation reset');
    } else {
      addLog('event', JSON.stringify(data));
    }
  });
  
  es.onopen = () => {
    sseReconnectDelay = 1000; // Reset backoff on success
    connDot.classList.remove('disconnected');
    connText.textContent = 'Connected';
    addLog('event', 'SSE connection established');
  };
  
  es.onerror = () => {
    connDot.classList.add('disconnected');
    connText.textContent = 'Reconnecting...';
    addLog('error', `SSE connection lost, retrying in ${sseReconnectDelay/1000}s...`);
    
    es.close();
    
    // Exponential backoff with jitter
    setTimeout(() => {
      connectSSE();
    }, sseReconnectDelay + Math.random() * 500);
    
    sseReconnectDelay = Math.min(sseReconnectDelay * 2, SSE_MAX_DELAY);
  };
}

connectSSE();

// Poll bus stats and clients (requires basic auth)
async function refreshStats() {
  if (!apiCredentials) return;
  
  try {
    // Fetch stats
    const r = await fetch('/api/v1/stats', {
      headers: { 'Authorization': 'Basic ' + apiCredentials }
    });
    if (r.status === 401) {
      apiCredentials = null;
      localStorage.removeItem('apiCredentials');
      return;
    }
    const s = await r.json();
    document.getElementById('stat-subs').textContent = s.bus.subscriber_count;
    document.getElementById('stat-published').textContent = s.bus.total_published.toLocaleString();
    document.getElementById('stat-dropped').textContent = s.bus.total_dropped.toLocaleString();
    document.getElementById('stat-delivered').textContent = s.bus.total_delivered.toLocaleString();
    
    // Fetch subscribers/clients
    const r2 = await fetch('/api/v1/subscribers', {
      headers: { 'Authorization': 'Basic ' + apiCredentials }
    });
    if (r2.ok) {
      const clients = await r2.json();
      renderClients(clients);
    }
  } catch (e) {}
}

function renderClients(clients) {
  if (!clients || clients.length === 0) {
    clientsList.innerHTML = '<div class="client-empty">No clients connected</div>';
    return;
  }
  
  clientsList.innerHTML = clients.map(c => `
    <div class="client-item">
      <span class="client-name">${c.name}</span>
      <span class="client-stats"> ^${c.received} x${c.dropped}</span>
    </div>
  `).join('');
}

// Configurable refresh interval for stats
let statsIntervalId = setInterval(refreshStats, 2000);

function setRefreshInterval(ms) {
  clearInterval(statsIntervalId);
  if (ms > 0) {
    statsIntervalId = setInterval(refreshStats, parseInt(ms));
    refreshStats();
  }
}

refreshStats();

// Heartbeat polling - checks server health and detects stuck simulation
async function checkHeartbeat() {
  try {
    const r = await fetch('/api/v1/heartbeat');
    if (!r.ok) {
      heartbeatOk = false;
      connDot.classList.add('disconnected');
      connText.textContent = 'Server Error';
      addLog('error', `Heartbeat failed: HTTP ${r.status}`);
      return;
    }
    
    const data = await r.json();
    const engineState = data.engine_state || 'unknown';
    
    // Update connection status based on engine state
    if (engineState === 'paused') {
      connText.textContent = 'Paused';
      heartbeatStuckCount = 0;
    } else if (engineState === 'stopped') {
      connText.textContent = 'Stopped';
      heartbeatStuckCount = 0;
    } else if (engineState === 'running') {
      // Check if simulation is stuck (tick not advancing while running)
      if (lastHeartbeatTick !== null && data.tick === lastHeartbeatTick) {
        heartbeatStuckCount++;
        if (heartbeatStuckCount >= 3) {
          connText.textContent = 'Simulation Stuck';
          addLog('error', `Simulation stuck at tick ${data.tick}`);
        }
      } else {
        heartbeatStuckCount = 0;
        connText.textContent = 'Connected';
      }
    }
    lastHeartbeatTick = data.tick;
    
    // Update status if was disconnected
    if (!heartbeatOk) {
      heartbeatOk = true;
      connDot.classList.remove('disconnected');
      addLog('event', 'Server connection restored');
    }
  } catch (e) {
    heartbeatOk = false;
    connDot.classList.add('disconnected');
    connText.textContent = 'Server Offline';
    addLog('error', 'Heartbeat failed: ' + e.message);
  }
}

// Poll heartbeat every 3 seconds
setInterval(checkHeartbeat, 3000);
checkHeartbeat();
