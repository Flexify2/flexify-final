let currentAddSearchResults = [];

async function fetchAlternatives(workoutId) {
    const res = await fetch(`/api/workouts/${workoutId}/alternatives`);
    if (!res.ok) throw new Error("Failed to fetch alternatives");
    return res.json();
}

async function fetchExternalWorkouts(q = "", muscleGroup = "", category = "", difficulty = "") {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (muscleGroup) params.set("muscle_group", muscleGroup);
    if (category) params.set("category", category);
    if (difficulty) params.set("difficulty", difficulty);
    params.set("limit", "10");
    const res = await fetch(`/api/workouts/external/search?${params.toString()}`);
    if (!res.ok) return [];
    return res.json();
}

function showToast(title, message, type = "success") {
    document.getElementById("toastTitle").textContent = title;
    document.getElementById("toastContent").textContent = message;
    const toastEl = document.getElementById("appToast");
    toastEl.className = `toast text-bg-${type}`;
    new bootstrap.Toast(toastEl).show();
}

async function saveRoutineWorkout(rwId, sets, reps) {
    const res = await fetch(`/api/routines/${ROUTINE_ID}/workouts/${rwId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sets, reps }),
    });
    if (!res.ok) throw new Error("Failed to update");
    return res.json();
}

async function removeFromRoutine(rwId) {
    const res = await fetch(`/api/routines/${ROUTINE_ID}/workouts/${rwId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to remove");
}

async function addWorkoutToRoutine(workoutId, sets, reps) {
    const res = await fetch(`/api/routines/${ROUTINE_ID}/workouts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workout_id: workoutId, sets, reps }),
    });
    if (!res.ok) throw new Error("Failed to add");
    return res.json();
}

async function addExternalWorkoutToRoutine(workout, sets, reps) {
    const res = await fetch(`/api/routines/${ROUTINE_ID}/workouts/external`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            name: workout.name,
            description: workout.description || "",
            muscle_group: workout.muscle_group,
            category: workout.category || "Strength",
            sets,
            reps,
        }),
    });
    if (!res.ok) throw new Error("Failed to add external exercise");
    return res.json();
}

async function swapWorkout(rwId, newWorkoutId, sets, reps) {
    await removeFromRoutine(rwId);
    return addWorkoutToRoutine(newWorkoutId, sets, reps);
}

async function renameRoutine(name) {
    const res = await fetch(`/api/routines/${ROUTINE_ID}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error("Failed to rename");
    return res.json();
}

function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function cleanWorkoutDescription(description) {
    const text = String(description || "").trim();
    if (!text) return "";
    if (/^Imported from/i.test(text)) return "";
    return text;
}

function updateCount() {
    const cards = document.querySelectorAll(".routine-workout-card");
    const count = cards.length;
    const label = document.getElementById("routineCountText");
    if (!label) return;
    label.textContent = `${count} exercise${count !== 1 ? "s" : ""} ready to train.`;
}

function buildWorkoutCard(w) {
    const description = cleanWorkoutDescription(w.description);
    const card = document.createElement("div");
    card.className = "card mb-3 shadow-sm routine-workout-card";
    card.dataset.rwId = w.routine_workout_id;
    card.dataset.workoutId = w.id;
    card.innerHTML = `
        <div class="card-body">
            <div class="row g-3 align-items-start">
                <div class="col-12 col-md-3 col-lg-2">
                    <div class="routine-image-wrap rounded-4 border overflow-hidden">
                        <img src="${escapeHtml(w.image_url || "https://placehold.co/320x240?text=Exercise")}" alt="${escapeHtml(w.name)}" class="routine-image">
                    </div>
                </div>
                <div class="col-12 col-md-9 col-lg-10">
                    <div class="d-flex align-items-center gap-2 flex-wrap mb-2">
                        <h5 class="card-title mb-0">${escapeHtml(w.name)}</h5>
                        <span class="badge bg-primary">${escapeHtml(w.muscle_group)}</span>
                        <span class="badge bg-secondary">${escapeHtml(w.category)}</span>
                    </div>
                    ${description ? `<p class="card-text text-muted small mb-3">${escapeHtml(description)}</p>` : ""}
                    <div class="d-flex align-items-center gap-3 flex-wrap">
                        <div class="d-flex align-items-center gap-1">
                            <label class="form-label mb-0 small fw-semibold">Sets:</label>
                            <input type="number" class="form-control form-control-sm sets-input input-fixed-65" value="${w.sets}" min="1">
                        </div>
                        <div class="d-flex align-items-center gap-1">
                            <label class="form-label mb-0 small fw-semibold">Reps:</label>
                            <input type="number" class="form-control form-control-sm reps-input input-fixed-65" value="${w.reps}" min="1">
                        </div>
                        <button class="btn btn-sm btn-outline-primary save-btn">Save</button>
                    </div>
                </div>
                <div class="col-12 col-lg-auto ms-lg-auto d-flex flex-row flex-lg-column gap-2 justify-content-start justify-content-lg-end">
                    <button class="btn btn-sm btn-outline-warning remix-btn" title="Find alternatives">
                        <span class="material-symbols-outlined icon-sm">shuffle</span>
                        Remix
                    </button>
                    <button class="btn btn-sm btn-outline-danger remove-btn" title="Remove from routine">
                        <span class="material-symbols-outlined icon-sm">delete</span>
                    </button>
                </div>
            </div>
        </div>
    `;
    attachCardListeners(card);
    return card;
}

function attachCardListeners(card) {
    const rwId = card.dataset.rwId;
    const workoutId = card.dataset.workoutId;

    card.querySelector(".save-btn").addEventListener("click", async () => {
        const sets = parseInt(card.querySelector(".sets-input").value, 10);
        const reps = parseInt(card.querySelector(".reps-input").value, 10);
        try {
            await saveRoutineWorkout(rwId, sets, reps);
            showToast("Saved", "Exercise updated!");
        } catch {
            showToast("Error", "Could not save changes", "danger");
        }
    });

    card.querySelector(".remove-btn").addEventListener("click", async () => {
        try {
            await removeFromRoutine(rwId);
            card.remove();
            updateCount();
            showToast("Removed", "Exercise removed from routine");
        } catch {
            showToast("Error", "Could not remove exercise", "danger");
        }
    });

    card.querySelector(".remix-btn").addEventListener("click", async () => {
        const workoutName = card.querySelector(".card-title").textContent;
        document.getElementById("remixWorkoutName").textContent = workoutName;
        document.getElementById("remixRwId").value = rwId;
        document.getElementById("remixWorkoutId").value = workoutId;

        const remixList = document.getElementById("remixList");
        remixList.innerHTML = `<div class="text-center py-3"><div class="spinner-border spinner-border-sm text-primary"></div></div>`;
        new bootstrap.Modal(document.getElementById("remixModal")).show();

        try {
            const alternatives = await fetchAlternatives(workoutId);
            if (!alternatives.length) {
                remixList.innerHTML = `<p class="text-muted text-center">No alternatives found for this muscle group.</p>`;
                return;
            }

            remixList.innerHTML = alternatives
                .map(
                    (a) => `
                <div class="d-flex align-items-center justify-content-between border rounded p-2 mb-2">
                    <div>
                        <strong>${escapeHtml(a.name)}</strong>
                        <p class="mb-0 small text-muted">${escapeHtml(a.description || "")}</p>
                    </div>
                    <button class="btn btn-sm btn-primary swap-btn" data-new-workout-id="${a.id}">
                        Swap
                    </button>
                </div>
            `,
                )
                .join("");

            remixList.querySelectorAll(".swap-btn").forEach((btn) => {
                btn.addEventListener("click", async () => {
                    const newWorkoutId = parseInt(btn.dataset.newWorkoutId, 10);
                    const sets = parseInt(card.querySelector(".sets-input").value, 10);
                    const reps = parseInt(card.querySelector(".reps-input").value, 10);
                    try {
                        const newRw = await swapWorkout(rwId, newWorkoutId, sets, reps);
                        bootstrap.Modal.getInstance(document.getElementById("remixModal")).hide();
                        const newCard = buildWorkoutCard(newRw);
                        card.replaceWith(newCard);
                        updateCount();
                        showToast("Remixed!", `Swapped to ${newRw.name}`);
                    } catch {
                        showToast("Error", "Could not swap exercise", "danger");
                    }
                });
            });
        } catch {
            remixList.innerHTML = `<p class="text-danger text-center">Failed to load alternatives.</p>`;
        }
    });
}

async function loadAddWorkoutList(q = "", mg = "", cat = "", difficulty = "") {
    const list = document.getElementById("addWorkoutList");
    list.innerHTML = `<div class="text-center py-3"><div class="spinner-border spinner-border-sm text-primary"></div></div>`;
    const externalWorkouts = await fetchExternalWorkouts(q, mg, cat, difficulty);
    currentAddSearchResults = externalWorkouts.map((w) => ({ ...w, source: "external" }));

    if (!currentAddSearchResults.length) {
        list.innerHTML = `<p class="text-muted text-center py-3">No workouts found.</p>`;
        return;
    }

    list.innerHTML = currentAddSearchResults
        .map(
            (w, index) => `
        <div class="d-flex align-items-center justify-content-between border rounded p-2 mb-2">
            <div class="d-flex align-items-start gap-2">
                <img src="${escapeHtml(w.image_url || "https://placehold.co/96x96?text=EX")}" alt="${escapeHtml(w.name)}" class="rounded thumb-56">
                <div>
                    <strong>${escapeHtml(w.name)}</strong>
                    <span class="badge bg-primary ms-1">${escapeHtml(w.muscle_group)}</span>
                    ${cleanWorkoutDescription(w.description) ? `<p class="mb-0 small text-muted">${escapeHtml(cleanWorkoutDescription(w.description))}</p>` : ""}
                    ${w.video_url ? `<a href="${escapeHtml(w.video_url)}" target="_blank" rel="noopener noreferrer" class="small">Watch demo</a>` : ""}
                </div>
            </div>
            <button class="btn btn-sm btn-primary pick-workout-btn" data-item-index="${index}">Add</button>
        </div>
    `,
        )
        .join("");

    list.querySelectorAll(".pick-workout-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const item = currentAddSearchResults[parseInt(btn.dataset.itemIndex, 10)];
            const sets = parseInt(document.getElementById("addSetsInput").value, 10) || 3;
            const reps = parseInt(document.getElementById("addRepsInput").value, 10) || 10;
            try {
                const newRw = await addExternalWorkoutToRoutine(item, sets, reps);
                bootstrap.Modal.getInstance(document.getElementById("addWorkoutModal")).hide();
                const workoutList = document.getElementById("workoutList");
                const emptyState = document.getElementById("emptyState");
                if (emptyState) emptyState.remove();
                workoutList.appendChild(buildWorkoutCard(newRw));
                updateCount();
                showToast("Added", `${newRw.name} added to routine!`);
            } catch {
                showToast("Error", "Could not add exercise", "danger");
            }
        });
    });
}

function main() {
    document.querySelectorAll(".routine-workout-card").forEach(attachCardListeners);

    document.getElementById("saveRoutineNameBtn").addEventListener("click", async () => {
        const name = document.getElementById("editRoutineName").value.trim();
        if (!name) return;
        try {
            await renameRoutine(name);
            document.getElementById("routineTitle").textContent = name;
            bootstrap.Modal.getInstance(document.getElementById("editRoutineModal")).hide();
            showToast("Saved", "Routine renamed!");
        } catch {
            showToast("Error", "Could not rename routine", "danger");
        }
    });

    document.getElementById("addWorkoutModal").addEventListener("show.bs.modal", () => {
        loadAddWorkoutList();
    });

    document.getElementById("addSearchBtn").addEventListener("click", () => {
        loadAddWorkoutList(
            document.getElementById("addSearchInput").value,
            document.getElementById("addMuscleGroupFilter").value,
            document.getElementById("addCategoryFilter").value,
            document.getElementById("addDifficultyFilter").value,
        );
    });

    document.getElementById("addSearchInput").addEventListener("keypress", (e) => {
        if (e.key === "Enter") document.getElementById("addSearchBtn").click();
    });
}

main();
