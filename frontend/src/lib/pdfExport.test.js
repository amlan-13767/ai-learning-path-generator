import { describe, expect, it, vi } from 'vitest';

const mockSave = vi.fn();
const mockDoc = {
  internal: { pageSize: { getWidth: () => 595.28, getHeight: () => 841.89 } },
  setFillColor: vi.fn(),
  roundedRect: vi.fn(),
  setTextColor: vi.fn(),
  setDrawColor: vi.fn(),
  setFont: vi.fn(),
  setFontSize: vi.fn(),
  text: vi.fn(),
  splitTextToSize: vi.fn((textValue) => [textValue]),
  rect: vi.fn(),
  link: vi.fn(),
  addPage: vi.fn(),
  save: mockSave,
};

vi.mock('jspdf', () => ({
  jsPDF: vi.fn(() => mockDoc),
}));

import { buildLearningPathFilename, exportLearningPathPdf, isValidResourceUrl, sanitizeLearningPathFilename } from './pdfExport';

describe('pdf export helpers', () => {
  it('sanitizes a title into a safe filename', () => {
    expect(sanitizeLearningPathFilename('AI + Machine Learning!!!')).toBe('ai-machine-learning');
    expect(sanitizeLearningPathFilename('   ')).toBe('learning-path');
  });

  it('builds a pdf filename from result data', () => {
    expect(buildLearningPathFilename({ title: 'Python for Data Science' })).toBe('python-for-data-science.pdf');
    expect(buildLearningPathFilename({ topic: 'ML Ops' })).toBe('ml-ops.pdf');
  });

  it('accepts valid http(s) URLs and rejects bad values', () => {
    expect(isValidResourceUrl('https://example.com/course')).toBe(true);
    expect(isValidResourceUrl('http://localhost:3000')).toBe(true);
    expect(isValidResourceUrl('javascript:alert(1)')).toBe(false);
    expect(isValidResourceUrl('not-a-url')).toBe(false);
    expect(isValidResourceUrl('')).toBe(false);
  });

  it('calls the PDF generator with the learning data', () => {
    mockSave.mockClear();

    exportLearningPathPdf({
      title: 'Data Analyst Roadmap',
      topic: 'data analysis',
      description: 'Start with SQL and grow into analytics.',
      duration_weeks: 12,
      total_hours: 40,
      expertise_level: 'Intermediate',
      job_market_data: { demand_score: 88, open_positions: 120, average_salary: '$95k' },
      milestones: [
        {
          title: 'SQL foundations',
          description: 'Practice joins and aggregations.',
          skills_gained: ['SQL', 'analytics'],
          resources: [{ title: 'Mode SQL tutorial', url: 'https://example.com/sql' }],
        },
      ],
    });

    expect(mockSave).toHaveBeenCalledWith('data-analyst-roadmap.pdf');
  });
});
