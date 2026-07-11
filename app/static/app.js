const form = document.querySelector("#lab-form");
const jokeInput = document.querySelector("#joke-input");
const characterCount = document.querySelector("#character-count");
const runButton = document.querySelector("#run-button");
const progress = document.querySelector("#progress");
const progressCopy = document.querySelector("#progress-copy");
const errorMessage = document.querySelector("#error-message");
const resultsPanel = document.querySelector("#results-panel");
const emptyState = document.querySelector("#empty-state");
const resultContent = document.querySelector("#result-content");

let currentRun = null;
let runtimeModel = "unknown";

function updateCount() {
  characterCount.textContent = `${jokeInput.value.length} / 4000`;
}

function shuffle(items) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[randomIndex]] = [copy[randomIndex], copy[index]];
  }
  return copy;
}

function setLoading(isLoading) {
  runButton.disabled = isLoading;
  progress.hidden = !isLoading;
}

function setProgress(message) {
  progressCopy.textContent = message;
}

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "The model could not complete this run.");
  return data;
}

async function loadRuntime() {
  try {
    const response = await fetch("/health");
    const data = await response.json();
    runtimeModel = data.model || "unknown";
    document.querySelector("#model-name").textContent = runtimeModel;
  } catch (_error) {
    document.querySelector("#model-name").textContent = "runtime offline";
  }
}

function textElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = text;
  return element;
}

function renderGenome(genome) {
  document.querySelector("#confidence-value").textContent = `${Math.round(genome.confidence * 100)}%`;
  const anatomyGrid = document.querySelector("#anatomy-grid");
  anatomyGrid.replaceChildren();
  [
    ["PREMISE", genome.premise],
    ["TURN", genome.turn],
    ["PUNCHLINE", genome.punchline],
  ].forEach(([label, copy]) => {
    const card = textElement("article", "anatomy-card", "");
    card.append(textElement("small", "", label), textElement("p", "", copy));
    anatomyGrid.append(card);
  });

  const mechanismList = document.querySelector("#mechanism-list");
  mechanismList.replaceChildren();
  genome.mechanisms.forEach((item) => {
    const chip = textElement("span", "mechanism-chip", item.mechanism.replaceAll("_", " "));
    chip.append(textElement("span", "", `${Math.round(item.confidence * 100)}%`));
    chip.title = `${item.evidence} — ${item.role}`;
    mechanismList.append(chip);
  });
}

function renderGenomeStage(genome, targetGene) {
  resultsPanel.classList.remove("empty");
  emptyState.hidden = true;
  resultContent.hidden = false;
  renderGenome(genome);
  document.querySelector("#target-gene-badge").textContent = `editing: ${targetGene.replaceAll("_", " ")}`;
  document.querySelector("#comparison-panel").hidden = true;
  const variantGrid = document.querySelector("#variant-grid");
  variantGrid.replaceChildren(
    textElement("div", "variant-skeleton", ""),
    textElement("div", "variant-skeleton", ""),
  );
  resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderVariants(mutation) {
  document.querySelector("#target-gene-badge").textContent = `editing: ${mutation.target_gene.replaceAll("_", " ")}`;
  const variantGrid = document.querySelector("#variant-grid");
  const comparisonPanel = document.querySelector("#comparison-panel");
  variantGrid.replaceChildren();
  comparisonPanel.hidden = true;

  shuffle(mutation.variants).forEach((variant, index) => {
    const blindLabel = String.fromCharCode(65 + index);
    const card = textElement("article", "variant-card", "");
    card.dataset.originalLabel = variant.label;
    card.append(
      textElement("span", "variant-letter", blindLabel),
      textElement("p", "variant-text", variant.text),
    );
    const button = textElement("button", "choose-button", `Choose ${blindLabel}`);
    button.type = "button";
    button.addEventListener("click", () => revealChoice(card, blindLabel, variant));
    card.append(button);
    variantGrid.append(card);
  });
}

async function revealChoice(chosenCard, blindLabel, variant) {
  document.querySelectorAll(".variant-card").forEach((card) => {
    card.classList.toggle("chosen", card === chosenCard);
    card.classList.toggle("dimmed", card !== chosenCard);
    card.querySelector("button").disabled = true;
  });

  const panel = document.querySelector("#comparison-panel");
  panel.hidden = false;
  document.querySelector("#choice-heading").textContent = `You chose ${blindLabel}. Gemma is inspecting the trade-off…`;
  document.querySelector("#tradeoff-copy").textContent = "The comparison starts only after your human choice.";
  document.querySelector("#human-test-copy").textContent = "Waiting for the comparison…";
  const list = document.querySelector("#observation-list");
  list.replaceChildren();
  panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  void saveFeedback(blindLabel, variant);

  try {
    const comparison = await postJson("/v1/compare", {
      source_text: currentRun.sourceText,
      variants: currentRun.mutation.variants,
      context: currentRun.context,
    });
    document.querySelector("#choice-heading").textContent = `You chose ${blindLabel}. Now inspect the trade-off.`;
    document.querySelector("#tradeoff-copy").textContent = comparison.key_tradeoff;
    document.querySelector("#human-test-copy").textContent = comparison.suggested_human_test;

    const selected = comparison.observations.find((item) => item.label === variant.label);
    const observations = selected ? [selected, ...comparison.observations.filter((item) => item !== selected)] : comparison.observations;
    observations.forEach((item) => {
      const block = textElement("div", "observation", "");
      block.append(
        textElement("h4", "", item.label === variant.label ? "Your choice" : "Alternative"),
        textElement("p", "", `${item.mechanism_effect} Uncertainty: ${item.uncertainty}`),
      );
      list.append(block);
    });
  } catch (error) {
    document.querySelector("#choice-heading").textContent = `You chose ${blindLabel}.`;
    document.querySelector("#tradeoff-copy").textContent = error.message;
    document.querySelector("#human-test-copy").textContent = "Your blind choice is still valid even when model explanation fails.";
  }
}

async function saveFeedback(blindLabel, variant) {
  const status = document.querySelector("#feedback-status");
  if (!currentRun.saveFeedback) {
    status.textContent = "Choice kept in this browser only.";
    return;
  }
  status.textContent = "Saving your opted-in evaluation example locally…";
  try {
    await postJson("/v1/feedback", {
      experiment_id: currentRun.experimentId,
      source_text: currentRun.sourceText,
      target_gene: currentRun.mutation.target_gene,
      variants: currentRun.mutation.variants,
      chosen_variant_label: variant.label,
      blind_label: blindLabel,
      model: runtimeModel,
      consent: true,
    });
    status.textContent = "A/B choice saved locally for evaluation.";
  } catch (_error) {
    status.textContent = "The choice could not be saved; the comparison still works.";
  }
}

document.querySelectorAll("input[name='gene']").forEach((input) => {
  input.addEventListener("change", () => {
    document.querySelectorAll(".gene").forEach((label) => label.classList.remove("active"));
    input.closest(".gene").classList.add("active");
  });
});

jokeInput.addEventListener("input", updateCount);
updateCount();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorMessage.hidden = true;
  setLoading(true);
  const payload = {
    text: jokeInput.value.trim(),
    target_gene: new FormData(form).get("gene"),
    number_of_variants: 2,
    context: {
      target_audience: document.querySelector("#audience-input").value.trim(),
      format: "short written joke",
      desired_tone: document.querySelector("#tone-input").value.trim(),
      language: "English",
      constraints: [],
    },
  };

  try {
    setProgress("Gemma is mapping the setup, turn, and punchline…");
    const genome = await postJson("/v1/analyze", {
      text: payload.text,
      context: payload.context,
    });
    renderGenomeStage(genome, payload.target_gene);

    setProgress("Genome ready. Editing one gene while preserving the premise…");
    const mutation = await postJson("/v1/mutate", {
      source_text: payload.text,
      genome,
      target_gene: payload.target_gene,
      context: payload.context,
      invariants: ["preserve the premise", "preserve the author's voice"],
      number_of_variants: payload.number_of_variants,
    });
    currentRun = {
      experimentId: crypto.randomUUID(),
      sourceText: payload.text,
      context: payload.context,
      genome,
      mutation,
      saveFeedback: document.querySelector("#feedback-consent").checked,
    };
    renderVariants(mutation);
  } catch (error) {
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
  } finally {
    setLoading(false);
  }
});

void loadRuntime();
