const DEFAULT_PAGE_SIZE = 9;

function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function showToast(title, message, type = "success") {
    document.getElementById("toastTitle").textContent = title;
    document.getElementById("toastContent").textContent = message;
    const toastEl = document.getElementById("appToast");
    toastEl.className = `toast text-bg-${type}`;
    new bootstrap.Toast(toastEl).show();
}

function readStateFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const page = Math.max(parseInt(params.get("page") || "1", 10), 1);
    const q = (params.get("q") || "").trim();
    const sortBy = params.get("sort_by") === "name" ? "name" : "created_at";
    return { page, q, sortBy, pageSize: DEFAULT_PAGE_SIZE };
}

function syncStateToUrl(state) {
    const params = new URLSearchParams();
    if (state.q) params.set("q", state.q);
    if (state.sortBy !== "created_at") params.set("sort_by", state.sortBy);
    if (state.page > 1) params.set("page", String(state.page));
    const query = params.toString();
    const nextUrl = query ? `${window.location.pathname}?${query}` : window.location.pathname;
    window.history.replaceState(null, "", nextUrl);
}

function setLoading() {
    document.getElementById("routinesGrid").innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
}

async function fetchRoutines(state) {
    const params = new URLSearchParams({
        page: String(state.page),
        page_size: String(state.pageSize),
        sort_by: state.sortBy,
    });
    if (state.q) params.set("q", state.q);

    const res = await fetch(`/api/routines?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to load routines");
    return res.json();
}

function attachDeleteListeners() {
    document.querySelectorAll(".delete-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.getElementById("deleteRoutineId").value = btn.dataset.routineId;
            document.getElementById("deleteRoutineName").textContent = btn.dataset.routineName;
            new bootstrap.Modal(document.getElementById("deleteRoutineModal")).show();
        });
    });
}

function renderRoutines(items, totalItems, hasSearch) {
    const grid = document.getElementById("routinesGrid");

    if (!items.length) {
        const message = hasSearch
            ? "No routines matched your search. Try a different name or clear filters."
            : "No routines yet. Create one to get started!";
        grid.innerHTML = `<div class="col-12 text-center py-5 text-muted">
            <div class="routine-empty-state mx-auto">
                <span class="material-symbols-outlined icon-lg">fitness_center</span>
                <p class="mt-2 mb-0">${message}</p>
            </div>
        </div>`;
        return;
    }

    grid.innerHTML = items
        .map(
            (routine) => `
        <div class="col-sm-6 col-md-4">
            <div class="card h-100 shadow-sm routine-card">
                <div class="card-body d-flex flex-column">
                    <div class="d-flex align-items-start justify-content-between gap-2 mb-2">
                        <div>
                            <h5 class="card-title mb-1">${escapeHtml(routine.name)}</h5>
                            <p class="card-text text-muted small mb-0">Created ${new Date(routine.created_at).toLocaleDateString()}</p>
                        </div>
                        <span class="badge text-bg-light border routine-count-pill">${routine.workout_count || 0} ${(routine.workout_count || 0) === 1 ? "exercise" : "exercises"}</span>
                    </div>
                    <div class="routine-card-rail mt-auto pt-3">
                        <a href="/routines/${routine.id}" class="btn btn-primary btn-sm flex-grow-1">
                            <span class="material-symbols-outlined me-1 icon-inline-middle icon-sm">open_in_new</span>
                            View Routine
                        </a>
                        <button class="btn btn-outline-danger btn-sm delete-btn" data-routine-id="${routine.id}" data-routine-name="${escapeHtml(routine.name)}">
                            <span class="material-symbols-outlined icon-sm">delete</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `,
        )
        .join("");

    attachDeleteListeners();
    document.getElementById("paginationSummary").textContent = `${totalItems} ${totalItems === 1 ? "routine" : "routines"}`;
}

function buildPageList(current, total) {
    const pages = [];
    if (total <= 7) {
        for (let page = 1; page <= total; page += 1) pages.push(page);
        return pages;
    }
    pages.push(1);
    if (current > 3) pages.push("...");
    for (let page = Math.max(2, current - 1); page <= Math.min(total - 1, current + 1); page += 1) pages.push(page);
    if (current < total - 2) pages.push("...");
    pages.push(total);
    return pages;
}

function renderPagination(meta, state, onPageChange) {
    const wrap = document.getElementById("routinesPaginationWrap");
    const ul = document.getElementById("routinesPagination");

    if (meta.total_pages <= 1) {
        wrap.style.setProperty("display", "none", "important");
        ul.innerHTML = "";
        return;
    }

    wrap.style.setProperty("display", "flex", "important");
    const pages = buildPageList(meta.page, meta.total_pages);
    const prevDisabled = meta.page <= 1;
    const nextDisabled = meta.page >= meta.total_pages;

    const prevBtn = `<li class="page-item ${prevDisabled ? "disabled" : ""}">
            <button class="page-link" data-page="${meta.page - 1}" ${prevDisabled ? "disabled" : ""}>Previous</button>
        </li>`;
    const nextBtn = `<li class="page-item ${nextDisabled ? "disabled" : ""}">
            <button class="page-link" data-page="${meta.page + 1}" ${nextDisabled ? "disabled" : ""}>Next</button>
        </li>`;
    const pageBtns = pages
        .map((page) => {
            if (page === "...") return '<li class="page-item disabled"><span class="page-link">...</span></li>';
            const active = page === meta.page ? "active" : "";
            return `<li class="page-item ${active}"><button class="page-link" data-page="${page}">${page}</button></li>`;
        })
        .join("");

    ul.innerHTML = `${prevBtn}${pageBtns}${nextBtn}`;
    ul.querySelectorAll("button[data-page]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const page = parseInt(btn.dataset.page, 10);
            if (!Number.isNaN(page) && page !== state.page) onPageChange(page);
        });
    });
}

async function createRoutine(name) {
    const res = await fetch("/api/routines", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error("Failed to create routine");
    return res.json();
}

async function deleteRoutine(routineId) {
    const res = await fetch(`/api/routines/${routineId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete routine");
}

async function main() {
    const state = readStateFromUrl();
    const searchInput = document.getElementById("routineSearch");
    const sortBySelect = document.getElementById("sortBy");
    const clearSearchBtn = document.getElementById("clearSearchBtn");

    searchInput.value = state.q;
    sortBySelect.value = state.sortBy;

    let latestMeta = null;

    async function loadAndRender() {
        setLoading();
        syncStateToUrl(state);
        try {
            const payload = await fetchRoutines(state);
            latestMeta = payload;

            if (payload.items.length === 0 && payload.total_items > 0 && state.page > 1) {
                state.page -= 1;
                await loadAndRender();
                return;
            }

            renderRoutines(payload.items, payload.total_items, Boolean(state.q));
            renderPagination(payload, state, async (nextPage) => {
                state.page = nextPage;
                await loadAndRender();
            });
        } catch {
            document.getElementById("routinesGrid").innerHTML = `
                <div class="col-12 text-center py-5 text-danger">
                    <span class="material-symbols-outlined icon-lg">error</span>
                    <p class="mt-2 mb-0">Could not load routines right now.</p>
                </div>
            `;
            document.getElementById("routinesPaginationWrap").style.setProperty("display", "none", "important");
        }
    }

    await loadAndRender();

    searchInput.addEventListener("keydown", async (event) => {
        if (event.key === "Enter") {
            state.q = searchInput.value.trim();
            state.page = 1;
            await loadAndRender();
        }
    });

    clearSearchBtn.addEventListener("click", async () => {
        if (!state.q && !searchInput.value.trim()) return;
        searchInput.value = "";
        state.q = "";
        state.page = 1;
        await loadAndRender();
    });

    sortBySelect.addEventListener("change", async () => {
        state.sortBy = sortBySelect.value;
        state.page = 1;
        await loadAndRender();
    });

    document.getElementById("createRoutineBtn").addEventListener("click", async () => {
        const name = document.getElementById("routineName").value.trim();
        if (!name) return;
        try {
            await createRoutine(name);
            bootstrap.Modal.getInstance(document.getElementById("createRoutineModal")).hide();
            document.getElementById("routineName").value = "";
            state.page = 1;
            await loadAndRender();
            showToast("Success", "Routine created!");
        } catch {
            showToast("Error", "Could not create routine", "danger");
        }
    });

    document.getElementById("confirmDeleteBtn").addEventListener("click", async () => {
        const routineId = document.getElementById("deleteRoutineId").value;
        try {
            await deleteRoutine(routineId);
            bootstrap.Modal.getInstance(document.getElementById("deleteRoutineModal")).hide();
            if (latestMeta && latestMeta.items.length === 1 && state.page > 1) state.page -= 1;
            await loadAndRender();
            showToast("Success", "Routine deleted");
        } catch {
            showToast("Error", "Could not delete routine", "danger");
        }
    });
}

main();
