import { jsPDF } from 'jspdf';

export function sanitizeLearningPathFilename(value = 'learning-path') {
  const normalized = String(value || 'learning-path')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase();

  return normalized || 'learning-path';
}

export function buildLearningPathFilename(pathData) {
  const baseName = pathData?.title || pathData?.topic || 'learning-path';
  return `${sanitizeLearningPathFilename(baseName)}.pdf`;
}

export function isValidResourceUrl(url) {
  if (!url || typeof url !== 'string') return false;

  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}

function addBlockText(doc, text, x, y, width, options = {}) {
  const { fontSize = 11, lineHeight = 16, font = 'helvetica', fontStyle = 'normal' } = options;
  const safeText = String(text ?? '').replace(/\s+/g, ' ').trim();

  if (!safeText) {
    return y;
  }

  doc.setFont(font, fontStyle);
  doc.setFontSize(fontSize);
  const lines = doc.splitTextToSize(safeText, width);
  doc.text(x, y, lines);

  return y + lines.length * lineHeight;
}

function ensureSpace(doc, y, pageHeight, margin) {
  if (y > pageHeight - margin * 2) {
    doc.addPage();
    return margin;
  }

  return y;
}

export function exportLearningPathPdf(pathData) {
  if (!pathData) return;

  const doc = new jsPDF({ unit: 'pt', format: 'a4' });
  const margin = 40;
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const contentWidth = pageWidth - margin * 2;
  const title = pathData.title || `${pathData.topic || 'Learning'} learning path`;
  const description = pathData.description || 'A generated roadmap to guide your next learning sprint.';

  let y = margin;
  doc.setFillColor(11, 18, 32);
  doc.roundedRect(margin, y - 18, pageWidth - margin * 2, 30, 8, 8, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(18);
  doc.text('Learning Path', margin + 16, y + 2);
  y += 48;

  doc.setTextColor(17, 24, 39);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(22);
  const titleLines = doc.splitTextToSize(title, contentWidth);
  doc.text(titleLines, margin, y);
  y += titleLines.length * 18 + 14;

  y = ensureSpace(doc, y, pageHeight, margin);
  y = addBlockText(doc, description, margin, y, contentWidth, { fontSize: 11, lineHeight: 16 });
  y += 12;

  const statItems = [
    { label: 'Duration', value: `${pathData.duration_weeks || 0} weeks` },
    { label: 'Estimated time', value: `${pathData.total_hours || 0} hours` },
    { label: 'Starting level', value: pathData.expertise_level || 'Custom' },
    { label: 'Modules', value: String(pathData.milestones?.length || 0) },
  ];

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  y = ensureSpace(doc, y, pageHeight, margin);
  const statX = margin;
  const statBoxWidth = contentWidth / statItems.length;
  statItems.forEach(({ label, value }, index) => {
    const x = statX + index * statBoxWidth;
    doc.setDrawColor(204, 214, 224);
    doc.rect(x, y, statBoxWidth - 12, 44, 'S');
    doc.setTextColor(91, 103, 123);
    doc.text(label, x + 10, y + 16);
    doc.setTextColor(17, 24, 39);
    doc.text(value, x + 10, y + 32);
  });
  y += 60;

  if (pathData.job_market_data) {
    const market = pathData.job_market_data;
    y = ensureSpace(doc, y, pageHeight, margin);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(14);
    doc.text('Career signals', margin, y);
    y += 18;
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(11);
    const marketLines = [
      `Demand: ${market.demand_score || '--'}/100`,
      `Open positions: ${market.open_positions || 'Researching'}`,
      `Salary range: ${market.average_salary || 'Researching'}`,
    ];
    marketLines.forEach((line) => {
      y = ensureSpace(doc, y, pageHeight, margin);
      doc.text(line, margin, y);
      y += 18;
    });
  }

  const milestones = pathData.milestones || [];
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(14);
  y = ensureSpace(doc, y, pageHeight, margin);
  doc.text('Milestones', margin, y);
  y += 20;

  milestones.forEach((milestone, index) => {
    y = ensureSpace(doc, y, pageHeight, margin);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.text(`${index + 1}. ${milestone.title || `Milestone ${index + 1}`}`, margin, y);
    y += 18;

    y = addBlockText(doc, milestone.description || milestone.descript || '', margin, y, contentWidth, {
      fontSize: 10,
      lineHeight: 14,
    });
    y += 6;

    const skills = milestone.skills_gained || [];
    if (skills.length > 0) {
      y = addBlockText(doc, `Skills: ${skills.join(', ')}`, margin, y, contentWidth, {
        fontSize: 10,
        lineHeight: 14,
      });
      y += 4;
    }

    const resources = milestone.resources || [];
    if (resources.length > 0) {
      y = ensureSpace(doc, y, pageHeight, margin);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(10);
      doc.text('Resources', margin, y);
      y += 14;

      resources.forEach((resource) => {
        y = ensureSpace(doc, y, pageHeight, margin);
        const label = resource.title || resource.name || 'Resource';
        const url = resource.url || '';
        const resourceText = url ? `${label} — ${url}` : label;
        const lines = doc.splitTextToSize(resourceText, contentWidth);
        const blockHeight = lines.length * 12;

        if (isValidResourceUrl(url)) {
          doc.link(margin, y - 10, contentWidth, blockHeight + 8, { url });
        }

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        doc.text(lines, margin, y);
        y += blockHeight + 8;
      });
    }

    y += 12;
  });

  const fileName = buildLearningPathFilename(pathData);
  doc.save(fileName);
}
