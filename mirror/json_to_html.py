import json
import re

def clean_style(style):
    # Remove height, top, left, transform (for stacked layout only)
    cleaned = re.sub(r'(height|top|left|transform)\s*:[^;]+;?', '', style, flags=re.IGNORECASE)
    # Add box layout styling
    cleaned += '; border: 1px solid #ccc; padding: 1rem; max-width: 900px; margin: 1rem auto; box-shadow: 2px 2px 5px rgba(0,0,0,0.05)'
    return cleaned.strip()

# Load JSON
with open('../research/2908423/2908423.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

tools_text = data['pages']['2908424']['tools'].get('tool-text', [])
tools_images = data['pages']['2908424']['tools'].get('tool-picture', [])

# Begin HTML output
html_output = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>RC Mirror</title>
<style>
  body {
    margin: 0;
    padding: 0;
    font-family: sans-serif;
  }
  .tool {
    position: absolute;
    box-sizing: border-box;
    transition: all 0.3s ease;
  }
  body.stacked .tool {
    position: static;
  }
  .toggle-layout {
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 1000;
    padding: 0.5rem 1rem;
    background: #007bff;
    color: white;
    border: none;
    cursor: pointer;
  }
  .view-btn {
    display: none;
    margin-top: 1rem;
    padding: 0.3rem 0.6rem;
    font-size: 0.9rem;
    background: #28a745;
    color: white;
    border: none;
    cursor: pointer;
  }
  .toggle-text-formatting {
    position: fixed;
    top: 4rem;
    left: 1rem;
    z-index: 1000;
    padding: 0.5rem 1rem;
    background: #17a2b8;
    color: white;
    border: none;
    cursor: pointer;
    }
  body.stacked .view-btn {
    display: inline-block;
  }
  @keyframes flash {
    0%   { box-shadow: 0 0 0px rgba(255, 200, 0, 0); }
    50%  { box-shadow: 0 0 20px 5px rgba(255, 200, 0, 0.9); }
    100% { box-shadow: 0 0 0px rgba(255, 200, 0, 0); }
  }
  .tool.highlight {
    animation: flash 1s ease;
  }
</style>
</head>
<body class="absolute">
<button class="toggle-layout" onclick="toggleLayout()">Toggle Layout</button>
<button class="toggle-text-formatting" onclick="toggleTextFormatting()">Toggle Text Formatting</button>
<script>
let formattingStripped = false;

function toggleTextFormatting() {
  const contentBlocks = document.querySelectorAll('.html-text-editor-content');

  contentBlocks.forEach(block => {
    if (!block.dataset.originalHtml) {
      // Save original
      block.dataset.originalHtml = block.innerHTML;
    }

    if (!formattingStripped) {
      // Strip formatting
      const stripped = stripStyles(block.innerHTML);
      block.innerHTML = stripped;
    } else {
      // Restore original
      block.innerHTML = block.dataset.originalHtml;
    }
  });

  formattingStripped = !formattingStripped;
}

function stripStyles(html) {
  // Create a temporary DOM element to manipulate
  const temp = document.createElement('div');
  temp.innerHTML = html;

  // Remove all inline styles
  temp.querySelectorAll('[style]').forEach(el => el.removeAttribute('style'));

  // Unwrap formatting tags (em, strong, span, etc. except p and br)
  temp.querySelectorAll('em, strong, span').forEach(el => {
    const parent = el.parentNode;
    while (el.firstChild) parent.insertBefore(el.firstChild, el);
    parent.removeChild(el);
  });

  return temp.innerHTML;
}

function toggleLayout() {
  const body = document.body;
  const stacked = body.classList.toggle('stacked');
  const tools = document.querySelectorAll('.tool');
  tools.forEach(tool => {
    if (stacked) {
      tool.setAttribute('style', tool.dataset.stackedStyle);
    } else {
      tool.setAttribute('style', tool.dataset.absoluteStyle);
    }
  });

  if (stacked) {
    window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
  }
}

function viewInPosition(id) {
  document.body.classList.remove('stacked');
  const tools = document.querySelectorAll('.tool');
  tools.forEach(tool => {
    tool.setAttribute('style', tool.dataset.absoluteStyle);
  });

  setTimeout(() => {
    const el = document.getElementById(id);
    if (el) {
      const rect = el.getBoundingClientRect();
      const scrollX = window.scrollX + rect.left + rect.width / 2 - window.innerWidth / 2;
      const scrollY = window.scrollY + rect.top + rect.height / 2 - window.innerHeight / 2;
      window.scrollTo({ top: scrollY, left: scrollX, behavior: 'smooth' });

      el.classList.add('highlight');
      setTimeout(() => el.classList.remove('highlight'), 1000);
    }
  }, 100);
}

window.addEventListener('load', () => {
  const tools = document.querySelectorAll('.tool');
  let maxBottom = 0;
  let maxRight = 0;
  tools.forEach(tool => {
    const style = tool.dataset.absoluteStyle;
    const top = parseFloat(/top:\s*([\d.]+)px/.exec(style)?.[1] || 0);
    const left = parseFloat(/left:\s*([\d.]+)px/.exec(style)?.[1] || 0);
    const height = parseFloat(/height:\s*([\d.]+)px/.exec(style)?.[1] || 0);
    const width = parseFloat(/width:\s*([\d.]+)px/.exec(style)?.[1] || 0);
    maxBottom = Math.max(maxBottom, top + height);
    maxRight = Math.max(maxRight, left + width);
  });

  const spacer = document.createElement('div');
  spacer.style.position = 'absolute';
  spacer.style.top = (maxBottom + 200) + 'px';
  spacer.style.left = (maxRight + 200) + 'px';
  spacer.style.width = '1px';
  spacer.style.height = '1px';
  document.body.appendChild(spacer);
});
</script>
"""

# Add text tools
for i, tool in enumerate(tools_text):
    style = tool.get("style", "")
    content = tool.get("content", "")
    stacked_style = clean_style(style)
    html_output += (
        f'<div class="tool" id="tool-text-{i}" contenteditable="true" '
        f'data-absolute-style="{style}" '
        f'data-stacked-style="{stacked_style}" '
        f'style="{style}">'
        f'{content}'
        f'<br><button class="view-btn" onclick="viewInPosition(\'tool-text-{i}\')">View in Position</button>'
        f'</div>\n'
    )

# Add image tools
for j, pic in enumerate(tools_images):
    style = pic.get("style", "")
    src = pic.get("src", "")
    alt = pic.get("name", f"Image {j}")
    # For stacked view, remove position-related styling
    stacked_style = clean_style(style)
    html_output += (
        f'<div class="tool" id="tool-img-{j}" '
        f'data-absolute-style="{style}" '
        f'data-stacked-style="{stacked_style}" '
        f'style="{style}">'
        f'<img src="{src}" alt="{alt}" style="max-width: 100%; height: auto;">'
        f'<br><button class="view-btn" onclick="viewInPosition(\'tool-img-{j}\')">View in Position</button>'
        f'</div>\n'
    )

# Close HTML
html_output += """
</body>
</html>
"""

# Save to file
with open('rcMirror.html', 'w', encoding='utf-8') as f:
    f.write(html_output)

print("Mirror saved as 'mirror.html'.")