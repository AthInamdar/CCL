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

  // Display all fields from the CSV
  // Key Information
  document.getElementById("key-value").textContent = item.key || "Not specified";
  document.getElementById("rule-value").textContent = item.rule || "Not specified";
  document.getElementById("type-value").textContent = item.type || "Not specified";
  document.getElementById("status-value").textContent = item.status || "Not specified";
  document.getElementById("issueStatus-value").textContent = item.issueStatus || "Not specified";
  
  // Location fields
  document.getElementById("component-value").textContent = item.component || "Not specified";
  document.getElementById("project-value").textContent = item.project || "Not specified";
  document.getElementById("projectName-value").textContent = item.projectName || "Not specified";
  document.getElementById("organization-value").textContent = item.organization || "Not specified";
  document.getElementById("line-value").textContent = item.line || "Not specified";
  document.getElementById("hash-value").textContent = item.hash || "Not specified";
  document.getElementById("textRange-value").textContent = formatTextRange(item.textRange);
  
  // Message
  document.getElementById("message-value").textContent = item.message || "No message provided";
  
  // Flows
  document.getElementById("flows-value").innerHTML = formatFlowsData(item.flows);
  
  // Clean Code Information
  document.getElementById("cleanCodeAttribute-value").textContent = item.cleanCodeAttribute || "Not specified";
  document.getElementById("cleanCodeAttributeCategory-value").textContent = item.cleanCodeAttributeCategory || "Not specified";
  document.getElementById("impacts-value").innerHTML = formatImpacts(item.impacts);
  
  // Technical Details
  document.getElementById("effort-value").textContent = item.effort || "Not specified";
  document.getElementById("debt-value").textContent = item.debt || "Not specified";
  document.getElementById("author-value").textContent = item.author || "Not specified";
  document.getElementById("creationDate-value").textContent = formatDate(item.creationDate);
  document.getElementById("updateDate-value").textContent = formatDate(item.updateDate);
  
  // Tags
  document.getElementById("tags-value").innerHTML = formatTagsData(item.tags);

  // Severity badge
  document.getElementById("severity-badge").textContent = item.severity || "Unknown";
  document.getElementById("severity-badge").className = `severity-badge severity-${(item.severity || "INFO").toUpperCase()}`;

  // Update navigation
  document.getElementById("card-footer").textContent = `Issue ${index + 1} of ${cardData.length}`;
  document.getElementById("prev-btn").disabled = index === 0;
  document.getElementById("next-btn").disabled = index === cardData.length - 1;
}

// Format date in a more readable way
function formatDate(dateString) {
  if (!dateString) return "Not specified";
  
  try {
    const date = new Date(dateString);
    return date.toLocaleString();
  } catch (e) {
    return dateString;
  }
}

// Format impacts data
function formatImpacts(impacts) {
  if (!impacts || impacts === "[]") return "No impacts data";
  
  try {
    const impactsArray = JSON.parse(impacts);
    return impactsArray.map(impact => `
      <div class="impact-item">
        <span class="impact-quality">${impact.softwareQuality || ""}</span>:
        <span class="impact-severity">${impact.severity || ""}</span>
      </div>
    `).join("");
  } catch (e) {
    return impacts;
  }
}

// Format text range
function formatTextRange(textRange) {
  if (!textRange || textRange === "[]") return "Not specified";
  try {
    const range = JSON.parse(textRange);
    return `Start Line: ${range.startLine}, End Line: ${range.endLine}, Start Offset: ${range.startOffset}, End Offset: ${range.endOffset}`;
  } catch (e) {
    return textRange;
  }
}

// Format flows data
function formatFlowsData(flows) {
  if (!flows || flows === "[]") return "No flows data";
  try {
    const flowsArray = JSON.parse(flows);
    return flowsArray.map((flow, flowIndex) => `
      <div class="flow-item">
        <div class="flow-header">Flow #${flowIndex + 1}</div>
        ${flow.locations?.map((loc, locIndex) => `
          <div class="flow-location">
            <div class="flow-location-header">Location #${locIndex + 1}</div>
            <div><strong>Component:</strong> ${loc.component || ""}</div>
            <div><strong>Message:</strong> ${loc.msg || "No message"}</div>
            ${loc.textRange ? `
              <div><strong>Text Range:</strong> 
                Line ${loc.textRange.startLine}-${loc.textRange.endLine}, 
                Offset ${loc.textRange.startOffset}-${loc.textRange.endOffset}
              </div>` : ''}
          </div>
        `).join("") || "<div>No locations</div>"}
      </div>
    `).join("");
  } catch (e) {
    return `Error parsing flows: ${e.message}`;
  }
}

// Format tags data
function formatTagsData(tags) {
  if (!tags || tags === "") return "No tags";
  return tags.split(",")
    .map(tag => `<span class="tag">${tag.trim()}</span>`)
    .join(" ");
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
    const sectionId = title.getAttribute("onclick").replace("toggleSection('", "").replace("')", "");
    const section = document.getElementById(sectionId);
    const icon = document.getElementById(`${sectionId}-icon`);

    // Set initial state (expanded)
    section.style.display = "block";
    icon.classList.remove("fa-chevron-right");
    icon.classList.add("fa-chevron-down");

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

  if (section.style.display === "none") {
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