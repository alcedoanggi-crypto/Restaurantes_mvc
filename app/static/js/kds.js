/* KDS — refresco por polling cada 5s y render en cliente */
(function () {
  const board = document.getElementById("board");
  const reloj = document.getElementById("reloj");
  const btnLabel = { pendiente: "Empezar", en_preparacion: "Listo" };

  function tick(t) {
    const items = t.items.map((d) => {
      const acc =
        window.CAN_EDIT && d.estado !== "listo"
          ? `<button class="btn btn-sm btn-outline-dark" data-avanzar="${d.id}">${btnLabel[d.estado]}</button>`
          : d.estado === "listo"
          ? '<i class="bi bi-check-circle-fill text-success"></i>'
          : "";
      return `<div class="kds-item estado-${d.estado}">
        <div><span class="qty">${d.cantidad}</span> ${d.nombre}
        ${d.notas ? `<div class="nota">“${d.notas}”</div>` : ""}</div>
        ${acc}</div>`;
    }).join("");

    const completar =
      window.CAN_EDIT && !t.todo_listo
        ? `<div class="p-2"><form class="d-grid"><button class="btn btn-sm btn-tomate" data-listo="${t.pedido_id}">Marcar pedido completo</button></form></div>`
        : "";

    return `<div class="kds-card ${t.nivel}">
      <div class="kds-head"><span class="mesa">Mesa ${t.mesa}</span>
      <span class="small">#${t.pedido_id} · ${t.espera} min</span></div>
      <div>${items}</div>${completar}</div>`;
  }

  async function refrescar() {
    let data;
    try {
      data = await (await fetch(window.FEED_URL)).json();
    } catch (e) {
      return;
    }
    if (!data.tickets.length) {
      board.innerHTML =
        '<div class="text-center text-muted py-5 w-100"><i class="bi bi-emoji-smile fs-1"></i><p>No hay pedidos pendientes en cocina.</p></div>';
    } else {
      board.innerHTML = data.tickets.map(tick).join("");
    }
    if (reloj) reloj.textContent = new Date().toLocaleTimeString();
  }

  async function post(url) {
    await fetch(url, { method: "POST", headers: { "X-Requested-With": "fetch" } });
    refrescar();
  }

  board.addEventListener("click", (e) => {
    const av = e.target.closest("[data-avanzar]");
    const li = e.target.closest("[data-listo]");
    if (av) {
      e.preventDefault();
      post(window.AVANZAR_URL.replace("/0/", "/" + av.dataset.avanzar + "/"));
    } else if (li) {
      e.preventDefault();
      post(window.LISTO_URL.replace("/0/", "/" + li.dataset.listo + "/"));
    }
  });

  refrescar();
  setInterval(refrescar, 5000);
})();
