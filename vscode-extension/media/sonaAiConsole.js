(function () {
  const vscode = acquireVsCodeApi();
  const script = document.currentScript;
  const initialAgents = safeParseAgents(script ? script.getAttribute("data-agents") : "");
  const defaultAgent = script ? script.getAttribute("data-default-agent") || "sona" : "sona";

  const elements = {
    agentTabs: document.getElementById("agentTabs"),
    activeAgentLabel: document.getElementById("activeAgentLabel"),
    providerStatus: document.getElementById("providerStatus"),
    messages: document.getElementById("messages"),
    promptInput: document.getElementById("promptInput"),
    sendButton: document.getElementById("sendButton"),
    clearButton: document.getElementById("clearButton"),
    toggleCurrentFile: document.getElementById("toggleCurrentFile"),
    toggleSelection: document.getElementById("toggleSelection"),
    toggleWorkspace: document.getElementById("toggleWorkspace"),
    toggleDiagnostics: document.getElementById("toggleDiagnostics")
  };

  const stored = vscode.getState() || {};
  const state = {
    activeAgent: stored.activeAgent || defaultAgent,
    agents: Array.isArray(stored.agents) && stored.agents.length ? stored.agents : initialAgents,
    messages: Array.isArray(stored.messages) ? stored.messages : [],
    busy: false,
    providerStatus: stored.providerStatus || undefined,
    toggles: Object.assign({
      currentFile: true,
      selectedText: true,
      workspaceSummary: true,
      diagnostics: true
    }, stored.toggles || {})
  };

  bindEvents();
  render();
  vscode.postMessage({ type: "refreshStatus" });

  window.addEventListener("message", event => {
    const message = event.data || {};
    if (message.type === "providerStatus") {
      state.providerStatus = message.status;
      state.agents = message.status && Array.isArray(message.status.agents)
        ? message.status.agents
        : state.agents;
      state.activeAgent = message.activeAgent || state.activeAgent || message.defaultAgent || "sona";
      render();
      persist();
      return;
    }

    if (message.type === "agentResponse") {
      state.busy = false;
      const response = message.response || {};
      addMessage({
        role: "agent",
        agentId: response.agentId || state.activeAgent,
        status: response.status || "error",
        text: response.text || "No response returned."
      });
      render();
      persist();
      return;
    }

    if (message.type === "clearChat") {
      state.messages = [];
      state.busy = false;
      render();
      persist();
      return;
    }

    if (message.type === "selectAgent") {
      state.activeAgent = message.agentId || state.activeAgent;
      render();
      persist();
    }
  });

  function bindEvents() {
    elements.sendButton.addEventListener("click", sendPrompt);
    elements.clearButton.addEventListener("click", () => {
      state.messages = [];
      state.busy = false;
      render();
      persist();
      vscode.postMessage({ type: "clearChat" });
    });
    elements.promptInput.addEventListener("keydown", event => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendPrompt();
      }
    });

    [
      elements.toggleCurrentFile,
      elements.toggleSelection,
      elements.toggleWorkspace,
      elements.toggleDiagnostics
    ].forEach(input => {
      input.addEventListener("change", () => {
        readToggles();
        persist();
      });
    });
  }

  function sendPrompt() {
    const prompt = elements.promptInput.value.trim();
    if (!prompt || state.busy) {
      return;
    }
    readToggles();
    addMessage({
      role: "user",
      agentId: state.activeAgent,
      status: "ok",
      text: prompt
    });
    state.busy = true;
    elements.promptInput.value = "";
    render();
    persist();
    vscode.postMessage({
      type: "sendPrompt",
      agentId: state.activeAgent,
      prompt,
      contextToggles: state.toggles
    });
  }

  function selectAgent(agentId) {
    state.activeAgent = agentId;
    render();
    persist();
    vscode.postMessage({
      type: "selectAgent",
      agentId
    });
  }

  function addMessage(message) {
    state.messages.push(Object.assign({
      id: Date.now().toString(36) + Math.random().toString(36).slice(2),
      createdAt: new Date().toISOString()
    }, message));
  }

  function render() {
    renderToggles();
    renderAgents();
    renderStatus();
    renderMessages();
    elements.sendButton.disabled = state.busy || !elements.promptInput.value.trim();
    elements.promptInput.disabled = state.busy;
    elements.sendButton.textContent = state.busy ? "Sending..." : "Send";
  }

  function renderAgents() {
    const active = getActiveAgent();
    elements.activeAgentLabel.textContent = active ? active.label : state.activeAgent;
    elements.agentTabs.textContent = "";
    state.agents.forEach(agent => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "agent-tab";
      if (agent.id === state.activeAgent) {
        button.classList.add("active");
      }
      if (!agent.configured) {
        button.classList.add("not-configured");
      }
      button.textContent = agent.label;
      button.title = `${agent.label}: ${agent.configured ? "configured" : "not configured"}\n${agent.description}`;
      button.addEventListener("click", () => selectAgent(agent.id));
      elements.agentTabs.appendChild(button);
    });
  }

  function renderStatus() {
    const active = getActiveAgent();
    const provider = elements.providerStatus;
    provider.className = "provider-status";
    if (!active) {
      provider.textContent = "Provider status unavailable.";
      provider.classList.add("status-error");
      return;
    }

    if (active.configured) {
      provider.textContent = `${active.label} provider ready.`;
      provider.classList.add("status-ok");
      return;
    }

    provider.textContent = `${active.label} provider not configured.`;
    provider.classList.add("status-warn");
  }

  function renderMessages() {
    elements.messages.textContent = "";
    if (!state.messages.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No messages yet.";
      elements.messages.appendChild(empty);
      return;
    }

    state.messages.forEach(message => {
      const wrapper = document.createElement("article");
      wrapper.className = `message ${message.role}`;
      if (message.status === "not_configured") {
        wrapper.classList.add("not-configured");
      }
      if (message.status === "error") {
        wrapper.classList.add("error");
      }

      const meta = document.createElement("div");
      meta.className = "message-meta";
      meta.textContent = `${message.role === "user" ? "You" : labelForAgent(message.agentId)} - ${message.status}`;

      const text = document.createElement("div");
      text.className = "message-text";
      text.textContent = message.text;

      wrapper.appendChild(meta);
      wrapper.appendChild(text);
      elements.messages.appendChild(wrapper);
    });
    elements.messages.scrollTop = elements.messages.scrollHeight;
  }

  function renderToggles() {
    elements.toggleCurrentFile.checked = Boolean(state.toggles.currentFile);
    elements.toggleSelection.checked = Boolean(state.toggles.selectedText);
    elements.toggleWorkspace.checked = Boolean(state.toggles.workspaceSummary);
    elements.toggleDiagnostics.checked = Boolean(state.toggles.diagnostics);
  }

  function readToggles() {
    state.toggles = {
      currentFile: elements.toggleCurrentFile.checked,
      selectedText: elements.toggleSelection.checked,
      workspaceSummary: elements.toggleWorkspace.checked,
      diagnostics: elements.toggleDiagnostics.checked
    };
  }

  function getActiveAgent() {
    return state.agents.find(agent => agent.id === state.activeAgent);
  }

  function labelForAgent(agentId) {
    const agent = state.agents.find(candidate => candidate.id === agentId);
    return agent ? agent.label : agentId;
  }

  function persist() {
    vscode.setState({
      activeAgent: state.activeAgent,
      agents: state.agents,
      messages: state.messages,
      providerStatus: state.providerStatus,
      toggles: state.toggles
    });
  }

  function safeParseAgents(encoded) {
    try {
      const parsed = JSON.parse(decodeURIComponent(encoded || "[]"));
      return Array.isArray(parsed) ? parsed : [];
    } catch (_error) {
      return [];
    }
  }

  elements.promptInput.addEventListener("input", render);
}());
