import { useState } from 'react'
import type {
  BeforeAfter,
  CostAssumptions,
  CostEstimate,
  FixRoadmapItem,
  GTIN14Suggestion,
  GTINResult,
  HierarchyAnalysis,
  RetailerChecklist,
  Severity,
} from '../types'
import styles from './AnalysisSections.module.css'

function effortColor(v: string) {
  return v === 'Low' ? '#158f75' : v === 'Medium' ? '#ee8a2a' : '#cc100a'
}
function impactColor(v: string) {
  return v === 'High' ? '#cc100a' : v === 'Medium' ? '#ee8a2a' : '#158f75'
}

// ---------------------------------------------------------------------------
// Issues by Severity
// ---------------------------------------------------------------------------

export function IssuesBySeverity({ results }: { results: GTINResult[] }) {
  const critical = results.filter((r) => r.has_critical)
  const warning = results.filter((r) => r.has_warning && !r.has_critical)
  const info = results.filter(
    (r) => r.issues.length > 0 && !r.has_critical && !r.has_warning,
  )

  function renderGroup(
    items: GTINResult[],
    severity: Severity,
    label: string,
    badgeClass: string,
    desc: string,
  ) {
    if (!items.length) return null
    return (
      <>
        <p>
          <span className={`badge ${badgeClass}`}>{label}</span> &mdash; {desc}
        </p>
        {items.map((r) => (
          <details key={r.row_number} className={styles.expandable}>
            <summary>
              Row {r.row_number}: {r.raw_input}
            </summary>
            <div className={styles.expandableContent}>
              {r.issues
                .filter(
                  (i) =>
                    severity === 'Critical'
                      ? i.severity === 'Critical'
                      : true,
                )
                .map((issue, idx) => (
                  <div key={idx} style={{ marginBottom: '0.75rem' }}>
                    <div
                      className={
                        issue.severity === 'Critical'
                          ? styles.issueError
                          : styles.issueWarning
                      }
                    >
                      {issue.message}
                    </div>
                    <div className={styles.fix}>
                      <strong>Fix: </strong>
                      {issue.recommendation}
                    </div>
                    <div className={styles.fix}>
                      <strong>Retailer impact: </strong>
                      {issue.retailer_impact}
                    </div>
                  </div>
                ))}
            </div>
          </details>
        ))}
      </>
    )
  }

  return (
    <section id="issues" className={styles.section}>
      <h3>Issues by Severity</h3>
      {renderGroup(critical, 'Critical', 'CRITICAL', 'badge-critical', 'These GTINs will be rejected by retailers.')}
      {renderGroup(warning, 'Warning', 'WARNING', 'badge-warning', 'These GTINs may cause problems.')}
      {renderGroup(info, 'Info', 'INFO', 'badge-info', 'Best practice notes.')}
      {!critical.length && !warning.length && !info.length && (
        <div className={styles.success}>All GTINs passed validation with no issues.</div>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Full Item Detail
// ---------------------------------------------------------------------------

export function FullItemDetail({ results }: { results: GTINResult[] }) {
  return (
    <section id="detail" className={styles.section}>
      <h3>Full Item Detail</h3>
      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Row</th>
              <th>GTIN</th>
              <th>Type</th>
              <th>Status</th>
              <th>Issues</th>
              <th>Corrected</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.row_number}>
                <td>{r.row_number}</td>
                <td style={{ fontFamily: 'monospace' }}>{r.raw_input}</td>
                <td>{r.gtin_type}</td>
                <td>
                  {!r.issues.length
                    ? 'Clean'
                    : r.has_critical
                      ? 'Critical'
                      : r.has_warning
                        ? 'Warning'
                        : 'Info'}
                </td>
                <td>{r.issues.length}</td>
                <td style={{ fontFamily: 'monospace' }}>{r.corrected_value || ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// Check Digit Corrections
// ---------------------------------------------------------------------------

export function CheckDigitCorrections({
  items,
}: {
  items: BeforeAfter[]
}) {
  return (
    <section id="corrections" className={styles.section}>
      <h3>Check Digit Corrections</h3>
      <p>
        These GTINs have incorrect check digits. Always verify corrections
        against your original barcode or GS1 registration before updating your
        product master.
      </p>
      {items.length ? (
        <table>
          <thead>
            <tr>
              <th>Row</th>
              <th>Current (Before)</th>
              <th>Corrected (After)</th>
              <th>Issue</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.row}>
                <td>{item.row}</td>
                <td style={{ fontFamily: 'monospace' }}>{item.before}</td>
                <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{item.after}</td>
                <td>{item.issue}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className={styles.success}>
          No check digit corrections needed — all check digits are valid.
        </div>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Packaging Hierarchy
// ---------------------------------------------------------------------------

export function PackagingHierarchy({
  hierarchy,
}: {
  hierarchy: HierarchyAnalysis
}) {
  return (
    <section id="hierarchy" className={styles.section}>
      <h3>Packaging Hierarchy Analysis</h3>
      <p>
        Retailers like Walmart require GTINs at every packaging level — each,
        inner pack, case, and pallet. This analysis checks whether your
        case-level GTIN-14s match up with unit-level GTINs.
      </p>

      {hierarchy.matched_pairs.length > 0 && (
        <>
          <h4>Matched unit &rarr; case pairs</h4>
          <table>
            <thead>
              <tr>
                <th>Case GTIN</th>
                <th>Case Row</th>
                <th>Unit GTIN</th>
                <th>Unit Row</th>
                <th>Indicator</th>
              </tr>
            </thead>
            <tbody>
              {hierarchy.matched_pairs.map((p, i) => (
                <tr key={i}>
                  <td style={{ fontFamily: 'monospace' }}>{p.case_gtin}</td>
                  <td>{p.case_row}</td>
                  <td style={{ fontFamily: 'monospace' }}>{p.unit_gtin}</td>
                  <td>{p.unit_row}</td>
                  <td>{p.indicator}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {hierarchy.orphan_cases.length > 0 && (
        <>
          <h4>Case GTINs without matching unit GTINs</h4>
          {hierarchy.orphan_cases.map((r) => (
            <p key={r.row_number} className={styles.issueWarning}>
              Row {r.row_number}: {r.cleaned} — no matching unit GTIN found
            </p>
          ))}
        </>
      )}

      {hierarchy.units_without_cases.length > 0 && (
        <>
          <h4>Unit GTINs without case-level GTINs</h4>
          <p className="text-muted">
            These items don't have a corresponding GTIN-14 for case/shipping
            identification.
          </p>
          {hierarchy.units_without_cases.map((r) => (
            <p key={r.row_number}>
              Row {r.row_number}: <strong>{r.cleaned}</strong> ({r.gtin_type})
            </p>
          ))}
        </>
      )}

      {!hierarchy.matched_pairs.length && !hierarchy.orphan_cases.length && (
        <div className={styles.success}>
          No GTIN-14 case-level codes found in your data. If you ship to Walmart
          or Costco, you'll likely need case GTINs.
        </div>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Executive Summary
// ---------------------------------------------------------------------------

export function ExecutiveSummary({ text }: { text: string }) {
  return (
    <section id="summary" className={styles.section}>
      <h3>Executive Summary</h3>
      <p>Copy this summary and send it to your team. No jargon.</p>
      <div className={styles.summaryBox}>{text}</div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// Prioritized Fix Plan
// ---------------------------------------------------------------------------

export function PrioritizedFixPlan({ items }: { items: FixRoadmapItem[] }) {
  return (
    <section id="roadmap" className={styles.section}>
      <h3>Prioritized Fix Plan</h3>
      <p>
        Issues ranked by impact x effort. Start at the top — these are your
        fastest wins with the biggest payoff.
      </p>
      {items.length ? (
        items.map((item, idx) => (
          <details key={item.code} className={styles.expandable}>
            <summary>
              Priority {idx + 1}: {item.action.slice(0, 80)}
              {item.action.length > 80 ? '...' : ''} ({item.count} item
              {item.count !== 1 ? 's' : ''})
            </summary>
            <div className={styles.expandableContent}>
              <div className={styles.roadmapMeta}>
                <div>
                  <strong>Effort</strong>
                  <span style={{ color: effortColor(item.effort) }}>
                    {item.effort}
                  </span>
                  <br />
                  <span className="text-xs">{item.effort_detail}</span>
                </div>
                <div>
                  <strong>Impact</strong>
                  <span style={{ color: impactColor(item.impact) }}>
                    {item.impact}
                  </span>
                  <br />
                  <span className="text-xs">{item.impact_detail}</span>
                </div>
                <div>
                  <strong>Time estimate</strong>
                  <span>{item.time_estimate}</span>
                </div>
              </div>
              <p>
                <strong>Full recommendation:</strong> {item.action}
              </p>
            </div>
          </details>
        ))
      ) : (
        <div className={styles.success}>No issues to fix — your data is clean.</div>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Retailer Readiness
// ---------------------------------------------------------------------------

export function RetailerReadiness({
  checklists,
  selectedRetailer,
}: {
  checklists: Record<string, RetailerChecklist>
  selectedRetailer: string
}) {
  const entries =
    selectedRetailer !== 'All Retailers'
      ? [[selectedRetailer, checklists[selectedRetailer]] as const]
      : Object.entries(checklists)

  return (
    <section id="retailer" className={styles.section}>
      <h3>Retailer Submission Readiness</h3>
      <p>Each retailer has specific GTIN requirements. Here's how your data stacks up.</p>
      {entries.map(([name, checklist]) => {
        if (!checklist) return null
        const statusText = checklist.ready
          ? 'READY'
          : `${checklist.passed}/${checklist.total} checks passed`
        return (
          <div
            key={name}
            className={`${styles.retailerCard} ${checklist.ready ? styles.retailerReady : styles.retailerNotReady}`}
          >
            <strong>{name}</strong> &mdash;{' '}
            {checklist.ready ? '✓ ' : '✗ '}
            {statusText}
            <br />
            <span className="text-muted">{checklist.profile.description}</span>
            <div style={{ marginTop: '0.5rem' }}>
              {checklist.checks.map((c, i) => (
                <div key={i} className={styles.checkItem}>
                  {c.passed ? '✓' : '✗'} {c.check} — <em>{c.detail}</em>
                </div>
              ))}
            </div>
            {checklist.profile.notes && (
              <p className="text-xs" style={{ marginTop: '0.5rem' }}>
                {checklist.profile.notes}
              </p>
            )}
          </div>
        )
      })}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Cost of Inaction
// ---------------------------------------------------------------------------

export function CostOfInaction({ cost }: { cost: CostEstimate | null }) {
  if (!cost) {
    return (
      <section id="cost" className={styles.section}>
        <h3>Estimated Cost of Inaction</h3>
        <div className={styles.success}>No cost estimates — no issues detected.</div>
      </section>
    )
  }
  return <CostOfInactionBody cost={cost} />
}

function CostOfInactionBody({ cost }: { cost: CostEstimate }) {
  const [a, setA] = useState<CostAssumptions>(cost.assumptions)
  const d = cost.drivers

  // Recompute client-side from driver counts × current assumptions so the
  // totals track edits. Mirrors estimate_cost_of_inaction in gtin_core.py.
  const chargebackLow = Math.round(d.critical_count * a.chargeback_per_item_low)
  const chargebackHigh = Math.round(d.critical_count * a.chargeback_per_item_high)
  const delayedSkus = Math.round(d.critical_count * a.delayed_sku_fraction)
  const delayLow = Math.round(delayedSkus * a.delayed_launch_per_sku_low)
  const delayHigh = Math.round(delayedSkus * a.delayed_launch_per_sku_high)
  const reworkHours = Math.round(
    d.critical_count * a.rework_hours_per_critical +
      d.warning_count * a.rework_hours_per_warning,
  )
  const reworkCost = Math.round(reworkHours * a.rework_rate_per_hour)
  const annualLow = chargebackLow + delayLow + reworkCost
  const annualHigh = chargebackHigh + delayHigh + reworkCost

  const set = (key: keyof CostAssumptions, value: string) => {
    const v = parseFloat(value)
    setA((prev) => ({ ...prev, [key]: Number.isFinite(v) ? v : 0 }))
  }
  const usd = (n: number) => `$${n.toLocaleString()}`

  const fields: { key: keyof CostAssumptions; label: string }[] = [
    { key: 'chargeback_per_item_low', label: 'Chargeback per invalid item — low ($)' },
    { key: 'chargeback_per_item_high', label: 'Chargeback per invalid item — high ($)' },
    { key: 'delayed_launch_per_sku_low', label: 'Delayed launch per SKU — low ($)' },
    { key: 'delayed_launch_per_sku_high', label: 'Delayed launch per SKU — high ($)' },
    { key: 'rework_rate_per_hour', label: 'Manual rework ($/hour)' },
    { key: 'growth_multiplier_low', label: 'Growth multiplier — low (×)' },
    { key: 'growth_multiplier_high', label: 'Growth multiplier — high (×)' },
  ]

  return (
    <section id="cost" className={styles.section}>
      <h3>Estimated Cost of Inaction</h3>
      <p>
        These figures are your assumptions run through simple arithmetic, not
        sourced facts. Edit any assumption to match your own retailer terms and
        the totals recalculate as you type.
      </p>
      <div className={styles.costGrid}>
        <div className={styles.costCard}>
          <div className={styles.costNumber}>
            {usd(annualLow)} – {usd(annualHigh)}
          </div>
          <div>Estimated annual cost of unresolved GTIN issues</div>
        </div>
        <div className={styles.costCard}>
          <div className={styles.costNumber}>{reworkHours} hours/year</div>
          <div>Manual rework from GTIN problems</div>
        </div>
      </div>

      <details className={styles.expandable}>
        <summary>
          Assumptions (editable) — {d.critical_count} critical and{' '}
          {d.warning_count} warning item(s) drive these numbers
        </summary>
        <div className={styles.expandableContent}>
          <div className={styles.assumptionGrid}>
            {fields.map((f) => (
              <label key={f.key}>
                {f.label}
                <input
                  type="number"
                  min={0}
                  value={a[f.key]}
                  onChange={(e) => set(f.key, e.target.value)}
                />
              </label>
            ))}
          </div>
          <button
            type="button"
            className="btn"
            style={{ marginTop: '0.75rem' }}
            onClick={() => setA(cost.assumptions)}
          >
            Reset to defaults
          </button>
        </div>
      </details>

      <h4>Breakdown</h4>
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th>Low Estimate</th>
            <th>High Estimate</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Chargebacks from invalid GTINs ({d.critical_count} items)</td>
            <td>{usd(chargebackLow)}</td>
            <td>{usd(chargebackHigh)}</td>
          </tr>
          <tr>
            <td>Delayed launches ({delayedSkus} SKUs)</td>
            <td>{usd(delayLow)}</td>
            <td>{usd(delayHigh)}</td>
          </tr>
          <tr>
            <td>Manual rework ({reworkHours} hrs)</td>
            <td>{usd(reworkCost)}</td>
            <td>{usd(reworkCost)}</td>
          </tr>
        </tbody>
      </table>
      <p style={{ marginTop: '0.75rem', color: '#a05a1a', fontWeight: 500 }}>
        Assumption: at 2× your current SKU count ({d.total_gtins * 2} SKUs) with
        additional retailers, these costs are assumed to scale{' '}
        {a.growth_multiplier_low}–{a.growth_multiplier_high}×. Adjust the
        multiplier above to your own retailer mix.
      </p>
    </section>
  )
}

// ---------------------------------------------------------------------------
// Case GTIN Generator
// ---------------------------------------------------------------------------

export function CaseGTINGenerator({
  suggestions,
}: {
  suggestions: GTIN14Suggestion[]
}) {
  return (
    <section id="gtin14" className={styles.section}>
      <h3>Case GTIN-14 Generator</h3>
      <p>
        Unit-level GTINs that don't have a corresponding case-level GTIN-14.
        Below are the GTIN-14s you'd need to create for each packaging level.
      </p>
      {suggestions.length ? (
        <>
          <p>
            <strong>{suggestions.length} unit GTIN(s)</strong> need case-level
            GTIN-14s.
          </p>
          {suggestions.map((s) => (
            <details key={s.row} className={styles.expandable}>
              <summary>
                Row {s.row}: {s.unit_gtin} ({s.unit_type})
              </summary>
              <div className={styles.expandableContent}>
                <table>
                  <thead>
                    <tr>
                      <th>Indicator</th>
                      <th>GTIN-14</th>
                      <th>Packaging Level</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(s.indicators).map(([ind, info]) => (
                      <tr key={ind}>
                        <td>{ind}</td>
                        <td style={{ fontFamily: 'monospace' }}>{info.gtin14}</td>
                        <td>{info.label}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="text-xs" style={{ marginTop: '0.5rem' }}>
                  Most commonly, indicator 1 = case. Copy the GTIN-14 you need
                  and add it to your product master.
                </p>
              </div>
            </details>
          ))}
        </>
      ) : (
        <div className={styles.success}>
          All unit GTINs have matching case-level GTIN-14s, or no valid unit
          GTINs were found.
        </div>
      )}
    </section>
  )
}
