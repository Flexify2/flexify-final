let remixModal = null;
let detailsModal = null;
let currentAlternatives = [];
let remixState = {
    routineWorkoutId: null,
    sets: 3,
    reps: 10,
};

function escapeHtml(text) {
    return String(text || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function showToast(title, message, type = "success") {
    const titleEl = document.getElementById("toastTitle");
    const contentEl = document.getElementById("toastContent");
    const toastEl = document.getElementById("appToast");
    if (!titleEl || !contentEl || !toastEl) {
        return;
    }
    titleEl.textContent = title;
    contentEl.textContent = message;
    toastEl.className = `toast text-bg-${type}`;
    new bootstrap.Toast(toastEl).show();
}

async function fetchAlternatives(workoutId) {
    const res = await fetch(`/api/workouts/${workoutId}/alternatives`);
    if (!res.ok) {
        throw new Error("Could not fetch alternatives");
    }
    return res.json();
}

async function fetchExternalWorkoutMatch(workout) {
    const params = new URLSearchParams();
    params.set("q", workout.name || "");
    if (workout.muscle_group) {
        params.set("muscle_group", workout.muscle_group);
    }
    if (workout.category) {
        params.set("category", workout.category);
    }
    params.set("limit", "3");

    const res = await fetch(`/api/workouts/external/search?${params.toString()}`);
    if (!res.ok) {
        return null;
    }

    const items = await res.json();
    if (!Array.isArray(items) || !items.length) {
        return null;
    }

    const targetName = String(workout.name || "").trim().toLowerCase();
    const exact = items.find((item) => String(item.name || "").trim().toLowerCase() === targetName);
    return exact || items[0];
}

async function fetchExternalWorkoutDetail(exerciseId) {
    const res = await fetch(`/api/workouts/external/${encodeURIComponent(exerciseId)}`);
    if (!res.ok) {
        return null;
    }
    return res.json();
}

async function swapWorkout(newWorkoutId) {
    const removeRes = await fetch(`/api/routines/${ROUTINE_ID}/workouts/${remixState.routineWorkoutId}`, {
        method: "DELETE",
    });
    if (!removeRes.ok) {
        throw new Error("Could not remove existing workout");
    }

    const addRes = await fetch(`/api/routines/${ROUTINE_ID}/workouts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            workout_id: newWorkoutId,
            sets: remixState.sets,
            reps: remixState.reps,
        }),
    });
    if (!addRes.ok) {
        throw new Error("Could not add replacement workout");
    }
}

function toStringList(value) {
    if (!value) return [];
    if (Array.isArray(value)) return value.map((item) => String(item));
    if (typeof value === "string") {
        return value.split(",").map((item) => item.trim()).filter(Boolean);
    }
    return [];
}

function renderAlternativeFallbackDetails(workout) {
    const container = document.getElementById("alternativeDetailsContent");
    if (!container) {
        return;
    }

    container.innerHTML = `
        <div class="row g-4">
            <div class="col-lg-6">
                <img class="img-fluid rounded-3 border" src="https://placehold.co/640x360?text=Exercise" alt="${escapeHtml(workout.name)} preview">
            </div>
            <div class="col-lg-6">
                <h4 class="mb-2">${escapeHtml(workout.name)}</h4>
                <div class="d-flex flex-wrap gap-2 mb-3">
                    ${workout.muscle_group ? `<span class="badge text-bg-primary">${escapeHtml(workout.muscle_group)}</span>` : ""}
                    ${workout.category ? `<span class="badge text-bg-secondary">${escapeHtml(workout.category)}</span>` : ""}
                </div>
                <p class="text-muted mb-0">${escapeHtml(workout.description || "No additional details are available for this exercise yet.")}</p>
            </div>
        </div>
    `;
}

function renderAlternativeDetails(workout, detail, imageUrl, videoUrl) {
    const container = document.getElementById("alternativeDetailsContent");
    if (!container) {
        return;
    }

    const instructions = toStringList(detail.instructions || detail.steps);
    const tips = toStringList(detail.exerciseTips).slice(0, 3);
    const equipments = toStringList(detail.equipments || detail.equipment);
    const mediaImage = imageUrl || "https://placehold.co/640x360?text=Exercise";

    container.innerHTML = `
        <div class="row g-4">
            <div class="col-lg-6">
                ${videoUrl ? `
                    <video class="w-100 rounded-3 border" controls autoplay muted playsinline preload="metadata" poster="${escapeHtml(mediaImage)}">
                        <source src="${escapeHtml(videoUrl)}" type="video/mp4">
                    </video>
                ` : `
                    <img class="img-fluid rounded-3 border" src="${escapeHtml(mediaImage)}" alt="${escapeHtml(workout.name)} preview">
                `}
                <div class="d-flex flex-wrap gap-2 mt-3">
                    ${workout.muscle_group ? `<span class="badge text-bg-primary">${escapeHtml(workout.muscle_group)}</span>` : ""}
                    ${workout.category ? `<span class="badge text-bg-secondary">${escapeHtml(workout.category)}</span>` : ""}
                    ${detail.difficultyLevel ? `<span class="badge text-bg-light border">${escapeHtml(detail.difficultyLevel)}</span>` : ""}
                </div>
                <div class="mt-3">
                    <h6 class="fw-semibold mb-2">Equipment</h6>
                    <p class="text-muted mb-0">${equipments.length ? escapeHtml(equipments.join(", ")) : "Not specified"}</p>
                </div>
            </div>
            <div class="col-lg-6">
                <h4 class="mb-2">${escapeHtml(detail.name || workout.name)}</h4>
                <p class="text-muted">${escapeHtml(detail.overview || detail.description || workout.description || "No overview available.")}</p>
                <h6 class="fw-semibold mt-3 mb-2">Instructions</h6>
                ${instructions.length ? `<ol class="mb-0">${instructions.map((step) => `<li class="mb-1">${escapeHtml(step)}</li>`).join("")}</ol>` : '<p class="text-muted mb-0">No instructions provided.</p>'}
                <h6 class="fw-semibold mt-3 mb-2">Tips</h6>
                ${tips.length ? `<ul class="mb-0">${tips.map((tip) => `<li class="mb-1">${escapeHtml(tip)}</li>`).join("")}</ul>` : '<p class="text-muted mb-0">No tips available.</p>'}
            </div>
        </div>
    `;
}

async function openAlternativeDetails(alternative) {
    const titleEl = document.getElementById("alternativeDetailsModalLabel");
    const contentEl = document.getElementById("alternativeDetailsContent");
    if (!contentEl || !detailsModal) {
        return;
    }

    if (titleEl) {
        titleEl.textContent = alternative.name || "Exercise Details";
    }

    contentEl.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></div>';
    detailsModal.show();

    try {
        const match = await fetchExternalWorkoutMatch(alternative);
        if (!match || !match.id) {
            renderAlternativeFallbackDetails(alternative);
            return;
        }

        const detail = await fetchExternalWorkoutDetail(match.id);
        if (!detail) {
            renderAlternativeFallbackDetails(alternative);
            return;
        }

        renderAlternativeDetails(alternative, detail, match.image_url, detail.videoUrl || match.video_url);
    } catch (_) {
        renderAlternativeFallbackDetails(alternative);
    }
}

function renderAlternatives(alternatives) {
    const remixList = document.getElementById("remixList");
    if (!remixList) {
        return;
    }

    if (!alternatives.length) {
        remixList.innerHTML = '<p class="text-muted text-center mb-0">No alternatives found right now.</p>';
        return;
    }

    currentAlternatives = alternatives;

    remixList.innerHTML = alternatives
        .map(
            (item, index) => `
            <div class="border rounded p-2 d-flex align-items-center justify-content-between gap-2">
                <div>
                    <div class="fw-semibold">${escapeHtml(item.name)}</div>
                    <div class="small text-muted">${escapeHtml(item.muscle_group || "")}${item.category ? ` • ${escapeHtml(item.category)}` : ""}</div>
                </div>
                <div class="d-flex align-items-center gap-2">
                    <button type="button" class="btn btn-sm btn-outline-secondary remix-details-btn" data-item-index="${index}">
                        Details
                    </button>
                    <button type="button" class="btn btn-sm btn-primary remix-swap-btn" data-new-workout-id="${item.id}">
                        Swap
                    </button>
                </div>
            </div>
        `,
        )
        .join("");

    remixList.querySelectorAll(".remix-details-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const itemIndex = parseInt(btn.dataset.itemIndex, 10);
            const selected = currentAlternatives[itemIndex];
            if (!selected) {
                return;
            }
            openAlternativeDetails(selected);
        });
    });

    remixList.querySelectorAll(".remix-swap-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const newWorkoutId = parseInt(btn.dataset.newWorkoutId, 10);
            if (!newWorkoutId) {
                return;
            }

            btn.disabled = true;
            btn.textContent = "Swapping...";
            try {
                await swapWorkout(newWorkoutId);
                showToast("Remixed", "Exercise swapped successfully.");
                if (remixModal) {
                    remixModal.hide();
                }
                window.location.reload();
            } catch (_) {
                btn.disabled = false;
                btn.textContent = "Swap";
                showToast("Error", "Could not swap exercise. Please try again.", "danger");
            }
        });
    });
}

async function openRemix(button) {
    const rwId = parseInt(button.dataset.rwId, 10);
    const workoutId = parseInt(button.dataset.workoutId, 10);
    const workoutName = button.dataset.workoutName || "this exercise";
    const sets = parseInt(button.dataset.sets, 10) || 3;
    const reps = parseInt(button.dataset.reps, 10) || 10;

    remixState = {
        routineWorkoutId: rwId,
        sets,
        reps,
    };

    const remixName = document.getElementById("remixWorkoutName");
    const remixList = document.getElementById("remixList");
    if (remixName) {
        remixName.textContent = workoutName;
    }
    if (remixList) {
        remixList.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm text-primary" role="status"></div></div>';
    }

    remixModal.show();

    try {
        const alternatives = await fetchAlternatives(workoutId);
        renderAlternatives(alternatives.filter((item) => item.id !== workoutId));
    } catch (_) {
        if (remixList) {
            remixList.innerHTML = '<p class="text-danger text-center mb-0">Failed to load alternatives.</p>';
        }
    }
}

async function updateWorkoutOrder(routineWorkoutId, newOrder) {
    const res = await fetch(`/api/routines/${ROUTINE_ID}/workouts/${routineWorkoutId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order: newOrder }),
    });

    if (!res.ok) {
        throw new Error("Could not update workout order");
    }

    return res.json();
}

let draggedCard = null;

function initDragAndDrop() {
    const list = document.getElementById("routine-exercises-list");
    if (!list) return;

    const cards = list.querySelectorAll(".routine-exercise-card");

    cards.forEach((card) => {
        card.addEventListener("dragstart", (e) => {
            draggedCard = card;
            card.classList.add("dragging");
            e.dataTransfer.effectAllowed = "move";
        });

        card.addEventListener("dragend", () => {
            draggedCard?.classList.remove("dragging");
            cards.forEach((c) => c.classList.remove("drag-over-before", "drag-over-after"));
            draggedCard = null;
        });

        card.addEventListener("dragover", (e) => {
            if (!draggedCard || draggedCard === card) return;
            e.preventDefault();
            e.dataTransfer.dropEffect = "move";

            const allCards = Array.from(list.children);
            const draggedIndex = allCards.indexOf(draggedCard);
            const targetIndex = allCards.indexOf(card);

            card.classList.remove("drag-over-before", "drag-over-after");
            card.classList.add(draggedIndex < targetIndex ? "drag-over-after" : "drag-over-before");
        });

        card.addEventListener("dragleave", () => {
            card.classList.remove("drag-over-before", "drag-over-after");
        });

        card.addEventListener("drop", async (e) => {
            e.preventDefault();
            cards.forEach((c) => c.classList.remove("drag-over-before", "drag-over-after"));

            if (!draggedCard || draggedCard === card) return;

            const allCards = Array.from(list.children);
            const draggedIndex = allCards.indexOf(draggedCard);
            const targetIndex = allCards.indexOf(card);

            if (draggedIndex < targetIndex) {
                card.parentNode.insertBefore(draggedCard, card.nextSibling);
            } else {
                card.parentNode.insertBefore(draggedCard, card);
            }

            const updatedCards = Array.from(list.children);
            try {
                for (let i = 0; i < updatedCards.length; i++) {
                    const rwId = parseInt(updatedCards[i].dataset.rwId, 10);
                    if (rwId) {
                        await updateWorkoutOrder(rwId, i);
                        updatedCards[i].dataset.order = String(i);
                    }
                }
            } catch (_) {
                showToast("Error", "Could not reorder exercises. Please try again.", "danger");
                window.location.reload();
            }
        });
    });
}

function main() {
    const remixModalEl = document.getElementById("remixModal");
    const detailsModalEl = document.getElementById("alternativeDetailsModal");
    if (!remixModalEl || !detailsModalEl) {
        return;
    }

    remixModal = new bootstrap.Modal(remixModalEl);
    detailsModal = new bootstrap.Modal(detailsModalEl);

    document.querySelectorAll(".remix-btn").forEach((btn) => {
        btn.addEventListener("click", () => openRemix(btn));
    });

    initDragAndDrop();
}

main();
