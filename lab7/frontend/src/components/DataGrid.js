// src/components/DataGrid.js
// Renders a paginated, scrollable preview table for dataset rows.

import React, { useState } from 'react';

export default function DataGrid({ columns = [], rows = [] }) {
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 8;
  const totalPages = Math.ceil(rows.length / PAGE_SIZE);
  const visible = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  if (!columns.length) return null;

  return (
    <div>
      <div className="data-grid-wrap">
        <table className="data-grid">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col} title={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((row, ri) => (
              <tr key={ri}>
                {columns.map((col) => (
                  <td key={col} title={String(row[col] ?? '')}>
                    {row[col] ?? <span style={{ color: '#9CA3AF' }}>null</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex-between mt-4" style={{ fontSize: 13, color: 'var(--color-muted)' }}>
          <span>
            Showing rows {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, rows.length)} of {rows.length}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="btn btn-ghost"
              style={{ padding: '5px 14px', fontSize: 13 }}
            >← Prev</button>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page === totalPages - 1}
              className="btn btn-ghost"
              style={{ padding: '5px 14px', fontSize: 13 }}
            >Next →</button>
          </div>
        </div>
      )}
    </div>
  );
}
