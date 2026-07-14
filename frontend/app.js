const ws = new WebSocket(`ws://${window.location.host}/ws`);
const objects = {};
let currentOid = null;
let chart = null;

// UI Elements
const els = {
    list: document.getElementById('object-list'),
    title: document.getElementById('current-oid'),
    badge: document.getElementById('prediction-badge'),
    tau: document.getElementById('metric-tau'),
    sigma: document.getElementById('metric-sigma'),
    pts: document.getElementById('metric-points')
};

// Initialize Chart with Astronomical Bands
function initChart() {
    const ctx = document.getElementById('lightcurveChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'scatter',
        data: { 
            datasets: [
                { 
                    label: 'g-band (Green)', 
                    data: [], 
                    backgroundColor: '#33ff99', 
                    borderColor: '#33ff99',
                    pointRadius: 3, 
                    pointHoverRadius: 6 
                },
                { 
                    label: 'r-band (Red)', 
                    data: [], 
                    backgroundColor: '#ff3366', 
                    borderColor: '#ff3366',
                    pointRadius: 3, 
                    pointHoverRadius: 6 
                }
            ] 
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                x: { 
                    type: 'linear', 
                    title: { display: true, text: 'Time (MJD)', color: '#8892b0' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#8892b0' }
                },
                y: { 
                    reverse: true, 
                    title: { display: true, text: 'Magnitude', color: '#8892b0' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#8892b0' }
                }
            },
            plugins: { 
                legend: { display: true, labels: { color: '#8892b0' } } 
            },
            animation: false
        }
    });
}

// Select an Object
function selectObject(oid) {
    if (currentOid) document.getElementById(`list-${currentOid}`)?.classList.remove('active');
    currentOid = oid;
    document.getElementById(`list-${currentOid}`)?.classList.add('active');
    els.title.textContent = `Object: ${oid}`;
    updateUI();
}

// Handle UI updates safely
function updateUI() {
    try {
        if (!currentOid || !objects[currentOid]) return;
        const obj = objects[currentOid];
        
        // Update Chart Datasets
        chart.data.datasets[0].data = obj.points_g;
        chart.data.datasets[1].data = obj.points_r;
        chart.update();
        
        // Update Metrics
        els.pts.textContent = obj.points_g.length + obj.points_r.length;
        if (obj.prediction) {
            els.badge.style.display = 'block';
            els.badge.textContent = obj.prediction.classification;
            els.badge.className = 'prediction-badge ' + (obj.prediction.classification === 'AGN' ? 'badge-agn' : 'badge-star');
            els.tau.textContent = obj.prediction.tau;
            els.sigma.textContent = obj.prediction.sigma;
        }
    } catch (e) {
        console.error("UI Update Error:", e);
    }
}

let pendingUpdate = false;
function requestUpdateUI() {
    if (!pendingUpdate) {
        pendingUpdate = true;
        requestAnimationFrame(() => { updateUI(); pendingUpdate = false; });
    }
}

// Handle WebSocket messages
ws.onmessage = (event) => {
    try {
        const msg = JSON.parse(event.data);
        const data = msg.data;
        if (!data || !data.oid) {
            console.warn("Received malformed data:", msg);
            return;
        }
        
        const oid = data.oid;
        
        if (!objects[oid]) {
            console.log("New OID detected:", oid);
            objects[oid] = { points_g: [], points_r: [], prediction: null };
            
            if (Object.keys(objects).length <= 100) {
                const li = document.createElement('li');
                li.id = `list-${oid}`;
                li.textContent = oid;
                li.onclick = () => selectObject(oid);
                els.list.appendChild(li);
            }
            
            if (!currentOid) selectObject(oid);
        }
        
        if (msg.type === 'point' && data.mjd && data.mag) {
            const pt = { x: data.mjd, y: data.mag };
            if (data.fid === 1) {
                objects[oid].points_g.push(pt);
            } else {
                objects[oid].points_r.push(pt);
            }
        } else if (msg.type === 'prediction') {
            console.log("Prediction received for", oid, ":", data);
            objects[oid].prediction = data;
        }
        
        if (currentOid === oid) requestUpdateUI();
    } catch (e) {
        console.error("WebSocket Message Error:", e);
    }
};

initChart();
