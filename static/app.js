async function loadHealth() {
    const response = await fetch("/health");
    const data = await response.json();

    document.getElementById("status").textContent =
        data.status.toUpperCase();
}


async function loadJobs() {
    const response = await fetch("/jobs?limit=10");
    const data = await response.json();

    document.getElementById("job-count").textContent =
        data.count;

    const container = document.getElementById("jobs");

    container.innerHTML = "";

    data.jobs.forEach(job => {

        const element = document.createElement("div");

        element.className = "job";

        element.innerHTML = `
            <h3>${escapeHtml(job.title)}</h3>

            <p>
                ${escapeHtml(job.company || "Unknown company")}
                ·
                ${escapeHtml(job.location || "Location not specified")}
            </p>

            <p>Source: ${escapeHtml(job.source)}</p>

            <a href="${job.url}" target="_blank">
                View original listing →
            </a>
        `;

        container.appendChild(element);
    });
}


async function runIngestion() {

    const button = document.getElementById("ingest-button");

    button.disabled = true;
    button.textContent = "Running...";

    document.getElementById("result").textContent =
        "Fetching and processing jobs...";

    try {

        const response = await fetch("/ingest", {
            method: "POST"
        });

        const data = await response.json();

        document.getElementById("result").textContent =
            `${data.status} · ${data.source} · ` +
            `${data.fetched} fetched · ` +
            `${data.inserted} inserted · ` +
            `${data.skipped} skipped`;

        await loadJobs();

    } catch (error) {

        document.getElementById("result").textContent =
            "Ingestion failed: " + error.message;

    } finally {

        button.disabled = false;
        button.textContent = "Run Ingestion";
    }
}


function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


document
    .getElementById("ingest-button")
    .addEventListener("click", runIngestion);


loadHealth();
loadJobs();