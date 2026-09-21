// ResQAI dashboard logic
// Handles: simulated sensor feed, chart, ML predict calls, confirmation
// countdown, emergency dispatch, and the hospital map.

(function () {
  "use strict";

  const DEFAULT_LOC = window.DEFAULT_LOCATION || { lat: 17.385, lon: 78.4867 };

  // ---------------------------------------------------------------------
  // Chart setup
  // ---------------------------------------------------------------------
  const MAX_POINTS = 40;
  const chartLabels = [];
  const accData = [];
  const gyroData = [];

  const ctx = document.getElementById("sensorChart").getContext("2d");
  const sensorChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: chartLabels,
      datasets: [
        {
          label: "Acc. magnitude (m/s\u00b2)",
          data: accData,
          borderColor: "#dc2626",
          backgroundColor: "rgba(220,38,38,0.08)",
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: "Gyro magnitude (rad/s)",
          data: gyroData,
          borderColor: "#2563eb",
          backgroundColor: "rgba(37,99,235,0.08)",
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 2,
          yAxisID: "y1",
        },
      ],
    },
    options: {
      animation: false,
      responsive: true,
      interaction: { mode: "index", intersect: false },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: "m/s\u00b2" } },
        y1: {
          beginAtZero: true,
          position: "right",
          grid: { drawOnChartArea: false },
          title: { display: true, text: "rad/s" },
        },
      },
      plugins: { legend: { labels: { boxWidth: 12, font: { size: 10 } } } },
    },
  });

  function pushChartPoint(reading) {
    const t = new Date().toLocaleTimeString();
    chartLabels.push(t);
    accData.push(reading.acc_magnitude);
    gyroData.push(reading.gyro_magnitude);
    if (chartLabels.length > MAX_POINTS) {
      chartLabels.shift();
      accData.shift();
      gyroData.shift();
    }
    sensorChart.update();
  }

  // ---------------------------------------------------------------------
  // Map setup
  // ---------------------------------------------------------------------
  const map = L.map("map").setView([DEFAULT_LOC.lat, DEFAULT_LOC.lon], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 18,
  }).addTo(map);

  let userMarker = null;
  let hospitalMarkers = [];

  function clearHospitalMarkers() {
    hospitalMarkers.forEach((m) => map.removeLayer(m));
    hospitalMarkers = [];
  }

  function plotEmergency(lat, lon, hospitals) {
    if (userMarker) map.removeLayer(userMarker);
    userMarker = L.marker([lat, lon], {
      icon: L.divIcon({
        className: "",
        html: '<i class="fa-solid fa-car-burst fa-2x" style="color:#dc2626"></i>',
        iconSize: [30, 30],
      }),
    }).addTo(map).bindPopup("Accident location").openPopup();

    clearHospitalMarkers();
    hospitals.forEach((h, idx) => {
      const marker = L.marker([h.lat, h.lon], {
        icon: L.divIcon({
          className: "",
          html: '<i class="fa-solid fa-hospital fa-lg" style="color:#2563eb"></i>',
          iconSize: [22, 22],
        }),
      })
        .addTo(map)
        .bindPopup(`${h.name}<br>${h.distance_km} km &bull; ${h.phone}`);
      hospitalMarkers.push(marker);
      if (idx === 0) marker.openPopup();
    });

    map.setView([lat, lon], 13);
  }

  // ---------------------------------------------------------------------
  // Status / event log helpers
  // ---------------------------------------------------------------------
  const statusIcon = document.getElementById("status-icon");
  const statusText = document.getElementById("status-text");
  const severityBadge = document.getElementById("severity-badge");
  const confText = document.getElementById("conf-text");
  const confBar = document.getElementById("conf-bar");
  const modelSourceEl = document.getElementById("model-source");
  const lastUpdateEl = document.getElementById("last-update");
  const eventLog = document.getElementById("event-log");

  const SEVERITY_STYLE = {
    None: { cls: "status-safe", badge: "bg-success", icon: "fa-circle-check" },
    Minor: { cls: "status-warning", badge: "bg-warning text-dark", icon: "fa-triangle-exclamation" },
    Moderate: { cls: "status-warning", badge: "bg-orange bg-warning text-dark", icon: "fa-triangle-exclamation" },
    Severe: { cls: "status-danger", badge: "bg-danger", icon: "fa-car-burst" },
  };

  function logEvent(text, level) {
    if (eventLog.children.length === 1 && eventLog.children[0].textContent.trim() === "No events yet.") {
      eventLog.innerHTML = "";
    }
    const li = document.createElement("li");
    li.className = "list-group-item";
    const color = level === "Severe" ? "text-danger" : level === "None" ? "text-muted" : "text-warning-emphasis";
    li.innerHTML = `<span class="${color}">[${new Date().toLocaleTimeString()}]</span> ${text}`;
    eventLog.prepend(li);
    while (eventLog.children.length > 25) eventLog.removeChild(eventLog.lastChild);
  }

  function updateStatusUI(result) {
    const style = SEVERITY_STYLE[result.severity_label] || SEVERITY_STYLE["None"];
    statusIcon.className = "status-icon " + style.cls;
    statusIcon.innerHTML = `<i class="fa-solid ${style.icon}"></i>`;
    statusText.textContent = result.accident_detected
      ? `Accident Detected (${result.severity_label})`
      : "No Accident \u2014 Normal";
    severityBadge.className = "badge " + style.badge + " mb-3";
    severityBadge.textContent = "Severity: " + result.severity_label;
    const pct = Math.round(result.confidence * 100);
    confText.textContent = pct + "%";
    confBar.style.width = pct + "%";
    confBar.className = "progress-bar " + (result.accident_detected ? "bg-danger" : "bg-success");
    modelSourceEl.textContent = result.model_source === "trained_ml_model" ? "Trained ML model" : "Rule-based fallback";
    lastUpdateEl.textContent = new Date().toLocaleTimeString();
  }

  // ---------------------------------------------------------------------
  // Confirmation countdown modal
  // ---------------------------------------------------------------------
  const confirmModalEl = document.getElementById("confirmModal");
  const confirmModal = new bootstrap.Modal(confirmModalEl);
  const countdownEl = document.getElementById("countdown");
  const countdownBig = document.getElementById("countdown-big");
  const modalSeverityEl = document.getElementById("modal-severity");
  let countdownTimer = null;
  let pendingResult = null;

  function startCountdown(result) {
    pendingResult = result;
    let seconds = 15;
    countdownEl.textContent = seconds;
    countdownBig.textContent = seconds;
    modalSeverityEl.textContent = result.severity_label;
    confirmModal.show();

    clearInterval(countdownTimer);
    countdownTimer = setInterval(() => {
      seconds -= 1;
      countdownEl.textContent = seconds;
      countdownBig.textContent = seconds;
      if (seconds <= 0) {
        clearInterval(countdownTimer);
        confirmModal.hide();
        dispatchEmergency(pendingResult);
      }
    }, 1000);
  }

  document.getElementById("im-fine-btn").addEventListener("click", () => {
    clearInterval(countdownTimer);
    confirmModal.hide();
    logEvent("User confirmed they are OK. Alert cancelled.", "None");
  });

  document.getElementById("send-now-btn").addEventListener("click", () => {
    clearInterval(countdownTimer);
    confirmModal.hide();
    dispatchEmergency(pendingResult);
  });

  // ---------------------------------------------------------------------
  // Emergency dispatch
  // ---------------------------------------------------------------------
  const dispatchModal = new bootstrap.Modal(document.getElementById("dispatchModal"));
  const dispatchMessageEl = document.getElementById("dispatch-message");

  function withLocation(callback) {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => callback(pos.coords.latitude, pos.coords.longitude),
        () => callback(null, null),
        { timeout: 3000 }
      );
    } else {
      callback(null, null);
    }
  }

  function dispatchEmergency(result) {
    withLocation((lat, lon) => {
      const payload = {
        severity_label: result.severity_label,
        confidence: result.confidence,
      };
      if (lat !== null) {
        payload.lat = lat;
        payload.lon = lon;
      }
      fetch("/api/emergency", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then((r) => r.json())
        .then((data) => {
          dispatchMessageEl.textContent = data.message;
          dispatchModal.show();
          plotEmergency(data.location.lat, data.location.lon, data.nearest_hospitals);

          const info = document.getElementById("hospital-info");
          const nearest = data.nearest_hospitals[0];
          info.innerHTML = nearest
            ? `<strong>${nearest.name}</strong><br>${nearest.distance_km} km away &bull; <a href="tel:${nearest.phone}">${nearest.phone}</a>`
            : "No hospital data available.";

          logEvent(`Emergency alert dispatched (ID ${data.alert_id}).`, "Severe");
        })
        .catch(() => logEvent("Failed to reach emergency service endpoint.", "Severe"));
    });
  }

  // ---------------------------------------------------------------------
  // Prediction pipeline
  // ---------------------------------------------------------------------
  function runPrediction(reading) {
    fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reading),
    })
      .then((r) => r.json())
      .then((result) => {
        pushChartPoint(reading.acc_magnitude !== undefined ? reading : result.features_used);
        updateStatusUI(result);
        logEvent(
          `${result.accident_detected ? "ACCIDENT" : "normal reading"} \u2014 severity ${result.severity_label}, confidence ${Math.round(result.confidence * 100)}%`,
          result.severity_label
        );
        if (result.severity_label === "Moderate" || result.severity_label === "Severe") {
          startCountdown(result);
        }
      })
      .catch(() => logEvent("Prediction request failed. Is the Flask server running?", "Severe"));
  }

  // ---------------------------------------------------------------------
  // Scenario buttons
  // ---------------------------------------------------------------------
  document.querySelectorAll(".scenario-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const scenario = btn.dataset.scenario;
      fetch(`/api/simulate?scenario=${scenario}`)
        .then((r) => r.json())
        .then((reading) => runPrediction(reading));
    });
  });

  // ---------------------------------------------------------------------
  // Manual override
  // ---------------------------------------------------------------------
  document.getElementById("manual-predict-btn").addEventListener("click", () => {
    const val = (id) => parseFloat(document.getElementById(id).value || "0");
    const reading = {
      acc_x: val("acc_x"),
      acc_y: val("acc_y"),
      acc_z: val("acc_z"),
      gyro_x: 0,
      gyro_y: 0,
      gyro_z: val("gyro_magnitude"),
      gyro_magnitude: val("gyro_magnitude"),
      speed_before: val("speed_before"),
      speed_change: val("speed_change"),
      jerk: val("jerk"),
    };
    reading.acc_magnitude = Math.sqrt(reading.acc_x ** 2 + reading.acc_y ** 2 + reading.acc_z ** 2);
    runPrediction(reading);
  });

  // ---------------------------------------------------------------------
  // Live monitoring toggle
  // ---------------------------------------------------------------------
  const liveBtn = document.getElementById("live-toggle");
  const liveStatus = document.getElementById("live-status");
  let liveInterval = null;

  liveBtn.addEventListener("click", () => {
    if (liveInterval) {
      clearInterval(liveInterval);
      liveInterval = null;
      liveBtn.innerHTML = '<i class="fa-solid fa-play me-1"></i>Start Live Monitoring';
      liveStatus.textContent = "Monitoring stopped";
    } else {
      liveBtn.innerHTML = '<i class="fa-solid fa-stop me-1"></i>Stop Live Monitoring';
      liveStatus.textContent = "Monitoring\u2026 streaming sensor data every 1.5s";
      liveInterval = setInterval(() => {
        fetch("/api/simulate?scenario=random")
          .then((r) => r.json())
          .then((reading) => runPrediction(reading));
      }, 1500);
    }
  });

  // ---------------------------------------------------------------------
  // Initial hospital preview on load
  // ---------------------------------------------------------------------
  fetch(`/api/hospitals?lat=${DEFAULT_LOC.lat}&lon=${DEFAULT_LOC.lon}&k=5`)
    .then((r) => r.json())
    .then((data) => {
      data.hospitals.forEach((h) => {
        L.marker([h.lat, h.lon], {
          icon: L.divIcon({
            className: "",
            html: '<i class="fa-solid fa-hospital" style="color:#6b7280"></i>',
            iconSize: [16, 16],
          }),
        })
          .addTo(map)
          .bindPopup(`${h.name}<br>${h.distance_km} km`);
      });
    });
})();
