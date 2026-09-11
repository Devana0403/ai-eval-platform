// const API_BASE = "http://localhost:8000";
const API_BASE = "https://ai-eval-platform-api.azurewebsites.net"; // live backend instead of localhost for testing
let tasksVisible = true;

function switchMode() {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    document.getElementById("mode-raw").style.display = mode === "raw" ? "block" : "none";
    document.getElementById("mode-examples").style.display = mode === "examples" ? "block" : "none";
    document.getElementById("mode-auto").style.display = mode === "auto" ? "block" : "none";
}
  
function parseExamplesText(text) {
    // Parses lines like "2, 3 -> 5" into {inputs: [2, 3], expected_output: 5}
    return text.split("\n").filter(line => line.trim()).map(line => {
      const [inputsPart, outputPart] = line.split("->").map(s => s.trim());
      const inputs = inputsPart.split(",").map(s => parseValue(s.trim()));
      const expected_output = parseValue(outputPart.trim());
      return { inputs, expected_output };
    });
}
  
function parseValue(str) {
    // Tries to interpret numbers correctly; falls back to plain text otherwise
    if (!isNaN(str) && str !== "") return Number(str);
    if (str === "true") return true;
    if (str === "false") return false;
    return str.replace(/^['"]|['"]$/g, "");  // strips surrounding quotes if user added them
}
  
async function createTask() {
    const description = document.getElementById("description").value;
    const function_name = document.getElementById("function_name").value;
    const mode = document.querySelector('input[name="mode"]:checked').value;
  
    if (!function_name) {
      alert("Function name is required");
      return;
    }
  
    const body = { description, function_name, test_code: null, examples: null, auto_generate_tests: false };
  
    if (mode === "raw") {
      body.test_code = document.getElementById("test_code").value;
    } else if (mode === "examples") {
      body.examples = parseExamplesText(document.getElementById("examples_text").value);
    } else if (mode === "auto") {
      body.auto_generate_tests = true;
    }
  
    const response = await fetch(`${API_BASE}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
  
    if (!response.ok) {
      const err = await response.json();
      alert("Failed to create task: " + JSON.stringify(err.detail));
      return;
    }
  
    document.getElementById("description").value = "";
    document.getElementById("function_name").value = "";
    document.getElementById("test_code").value = "";
    document.getElementById("examples_text").value = "";
    loadTasks();
}

function toggleTasksVisibility() {
  tasksVisible = !tasksVisible;
  document.getElementById("tasks-list").style.display = tasksVisible ? "block" : "none";
  document.getElementById("toggle-btn").textContent = tasksVisible ? "Hide Tasks" : "Show Tasks";
}

async function findTaskById() {
  const id = document.getElementById("search-id").value;
  if (!id) {
    loadTasks();  // empty search = show everything again
    return;
  }
  await loadTasks(parseInt(id));
}

async function searchTasksByText() {
    const query = document.getElementById("search-text").value.trim();
    if (!query) {
      loadTasks();
      return;
    }
    const response = await fetch(`${API_BASE}/tasks/search?q=${encodeURIComponent(query)}`);
    const tasks = await response.json();
    renderTasks(tasks);
  }
  
  async function loadTasks() {
    const response = await fetch(`${API_BASE}/tasks`);
    const tasks = await response.json();
    renderTasks(tasks);
  }
  
  function renderTasks(tasks) {
    const container = document.getElementById("tasks-list");
    container.innerHTML = "";
  
    if (tasks.length === 0) {
      container.innerHTML = "<p>No matching tasks found.</p>";
      return;
    }
  
    tasks.forEach(task => {
      const card = document.createElement("div");
      card.className = "task-card";
      card.innerHTML = `
        <strong>Task #${task.id}</strong>: ${task.description}
        <br>
        <button onclick="generateSolution(${task.id})">Generate Solution</button>
        <div id="task-${task.id}-output"></div>
      `;
      container.appendChild(card);
    });
  }

async function generateSolution(taskId) {
  const outputDiv = document.getElementById(`task-${taskId}-output`);
  outputDiv.innerHTML = "Generating...";

  const response = await fetch(`${API_BASE}/tasks/${taskId}/generate`, { method: "POST" });
  const solution = await response.json();

  outputDiv.innerHTML = `
    <pre>${solution.generated_code}</pre>
    <button onclick="evaluateSolution(${solution.id}, ${taskId})">Evaluate</button>
    <div id="solution-${solution.id}-result"></div>
  `;
}

async function evaluateSolution(solutionId, taskId) {
  const resultDiv = document.getElementById(`solution-${solutionId}-result`);
  resultDiv.innerHTML = "Evaluating...";

  const response = await fetch(`${API_BASE}/solutions/${solutionId}/evaluate?expected_task_id=${taskId}`, {
    method: "POST"
  });
  const evaluation = await response.json();

  const statusClass = evaluation.passed ? "pass" : "fail";
  const statusText = evaluation.passed ? "PASSED" : `FAILED (${evaluation.failure_type})`;

  // Show stderr on failure so we can actually see what went wrong
  const detailsHtml = evaluation.passed
    ? ""
    : `<details><summary>See error details</summary><pre>${escapeHtml(evaluation.stderr)}</pre></details>`;

  resultDiv.innerHTML = `<span class="${statusClass}">${statusText}</span>${detailsHtml}`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

loadTasks();