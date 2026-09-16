/* Dashboard — carga los gráficos de Chart.js desde el endpoint JSON */
(function () {
  const PALETA = {
    tomate: "#DC2626",
    naranja: "#EA580C",
    crema: "#FEF3C7",
    carbon: "#1C1917",
    verde: "#16a34a",
    amarillo: "#f59e0b",
  };
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  Chart.defaults.color = "#57534e";

  let charts = {};

  function make(id, config) {
    const el = document.getElementById(id);
    if (!el) return;
    if (charts[id]) charts[id].destroy();
    charts[id] = new Chart(el, config);
  }

  async function load() {
    let d;
    try {
      d = await (await fetch(window.CHARTS_URL)).json();
    } catch (e) {
      return;
    }

    make("chartVentasDia", {
      type: "line",
      data: {
        labels: d.ventas_dia.labels,
        datasets: [{
          label: "Ventas ($)",
          data: d.ventas_dia.data,
          borderColor: PALETA.tomate,
          backgroundColor: "rgba(220,38,38,.12)",
          fill: true, tension: .35, pointRadius: 3,
        }],
      },
      options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
    });

    make("chartOcupacion", {
      type: "doughnut",
      data: {
        labels: d.ocupacion.labels,
        datasets: [{
          data: d.ocupacion.data,
          backgroundColor: [PALETA.verde, PALETA.tomate, PALETA.amarillo],
          borderWidth: 2, borderColor: "#fff",
        }],
      },
      options: { plugins: { legend: { position: "bottom" } }, cutout: "62%" },
    });

    make("chartTop", {
      type: "bar",
      data: {
        labels: d.top_platillos.labels,
        datasets: [{
          label: "Unidades",
          data: d.top_platillos.data,
          backgroundColor: PALETA.naranja,
          borderRadius: 6,
        }],
      },
      options: { indexAxis: "y", plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true } } },
    });

    make("chartVentasMes", {
      type: "bar",
      data: {
        labels: d.ventas_mes.labels,
        datasets: [{
          label: "Ventas ($)",
          data: d.ventas_mes.data,
          backgroundColor: PALETA.carbon,
          borderRadius: 6,
        }],
      },
      options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
    });
  }

  load();
  setInterval(load, 60000);
})();
