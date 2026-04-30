import React from 'react'

export interface ReportTableColumn<T> {
  key: keyof T | string
  label: string
  render?: (row: T) => React.ReactNode
}

interface Props<T> {
  columns: ReportTableColumn<T>[]
  rows: T[]
}

function valueFor<T>(row: T, key: keyof T | string): React.ReactNode {
  const value = row[key as keyof T]
  if (value === null || value === undefined || value === '') return 'Dato non fornito'
  return String(value)
}

export function ReportTable<T>({ columns, rows }: Props<T>) {
  return (
    <div className="report-table-wrap">
      <table className="report-table">
        <thead>
          <tr>
            {columns.map(column => (
              <th key={String(column.key)}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length > 0 ? (
            rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {columns.map(column => (
                  <td key={String(column.key)}>
                    {column.render ? column.render(row) : valueFor(row, column.key)}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length}>Dato non fornito</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
