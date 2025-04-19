// static/js/script.js
let cardData = [];
let currentIndex = 0;

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  fetchCSVData();
  initializeChat();
  initializeSectionToggles();
});

// Fetch CSV data from server
async function fetchCSVData() {
  try {
    const response = await fetch("/get_csv_data");
    if (!response.ok) throw new Error("Network response was not ok");

    cardData = await response.json();
    document.getElementById("loading").style.display = "none";
    document.getElementById("card-container").style.display = "block";

    if (cardData.length > 0) {
      showCard(0);
    } else {
      document.getElementById("card-container").innerHTML =
        "<p>No data found in the CSV file.</p>";
    }
  } catch (error) {
    console.error("Error fetching CSV data:", error);
    document.getElementById(
      "loading"
    ).innerHTML = `<p>Error loading data: ${error.message}</p>`;
  }
}

// Show specific card
function showCard(index) {
  if (index < 0 || index >= cardData.length) return;

  currentIndex = index;
  const item = cardData[index];

  // Update card UI
  document.getElementById("severity-badge").textContent =
    item.severity || "Unknown";
  document.getElementById(
    "severity-badge"
  ).className = `severity-badge severity-${(
    item.severity || "INFO"
  ).toUpperCase()}`;

  document.getElementById("component-value").textContent =
    item.component || "Not specified";
  document.getElementById("project-value").textContent =
    item.project || "Not specified";
  document.getElementById("line-value").textContent =
    item.line || "Not specified";
  document.getElementById("textRange-value").textContent = formatTextRange(
    item.textRange
  );
  document.getElementById("message-value").textContent =
    item.message || "No message provided";
  document.getElementById("effort-value").textContent =
    item.effort || "Not specified";

  document.getElementById("flows-value").innerHTML = formatFlowsData(
    item.flows
  );
  document.getElementById("tags-value").innerHTML = formatTagsData(item.tags);

  // Update navigation
  document.getElementById("card-footer").textContent = `Issue ${index + 1} of ${
    cardData.length
  }`;
  document.getElementById("prev-btn").disabled = index === 0;
  document.getElementById("next-btn").disabled = index === cardData.length - 1;
}

// Initialize chat functionality
function initializeChat() {
  const chatInput = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");

  sendBtn.addEventListener("click", sendMessage);
  chatInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") sendMessage();
  });
}

// Initialize section toggles
function initializeSectionToggles() {
  document.querySelectorAll(".section-title").forEach((title) => {
    const sectionId = title
      .getAttribute("onclick")
      .replace("toggleSection('", "")
      .replace("')", "");
    const section = document.getElementById(sectionId);
    const icon = document.getElementById(`${sectionId}-icon`);

    // Set initial state (collapsed)
    section.style.display = "block";
    icon.classList.remove("fa-chevron-down");
    icon.classList.add("fa-chevron-right");

    // Add click handler
    title.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent event bubbling
      toggleSection(sectionId);
    });
  });
}

// Toggle section visibility
function toggleSection(sectionId) {
  const section = document.getElementById(sectionId);
  const icon = document.getElementById(`${sectionId}-icon`);

  if (section.style.display === "none" || !section.style.display) {
    section.style.display = "block";
    icon.classList.remove("fa-chevron-right");
    icon.classList.add("fa-chevron-down");
  } else {
    section.style.display = "none";
    icon.classList.remove("fa-chevron-down");
    icon.classList.add("fa-chevron-right");
  }
}
// Send message to chatbot
async function sendMessage() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;

  // Add user message
  addMessageToChat(message, "user");
  input.value = "";

  // Show thinking indicator
  const thinkingIndicator = document.getElementById("thinking-indicator");
  thinkingIndicator.style.display = "block";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        csvData: cardData.length > 0 ? [cardData[currentIndex]] : [],
      }),
    });

    const data = await response.json();
    if (data.error) {
      addMessageToChat(`Error: ${data.error}`, "bot error");
    } else {
      addMessageToChat(data.response, "bot");
    }
  } catch (error) {
    console.error("Error:", error);
    addMessageToChat("Sorry, I encountered an error.", "bot error");
  } finally {
    thinkingIndicator.style.display = "none";
  }
}

// Add message to chat
function addMessageToChat(content, sender) {
  const chatMessages = document.getElementById("chat-messages");
  const messageDiv = document.createElement("div");
  messageDiv.className = `chat-message ${sender}`;

  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";
  contentDiv.innerHTML = content;

  messageDiv.appendChild(contentDiv);
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Helper functions
function formatTextRange(textRange) {
  if (!textRange || textRange === "[]") return "Not specified";
  try {
    const range = JSON.parse(textRange);
    return `Start Line: ${range.startLine}, End Line: ${range.endLine}`;
  } catch (e) {
    return textRange;
  }
}

function formatFlowsData(flows) {
  if (!flows || flows === "[]") return "No flows data";
  try {
    const flowsArray = JSON.parse(flows);
    return flowsArray
      .map(
        (flow) => `
      <div class="flow-item">
        <div class="flow-header">Flow</div>
        ${
          flow.locations
            ?.map(
              (loc) => `
          <div class="flow-location">
            <div>Component: ${loc.component || ""}</div>
            <div>Message: ${loc.msg || "No message"}</div>
          </div>
        `
            )
            .join("") || "<div>No locations</div>"
        }
      </div>
    `
      )
      .join("");
  } catch (e) {
    return `Error parsing flows: ${e.message}`;
  }
}

function formatTagsData(tags) {
  if (!tags || tags === "") return "No tags";
  return tags
    .split(",")
    .map((tag) => `<span class="tag">${tag.trim()}</span>`)
    .join(" ");
}
