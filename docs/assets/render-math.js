// Render LaTeX equations to self-contained SVGs using MathJax.
//
// GitHub's mobile app renders images but not $$...$$ math. Every equation in
// README.md and docs/science/README.md is pre-rendered here and referenced as
// an <img>. Re-run this script after editing any equation.
//
// Usage:
//   node docs/assets/render-math.js

const fs = require("fs");
const path = require("path");

const MJ_PATH = path.join(__dirname, "node_modules", "mathjax-full");
require(path.join(MJ_PATH, "js", "util", "asyncLoad", "node.js"));

const { mathjax } = require(path.join(MJ_PATH, "js", "mathjax.js"));
const { TeX } = require(path.join(MJ_PATH, "js", "input", "tex.js"));
const { SVG } = require(path.join(MJ_PATH, "js", "output", "svg.js"));
const { liteAdaptor } = require(path.join(MJ_PATH, "js", "adaptors", "liteAdaptor.js"));
const { RegisterHTMLHandler } = require(path.join(MJ_PATH, "js", "handlers", "html.js"));
const { AllPackages } = require(path.join(MJ_PATH, "js", "input", "tex", "AllPackages.js"));

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);

const tex = new TeX({ packages: AllPackages });
const svg = new SVG({ fontCache: "none" });
const html = mathjax.document("", { InputJax: tex, OutputJax: svg });

const FG = "#e6edf3";
const OUT = path.join(__dirname, "math");
fs.mkdirSync(OUT, { recursive: true });

// [filename, TeX source]
const EQUATIONS = [
  // README.md science section
  ["gauss-sigma",
   String.raw`\sigma(P) = \sqrt{\dfrac{\sum_{i=1}^{5}\bigl(S_i(P) - 10\bigr)^2}{5}}`],
  ["gauss-transform",
   String.raw`P_{n+1} = T_{k^\ast}(P_n) \qquad \text{where} \qquad k^\ast = \arg\min_i \, S_i(P_n)`],
  ["sat-deploy",
   String.raw`\text{DEPLOY}(P) \;\iff\; \sigma(P) < \tau \;\wedge\; \bigwedge_{j=1}^{8} A_j(P)`],
  ["adapt-signature",
   String.raw`T : \; (P,\, M_s) \;\longrightarrow\; (P',\, M_t)`],
  ["adapt-constraints",
   String.raw`\text{Semantic}(P') = \text{Semantic}(P) \;\wedge\; \text{Techniques}(P') \cap \text{AntiPatterns}(M_t) = \emptyset`],
  ["robust-omega",
   String.raw`\Omega(P) = \dfrac{\bigl|\{\, k : \delta(P,\alpha(c_k)) = \text{RESIST} \,\}\bigr|}{|C|}`],
  ["robust-hardened",
   String.raw`P_{\text{hardened}} = \arg\max_{P'} \, \Omega(P') \qquad \text{s.t.} \qquad S(P') \geq S(P) - \varepsilon`],
  ["verified",
   String.raw`\text{VERIFIED}(P) \;\iff\; \sigma(P) < \tau \;\wedge\; \text{PassRate}(P, T) = 1.0`],
  ["accumulation",
   String.raw`K_n = K_{n-1} \cup \bigl\{\, (k^\ast,\, \Delta\sigma,\, \text{outcome}) \,\bigr\}`],

  // docs/science/README.md additional
  ["sci-argmin-only",
   String.raw`k^\ast = \arg\min_i \, S_i(P_n)`],
  ["sci-transform-only",
   String.raw`P_{n+1} = T_{k^\ast}(P_n)`],
  ["sci-accept",
   String.raw`\text{Accept}\; P_{n+1} \;\iff\; \sigma(P_{n+1}) < \sigma(P_n)`],
  ["sci-convergence",
   String.raw`\text{DEPLOY}:\; \sigma(P) < 0.45 \qquad \text{PLATEAU}:\; \sigma(P_n) = \sigma(P_{n-1}) = \sigma(P_{n-2}) \qquad \text{MAX}:\; n \geq 100`],
  ["sci-adapt-composition",
   String.raw`P' = A_{M_t} \circ T_{M_t} \circ F_{M_s \to M_t}(P)`],
  ["sci-passrate",
   String.raw`\text{PassRate}(P, T) = \dfrac{\bigl|\{\, i : \forall s \in E_i,\; s \subseteq \text{Output}(P, x_i) \,\}\bigr|}{|T|}`],

  // Fae context-health equations
  ["fae-readloop",
   String.raw`P(\text{read\ loop}) = 1 \quad \text{if} \quad \text{count}\bigl(\text{read}(f, h)\bigr) \geq 3 \;\wedge\; \nexists\, \text{write}(f)`],
  ["fae-editrevert",
   String.raw`P(\text{edit\ revert}) = 1 \quad \text{if} \quad h\bigl(\text{write}_n(f)\bigr) = h\bigl(\text{write}_{n-2}(f)\bigr)`],
  ["fae-testfail",
   String.raw`P(\text{test\ fail}) = 1 \quad \text{if} \quad \text{count}\bigl(\text{bash}(\text{cmd},\, \text{exit} \neq 0)\bigr) \geq 3`],
  ["fae-alert",
   String.raw`\text{Alert}(t) = 1 \;\iff\; P(\text{drift}) = 1 \;\wedge\; t - t_{\text{last}} > \tau`],
  ["fae-forecast",
   String.raw`\hat{\mu} = \dfrac{1}{N}\sum_{i=1}^{N} \text{tokens}_i \qquad \text{runway} = \left\lfloor \dfrac{\text{remaining}}{\hat{\mu}} \right\rfloor`],
  ["fae-ci",
   String.raw`\text{CI} = t_{\alpha/2} \cdot \dfrac{s}{\sqrt{N}}`],
  ["fae-compression",
   String.raw`O \;\longrightarrow\; O' \qquad \text{s.t.} \qquad H(O') \geq \theta \cdot H(O) \;\wedge\; |O'| < |O|`],
  ["fae-cr",
   String.raw`\text{CR}(O) = 1 - \dfrac{|O'|}{|O|}`],
  ["fae-checkpoint-size",
   String.raw`\bigl|\text{Checkpoint}(t)\bigr| \leq 50\,\text{KB}`],
  ["fae-atomic",
   String.raw`\text{write}(f.\text{tmp}) \;\to\; \text{validate}(f.\text{tmp}) \;\to\; \text{rename}(f.\text{tmp},\, f)`],
  ["fae-sha",
   String.raw`h_t = \text{SHA256}\bigl(\text{content}(f, t)\bigr)`],
  ["fae-decision",
   String.raw`\text{Decision}(f, t) = \begin{cases} \text{BLOCK} & \text{cache}[f].h = h_t \\ \text{ALLOW} & \text{cache}[f].h \neq h_t \\ \text{ALLOW} & t - \text{cache}[f].t > \text{TTL} \end{cases}`],
];

function render(name, source) {
  const node = html.convert(source, { display: true, em: 16, ex: 8, containerWidth: 1200 });
  let svgStr = adaptor.innerHTML(node);
  // Force visible ink. MathJax uses currentColor by default, which on mobile
  // GitHub (image opened in isolation) falls back to black — invisible on our
  // dark page. Bake a fixed fill so the SVG is self-contained.
  svgStr = svgStr.replace(/currentColor/g, FG);
  svgStr = `<?xml version="1.0" encoding="UTF-8"?>\n` + svgStr;
  const outPath = path.join(OUT, `${name}.svg`);
  fs.writeFileSync(outPath, svgStr, "utf8");
  console.log(`  docs/assets/math/${name}.svg`);
}

console.log(`Rendering ${EQUATIONS.length} equations...`);
for (const [name, src] of EQUATIONS) {
  try {
    render(name, src);
  } catch (err) {
    console.error(`FAILED: ${name}\n  ${err.message}`);
    process.exitCode = 1;
  }
}
console.log("Done.");
