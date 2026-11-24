import { useEffect, useRef, useState } from 'react'

// Zahlenfeld zum freien Tippen (REV01-B05): kein Browser-Spinner, Komma oder Punkt als Dezimaltrenner,
// Zwischenstände wie „12,“ oder „-“ bleiben stehen. Nach außen wird ein Ereignis mit Punkt-Dezimalzahl gemeldet,
// damit bestehende Handler (Number(e.target.value)) unverändert funktionieren.
// Für type ≠ "number" wird ein normales Eingabefeld gezeigt.
const toText = (v) => (v === null || v === undefined || v === '' || Number.isNaN(v) ? '' : String(v).replace('.', ','))
const parse = (t) => {
  // „1.234,5“ → 1234.5 · „12,5“ → 12.5 · „12.5“ → 12.5 · „1.234.567“ → 1234567
  let s = String(t).trim().replace(/\s/g, '')
  if (s.includes(',')) s = s.replace(/\./g, '').replace(',', '.')
  else if ((s.match(/\./g) || []).length > 1) s = s.replace(/\./g, '')
  if (s === '') return ''
  return /^-?\d*\.?\d*$/.test(s) && /\d/.test(s) ? s : null
}

export default function NumInput({ type = 'number', value, onChange, onBlur, step, min, max, className = '', ...rest }) {
  if (type !== 'number') return <input type={type} autoComplete={type === 'password' ? 'new-password' : 'off'} value={value} onChange={onChange} onBlur={onBlur} className={className} step={step} min={min} max={max} {...rest} />
  return <NumText value={value} onChange={onChange} onBlur={onBlur} className={className} {...rest} />
}

function NumText({ value, onChange, onBlur, className, ...rest }) {
  const [text, setText] = useState(toText(value))
  const focused = useRef(false)
  useEffect(() => {
    // Wert von außen geändert (Standard übernommen, Standortwechsel …) → Anzeige nachziehen
    const p = parse(text)
    if (p === null || (p === '' ? '' : Number(p)) !== (value === '' || value == null ? '' : Number(value))) {
      if (!focused.current || p === null) setText(toText(value))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])
  return (
    <input type="text" inputMode="decimal" autoComplete="off" className={`${className} num`.trim()} value={text} {...rest}
      onFocus={(e) => { focused.current = true; rest.onFocus?.(e) }}
      onChange={(e) => {
        const t = e.target.value
        setText(t)
        const p = parse(t)
        if (p !== null && !/[.,]$/.test(t.trim()) && t.trim() !== '-') onChange?.({ target: { value: p, name: rest.name, id: rest.id } })
        else if (p === '') onChange?.({ target: { value: '', name: rest.name, id: rest.id } })
      }}
      onBlur={(e) => { focused.current = false; setText(toText(value)); onBlur?.(e) }} />
  )
}
