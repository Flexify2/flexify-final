let currentSearchResults = [];
const searchCache = new Map();
let detailsModalInstance = null;
let addToRoutineModalInstance = null;

function escapeHtml(text) {
    return String(text || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

async function fetchWorkouts(q = "", muscleGroup = "", category = "", equipment = "") {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (muscleGroup) params.set("muscle_group", muscleGroup);
    if (category) params.set("category", category);
    if (equipment) params.set("equipment", equipment);
    params.set("limit", "20");
    const res = await fetch(`/api/workouts/external/search?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to load exercises");
    return res.json();
}

function getSearchState() {
    return {
        q: document.getElementById("searchInput").value.trim().toLowerCase(),
        muscleGroup: document.getElementById("muscleGroupFilter").value,
        category: document.getElementById("categoryFilter").value,
        equipment: document.getElementById("equipmentFilter").value,
    };
}

function getSearchKey(state) {
    return JSON.stringify(state);
}

function setGridLoading() {
    const grid = document.getElementById("workoutsGrid");
    grid.innerHTML = `<div class="col-12 text-center py-5">
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    </div>`;
}

function updateResultsMeta(count, failed = false) {
    const el = document.getElementById("searchResultsMeta");
    if (!el) return;
    if (failed) {
        el.textContent = "Search failed. Please try again.";
        return;
    }
    if (!count) {
        el.textContent = "0 results found.";
        return;
    }
    el.textContent = `${count} result${count === 1 ? "" : "s"} found.`;
}

async function runSearch() {
    const state = getSearchState();
    const cacheKey = getSearchKey(state);
    if (searchCache.has(cacheKey)) {
        renderWorkouts(searchCache.get(cacheKey));
        return;
    }

    setGridLoading();
    try {
        const results = await fetchWorkouts(state.q, state.muscleGroup, state.category, state.equipment);
        searchCache.set(cacheKey, results);
        renderWorkouts(results);
    } catch (_) {
        updateResultsMeta(0, true);
        const grid = document.getElementById("workoutsGrid");
        grid.innerHTML = `<div class="col-12 text-center py-5 text-danger">
            <span class="material-symbols-outlined icon-lg">error</span>
            <p class="mt-2 mb-0">Could not load exercises right now. Please try again.</p>
        </div>`;
    }
}

async function fetchWorkoutDetail(exerciseId) {
    const res = await fetch(`/api/workouts/external/${encodeURIComponent(exerciseId)}`);
    if (!res.ok) throw new Error("Failed to load exercise details");
    return res.json();
}

function formatPills(items, variant = "text-bg-light") {
    if (!items || !items.length) {
        return '<span class="badge text-bg-light border">N/A</span>';
    }
    return items.map((item) => `<span class="badge ${variant} me-1 mb-1">${escapeHtml(item)}</span>`).join("");
}

function isMeaningfulTag(value) {
    if (!value) return false;
    return String(value).trim().toLowerCase() !== "unknown";
}

function renderCardTags(workout) {
    const tags = [];
    if (isMeaningfulTag(workout.muscle_group)) tags.push(`<span class="badge bg-primary">${escapeHtml(workout.muscle_group)}</span>`);
    if (isMeaningfulTag(workout.category)) tags.push(`<span class="badge bg-secondary">${escapeHtml(workout.category)}</span>`);
    if (!tags.length) return "";
    return `<div class="d-flex gap-1 mb-2">${tags.join("")}</div>`;
}

function accordionItem(id, title, bodyHtml, expanded = false) {
    return `
        <div class="accordion-item detail-accordion-item">
            <h2 class="accordion-header" id="heading-${id}">
                <button class="accordion-button ${expanded ? "" : "collapsed"}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-${id}" aria-expanded="${expanded ? "true" : "false"}" aria-controls="collapse-${id}">
                    ${escapeHtml(title)}
                </button>
            </h2>
            <div id="collapse-${id}" class="accordion-collapse collapse ${expanded ? "show" : ""}" aria-labelledby="heading-${id}">
                <div class="accordion-body">${bodyHtml}</div>
            </div>
        </div>
    `;
}

function toStringList(value) {
    if (!value) return [];
    if (Array.isArray(value)) return value.map((v) => String(v));
    if (typeof value === "string") return value.split(",").map((v) => v.trim()).filter(Boolean);
    return [];
}

function formatInstructionSteps(instructions) {
    if (!instructions.length) return '<p class="text-muted small mb-0">No instructions provided.</p>';
    return `
        <ol class="instruction-steps mb-0">
            ${instructions.map((step) => `<li class="instruction-step-item">${escapeHtml(step)}</li>`).join("")}
        </ol>
    `;
}

function formatTips(tips) {
    if (!tips.length) return '<p class="text-muted small mb-0">No tips available.</p>';
    return `
        <div class="tip-list">
            ${tips.map((tip) => `<div class="tip-item"><span class="tip-dot"></span><span>${escapeHtml(tip)}</span></div>`).join("")}
        </div>
    `;
}

function renderDetails(workout, detail) {
    const content = document.getElementById("exerciseDetailsContent");
    const instructions = toStringList(detail.instructions || detail.steps);
    const tips = toStringList(detail.exerciseTips).slice(0, 2);
    const equipments = toStringList(detail.equipments || detail.equipment);
    const videoUrl = detail.videoUrl || workout.video_url;
    const description = detail.overview || detail.description || workout.description || "";
    const detailId = String(workout.id || detail.exerciseId || detail.id || "exercise").replace(/[^a-zA-Z0-9_-]/g, "_");

    const sections = [
        accordionItem(`${detailId}-instructions`, "Instructions", formatInstructionSteps(instructions), true),
        accordionItem(`${detailId}-tips`, "Exercise Tips", formatTips(tips), true),
    ];

    content.innerHTML = `
        <div class="row g-4 details-layout">
            <div class="col-lg-6">
                <div class="details-media-card p-3 border rounded-4 bg-light-subtle">
                    <h6 class="fw-semibold mb-3">Demo</h6>
                    ${videoUrl ? `
                        <video class="w-100 rounded-3 border detail-video" controls autoplay muted playsinline preload="metadata" poster="${escapeHtml(workout.image_url || "")}">
                            <source src="${escapeHtml(videoUrl)}" type="video/mp4">
                        </video>
                    ` : `
                        <img class="img-fluid rounded-3 border" src="${escapeHtml(workout.image_url || "https://placehold.co/640x360?text=Exercise")}" alt="${escapeHtml(workout.name)} image">
                        <p class="text-muted small mt-2 mb-0">Video is not available for this exercise.</p>
                    `}
                    <div class="mt-3">
                        <h6 class="fw-semibold mb-2">Quick Facts</h6>
                        <div class="d-flex flex-wrap gap-2">
                            ${isMeaningfulTag(workout.muscle_group) ? `<span class="badge text-bg-primary">${escapeHtml(workout.muscle_group)}</span>` : ""}
                            ${isMeaningfulTag(workout.category) ? `<span class="badge text-bg-secondary">${escapeHtml(workout.category)}</span>` : ""}
                            ${detail.exerciseType ? `<span class="badge text-bg-info">${escapeHtml(detail.exerciseType)}</span>` : ""}
                            ${detail.difficultyLevel ? `<span class="badge text-bg-light border">${escapeHtml(detail.difficultyLevel)}</span>` : ""}
                        </div>
                    </div>
                    <div class="mt-3">
                        <h6 class="fw-semibold mb-2">Equipment</h6>
                        <div>${formatPills(equipments, "text-bg-dark")}</div>
                    </div>
                    <div class="mt-3 detail-overview-card p-3 rounded-3 border">
                        <h6 class="fw-semibold mb-2">Overview</h6>
                        <p class="text-muted mb-0">${escapeHtml(description)}</p>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="details-info-card p-3 border rounded-4">
                    <h4 class="mb-2">${escapeHtml(detail.name || workout.name)}</h4>
                    <div class="accordion detail-accordion" id="detailsAccordion-${detailId}">
                        ${sections.join("")}
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function openExerciseDetails(workout) {
    const content = document.getElementById("exerciseDetailsContent");
    const modalTitle = document.getElementById("exerciseDetailsModalLabel");
    modalTitle.textContent = workout.name;
    content.innerHTML = `<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>`;
    detailsModalInstance.show();

    if (!workout.id) {
        content.innerHTML = "<p class='text-danger mb-0'>Exercise ID is missing, so details cannot be loaded.</p>";
        return;
    }

    try {
        const detail = await fetchWorkoutDetail(workout.id);
        renderDetails(workout, detail);
    } catch (_) {
        content.innerHTML = "<p class='text-danger mb-0'>Could not load exercise details. Please try again.</p>";
    }
}

async function fetchRoutines() {
    const res = await fetch("/api/routines");
    const payload = await res.json();
    if (Array.isArray(payload)) return payload;
    if (payload && Array.isArray(payload.items)) return payload.items;
    return [];
}

function renderWorkouts(workouts) {
    const grid = document.getElementById("workoutsGrid");
    currentSearchResults = workouts;
    updateResultsMeta(workouts.length);
    if (!workouts.length) {
        grid.innerHTML = `<div class="col-12 text-center py-5 text-muted">
            <span class="material-symbols-outlined icon-lg">search_off</span>
            <p class="mt-2">No workouts found.</p>
        </div>`;
        return;
    }

    grid.innerHTML = workouts
        .map(
            (w, index) => `
        <div class="col-sm-6 col-md-4 col-lg-3">
            <div class="card h-100 shadow-sm workout-media-card" data-workout-index="${index}">
                <div class="workout-media-wrap">
                    <img class="workout-thumb workout-thumb-image" src="${escapeHtml(w.image_url || "https://placehold.co/640x360?text=Exercise")}" alt="${escapeHtml(w.name)} preview">
                </div>
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">${escapeHtml(w.name)}</h5>
                    <p class="card-text text-muted small flex-grow-1">${escapeHtml(w.description || "")}</p>
                    ${renderCardTags(w)}
                    <button class="btn btn-outline-primary btn-sm add-btn" data-workout-index="${index}">
                        <span class="material-symbols-outlined me-1 icon-inline-middle icon-sm">add</span>
                        Add to Routine
                    </button>
                </div>
            </div>
        </div>
    `,
        )
        .join("");

    document.querySelectorAll(".workout-media-card").forEach((card) => {
        card.addEventListener("click", () => {
            const workout = currentSearchResults[parseInt(card.dataset.workoutIndex, 10)];
            openExerciseDetails(workout);
        });
    });

    document.querySelectorAll(".add-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            const workout = currentSearchResults[parseInt(btn.dataset.workoutIndex, 10)];
            openAddToRoutineModal(workout);
        });
    });
}

let userRoutines = [];

async function openAddToRoutineModal(workout) {
    document.getElementById("selectedWorkoutPayload").value = JSON.stringify(workout);
    userRoutines = await fetchRoutines();

    const select = document.getElementById("routineSelect");
    const noMsg = document.getElementById("noRoutinesMsg");

    if (!userRoutines.length) {
        select.classList.add("d-none");
        noMsg.classList.remove("d-none");
    } else {
        noMsg.classList.add("d-none");
        select.classList.remove("d-none");
        select.innerHTML = userRoutines.map((r) => `<option value="${r.id}">${r.name}</option>`).join("");
    }

    addToRoutineModalInstance.show();
}

async function addToRoutine() {
    const workout = JSON.parse(document.getElementById("selectedWorkoutPayload").value);
    const routineId = parseInt(document.getElementById("routineSelect").value, 10);
    const sets = parseInt(document.getElementById("setsInput").value, 10) || 3;
    const reps = parseInt(document.getElementById("repsInput").value, 10) || 10;

    if (!routineId) return;

    const res = await fetch(`/api/routines/${routineId}/workouts/external`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            name: workout.name,
            description: workout.description || "",
            muscle_group: workout.muscle_group,
            category: workout.category || "strength",
            sets,
            reps,
        }),
    });

    if (res.ok) {
        addToRoutineModalInstance.hide();
        showToast("Success", "Exercise added to routine!", "success");
    } else {
        const err = await res.json();
        showToast("Error", err.detail || "Failed to add exercise", "danger");
    }
}

function showToast(title, message, type = "success") {
    document.getElementById("toastTitle").textContent = title;
    document.getElementById("toastContent").textContent = message;
    const toastEl = document.getElementById("appToast");
    toastEl.className = `toast text-bg-${type}`;
    new bootstrap.Toast(toastEl).show();
}

async function main() {
    detailsModalInstance = new bootstrap.Modal(document.getElementById("exerciseDetailsModal"));
    addToRoutineModalInstance = new bootstrap.Modal(document.getElementById("addToRoutineModal"));
    await runSearch();

    document.getElementById("searchBtn").addEventListener("click", async () => {
        await runSearch();
    });

    document.getElementById("searchInput").addEventListener("keypress", async (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            await runSearch();
        }
    });

    document.getElementById("muscleGroupFilter").addEventListener("change", runSearch);
    document.getElementById("categoryFilter").addEventListener("change", runSearch);
    document.getElementById("equipmentFilter").addEventListener("change", runSearch);
    document.getElementById("confirmAddBtn").addEventListener("click", addToRoutine);
}

main();
