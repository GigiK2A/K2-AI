import React from 'react'

interface SectorPickerProps {
  sectors: Array<{ slug: string; label: string }>
  selectedSector: string
  problem: string
  onSectorSelect: (sector: string) => void
  onProblemChange: (value: string) => void
  onNext: () => void
}

export function SectorPicker({
  sectors,
  selectedSector,
  problem,
  onSectorSelect,
  onProblemChange,
  onNext,
}: SectorPickerProps) {
  const canProceed = selectedSector.length > 0 && problem.trim().length >= 10

  return (
    <div className="kbot-intake-stream">
      <div className="kbot-bubble assistant">
        <div className="kbot-bubble-role">K-BOT</div>
        <div className="kbot-bubble-text">Ciao! Prima di tutto: in quale settore operi?</div>
      </div>

      <div className="kbot-intake-options">
        <div className="kbot-sector-grid">
          {sectors.map(sector => (
            <button
              key={sector.slug}
              type="button"
              className={`kbot-sector-card ${selectedSector === sector.slug ? 'active' : ''}`}
              onClick={() => onSectorSelect(sector.slug)}
            >
              {sector.label}
            </button>
          ))}
        </div>
      </div>

      <div className="kbot-bubble assistant">
        <div className="kbot-bubble-role">K-BOT</div>
        <div className="kbot-bubble-text">Descrivi in parole tue cosa ti serve</div>
      </div>

      <div className="kbot-intake-options">
        <textarea
          id="kbot-problem-input"
          className="kbot-textarea"
          placeholder="Esempio: Gestiamo 120 clienti e perdiamo ore ogni settimana nella raccolta documenti e riconciliazione."
          value={problem}
          onChange={e => onProblemChange(e.target.value)}
        />
      </div>

      <button type="button" className="kbot-next-btn" onClick={onNext} disabled={!canProceed}>
        Avanti →
      </button>
    </div>
  )
}
